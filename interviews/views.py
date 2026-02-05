from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Interview
from .serializers import (
    InterviewSerializer,
    InterviewDetailSerializer,
    InterviewCreateSerializer,
    InterviewUpdateSerializer
)

class InterviewViewSet(viewsets.ModelViewSet):
    queryset = Interview.objects.all()
    permission_classes = []  # No authentication for now
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['candidate__user__full_name', 'candidate__user__email', 'job__title']
    ordering_fields = ['scheduled_at', 'created_at', 'status']
    ordering = ['-scheduled_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InterviewUpdateSerializer
        elif self.action == 'retrieve':
            return InterviewDetailSerializer
        return InterviewSerializer
    
    def get_queryset(self):
        queryset = Interview.objects.select_related(
            'job', 'candidate', 'candidate__user', 'agent', 'recruiter',
            'job__company', 'created_by'
        )
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by job if provided
        job_id = self.request.query_params.get('job')
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        
        # Filter by candidate if provided
        candidate_id = self.request.query_params.get('candidate')
        if candidate_id:
            queryset = queryset.filter(candidate_id=candidate_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an interview"""
        interview = self.get_object()
        
        if interview.status == 'cancelled':
            return Response(
                {'error': 'Interview is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.status = 'cancelled'
        interview.cancelled_at = timezone.now()
        interview.cancelled_by = request.user
        interview.cancellation_reason = request.data.get('cancellation_reason', '')
        interview.save()
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule an interview"""
        interview = self.get_object()
        
        new_time = request.data.get('scheduled_at')
        if not new_time:
            return Response(
                {'error': 'scheduled_at is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.scheduled_at = new_time
        interview.updated_by = request.user
        interview.save()
        
        serializer = self.get_serializer(interview)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming interviews"""
        now = timezone.now()
        interviews = self.get_queryset().filter(
            scheduled_at__gte=now,
            status='scheduled'
        )
        serializer = self.get_serializer(interviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_job(self, request):
        """Get interviews for a specific job"""
        job_id = request.query_params.get('job_id')
        if not job_id:
            return Response(
                {'error': 'job_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interviews = self.get_queryset().filter(job_id=job_id)
        serializer = self.get_serializer(interviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_candidate(self, request):
        """Get interviews for a specific candidate"""
        candidate_id = request.query_params.get('candidate_id')
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interviews = self.get_queryset().filter(candidate_id=candidate_id)
        serializer = self.get_serializer(interviews, many=True)
        return Response(serializer.data)