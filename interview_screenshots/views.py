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
