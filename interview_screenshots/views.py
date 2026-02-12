from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import InterviewScreenshot
from .serializers import InterviewScreenshotSerializer, InterviewScreenshotCreateSerializer
from interviews.models import Interview

import os
import time
from django.conf import settings
from .face_analyzer import FaceAnalyzer



class InterviewScreenshotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing interview screenshots
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = InterviewScreenshot.objects.all()
        
        # Filter by interview
        interview_id = self.request.query_params.get('interview', None)
        if interview_id:
            queryset = queryset.filter(interview_id=interview_id)
        
        # Filter by session
        session_id = self.request.query_params.get('session', None)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by issue type
        issue_type = self.request.query_params.get('issue_type', None)
        if issue_type:
            queryset = queryset.filter(issue_type=issue_type)
        
        # Filter flagged screenshots
        flagged = self.request.query_params.get('flagged', None)
        if flagged == 'true':
            queryset = queryset.filter(multiple_people_detected=True)
        
        return queryset.select_related('interview', 'session')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewScreenshotCreateSerializer
        return InterviewScreenshotSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new screenshot"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Auto-capture IP if not provided
        if not serializer.validated_data.get('created_ip'):
            serializer.validated_data['created_ip'] = self.get_client_ip(request)
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def by_interview(self, request):
        """Get all screenshots for a specific interview"""
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
        """Get all flagged screenshots (with issues detected)"""
        screenshots = self.get_queryset().filter(
            multiple_people_detected=True
        )
        serializer = self.get_serializer(screenshots, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload and analyze screenshot
    
        Expected data:
        - webcam_image: Image file from webcam
        - interview: Interview ID
        - screenshot_number: Sequential number
        """
        try:
            # Get uploaded file
            webcam_file = request.FILES.get('webcam_image')
            if not webcam_file:
                return Response(
                    {'error': 'No webcam_image file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            # Get interview ID
            interview_id = request.data.get('interview')
            if not interview_id:
                return Response(
                    {'error': 'interview ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            # Get screenshot number
            screenshot_number = request.data.get('screenshot_number', 1)
        
            # Validate interview exists
            interview = get_object_or_404(Interview, id=interview_id)
        
            # Save file to disk
            file_url = self._save_screenshot_file(webcam_file, interview_id)
        
            # Analyze image with AI
            analyzer = FaceAnalyzer()
            analysis_result = analyzer.analyze_image(webcam_file)
        
            # Create database record
            screenshot = InterviewScreenshot.objects.create(
                interview=interview,
                screenshot_url=file_url,
                screenshot_number=screenshot_number,
                face_count=analysis_result['face_count'],
                multiple_people_detected=analysis_result['multiple_people_detected'],
                issue_type=analysis_result['issue_type'],
                confidence_score=analysis_result['confidence_score'],
                created_ip=self._get_client_ip(request),
                metadata={
                    'analysis_success': analysis_result['success'],
                    'file_size': webcam_file.size,
                    'content_type': webcam_file.content_type
                }
            )
        
            # Return response
            serializer = self.get_serializer(screenshot)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _save_screenshot_file(self, file, interview_id):
        """Save uploaded file to media/screenshots/ folder"""
        # Create screenshots directory if it doesn't exist
        screenshots_dir = os.path.join(settings.MEDIA_ROOT, 'screenshots', str(interview_id))
        os.makedirs(screenshots_dir, exist_ok=True)
    
        # Generate unique filename
        timestamp = int(time.time() * 1000)  # milliseconds
        filename = f"screenshot_{timestamp}_{file.name}"
        filepath = os.path.join(screenshots_dir, filename)
    
        # Save file
        with open(filepath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
    
        # Return URL path (not full system path)
        return f"/media/screenshots/{interview_id}/{filename}"

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    
    
    
    
