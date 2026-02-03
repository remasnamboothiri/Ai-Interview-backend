from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import InterviewData
from .serializers import (
    InterviewDataSerializer,
    InterviewDataCreateSerializer,
    InterviewDataUpdateSerializer
)

class InterviewDataViewSet(viewsets.ModelViewSet):
    queryset = InterviewData.objects.all()
    permission_classes = []
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewDataCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InterviewDataUpdateSerializer
        return InterviewDataSerializer
    
    def get_queryset(self):
        queryset = InterviewData.objects.select_related('interview')
        
        # Filter by interview if provided
        interview_id = self.request.query_params.get('interview')
        if interview_id:
            queryset = queryset.filter(interview_id=interview_id)
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Mark session as started"""
        session = self.get_object()
        session.started_at = timezone.now()
        session.status = 'active'
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """Mark session as completed"""
        session = self.get_object()
        session.ended_at = timezone.now()
        session.status = 'completed'
        
        # Calculate duration
        if session.started_at:
            duration = (session.ended_at - session.started_at).total_seconds() / 60
            session.actual_duration_minutes = int(duration)
        
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_activity(self, request, pk=None):
        """Update last activity timestamp"""
        session = self.get_object()
        session.last_activity_at = timezone.now()
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_interview(self, request):
        """Get all sessions for a specific interview"""
        interview_id = request.query_params.get('interview_id')
        if not interview_id:
            return Response(
                {'error': 'interview_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sessions = self.get_queryset().filter(interview_id=interview_id)
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
