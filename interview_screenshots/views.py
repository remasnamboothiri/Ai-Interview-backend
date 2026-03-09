from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import InterviewScreenshot
from .serializers import InterviewScreenshotSerializer, InterviewScreenshotCreateSerializer
from interviews.models import Interview

import os
import json
import time
import logging
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)


class InterviewScreenshotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing interview screenshots.
    Detection is done client-side (face-api.js + MediaPipe).
    Frontend sends metadata with each screenshot upload.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = InterviewScreenshot.objects.all()

        interview_id = self.request.query_params.get('interview', None)
        if interview_id:
            queryset = queryset.filter(interview_id=interview_id)

        session_id = self.request.query_params.get('session', None)
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        issue_type = self.request.query_params.get('issue_type', None)
        if issue_type:
            queryset = queryset.filter(issue_type=issue_type)

        flagged = self.request.query_params.get('flagged', None)
        if flagged == 'true':
            queryset = queryset.filter(multiple_people_detected=True)

        return queryset.select_related('interview', 'session')

    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewScreenshotCreateSerializer
        return InterviewScreenshotSerializer

    def get_permissions(self):
        """Allow unauthenticated access for upload action only"""
        if self.action == 'upload':
            return []
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data.get('created_ip'):
            serializer.validated_data['created_ip'] = self._get_client_ip(request)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_interview(self, request):
        interview_id = request.query_params.get('interview_id')
        if not interview_id:
            return Response(
                {'error': 'interview_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        screenshots = self.get_queryset().filter(interview_id=interview_id)
        serializer = self.get_serializer(screenshots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def flagged(self, request):
        screenshots = self.get_queryset().filter(multiple_people_detected=True)
        serializer = self.get_serializer(screenshots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload screenshot with client-side detection metadata.

        Expected data:
        - webcam_image: Image file from webcam
        - interview: Interview ID
        - screenshot_number: Sequential number
        - face_count: Number of faces detected (from face-api.js)
        - multiple_people_detected: 'true' if 2+ faces
        - issue_type: 'none' | 'multiple_faces' | 'phone_detected' | 'looking_away'
        - is_flagged: 'true' if any integrity issue detected
        - metadata: JSON string with full detection details
        """
        try:
            webcam_file = request.FILES.get('webcam_image')
            if not webcam_file:
                return Response(
                    {'error': 'No webcam_image file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            interview_id = request.data.get('interview')
            if not interview_id:
                return Response(
                    {'error': 'interview ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            screenshot_number = request.data.get('screenshot_number', 1)
            interview = get_object_or_404(Interview, id=interview_id)

            # Save file to disk and get absolute URL
            file_url = self._save_screenshot_file(webcam_file, interview_id)

            # ── Read client-side detection metadata ───────────
            face_count = int(request.data.get('face_count', 0))
            multiple_people = (
                request.data.get('multiple_people_detected', '').lower() == 'true'
                or face_count > 1
            )
            issue_type = request.data.get('issue_type', 'none') or 'none'
            is_flagged = request.data.get('is_flagged', '').lower() == 'true'
            flag_reason = request.data.get('flag_reason', '')

            # Parse metadata JSON from frontend
            raw_metadata = request.data.get('metadata', '{}')
            try:
                client_metadata = json.loads(raw_metadata) if isinstance(raw_metadata, str) else raw_metadata
            except (json.JSONDecodeError, TypeError):
                client_metadata = {}

            # Also check metadata for detection flags (belt and suspenders)
            if not multiple_people and client_metadata.get('multiple_faces'):
                multiple_people = True
            if issue_type == 'none' and client_metadata.get('phone_detected'):
                issue_type = 'phone_detected'
            if issue_type == 'none' and client_metadata.get('looking_away'):
                issue_type = 'looking_away'

            # Calculate confidence based on detection state
            confidence = 0.0
            if multiple_people or issue_type != 'none':
                confidence = 0.85
            elif face_count == 1:
                confidence = 0.95

            # Build full metadata
            metadata = {
                **client_metadata,
                'file_size': webcam_file.size,
                'content_type': webcam_file.content_type,
                'is_flagged': is_flagged,
                'flag_reason': flag_reason,
            }

            screenshot = InterviewScreenshot.objects.create(
                interview=interview,
                screenshot_url=file_url,
                screenshot_number=screenshot_number,
                face_count=face_count,
                multiple_people_detected=multiple_people,
                issue_type=issue_type,
                confidence_score=confidence,
                created_ip=self._get_client_ip(request),
                metadata=metadata,
            )

            if is_flagged or issue_type != 'none':
                logger.info(
                    f":warning: Flagged screenshot #{screenshot_number} for interview {interview_id}: "
                    f"issue={issue_type}, faces={face_count}, reason={flag_reason}"
                )

            serializer = self.get_serializer(screenshot)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Screenshot upload failed (non-critical): {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Screenshot upload failed but interview continues'
            }, status=status.HTTP_200_OK)

    
    
    def _save_screenshot_file(self, file, interview_id):
        # Save file to disk (same as before)
        screenshots_dir = os.path.join(settings.MEDIA_ROOT, 'screenshots', str(interview_id))
        os.makedirs(screenshots_dir, exist_ok=True)
    
        timestamp = int(time.time() * 1000)
        filename = f"screenshot_{timestamp}_{file.name}"
        filepath = os.path.join(screenshots_dir, filename)
    
        # Write file to disk (same as before)
        with open(filepath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
    
        # ✅ FIX: Build ABSOLUTE URL using environment variable
        backend_url = config('BACKEND_URL', default='http://localhost:8000')
        #            ↑ Gets backend URL from .env file
    
        # Remove trailing slash if present
        backend_url = backend_url.rstrip('/')
    
        # Return FULL URL with domain
        return f"{backend_url}/media/screenshots/{interview_id}/{filename}"
        #       ↑ Complete URL with domain!


    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip



