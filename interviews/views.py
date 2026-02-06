from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Interview

from activity_logs.models import ActivityLog
from notifications.models import Notification

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
        interview = serializer.save()
        
        # ✅ Create activity log
        try:
            ActivityLog.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                action='interview_scheduled',
                resource_type='Interview',
                resource_id=interview.id,
                details={
                    'candidate_name': interview.candidate.user.full_name if interview.candidate and interview.candidate.user else 'Unknown',
                    'job_title': interview.job.title if interview.job else 'Unknown',
                    'scheduled_at': str(interview.scheduled_at)
                },
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error creating activity log: {e}")
        
        # ✅ Create notification for candidate
        try:
            if interview.candidate and interview.candidate.user:
                Notification.objects.create(
                    user=interview.candidate.user,
                    notification_type='interview_scheduled',
                    title='Interview Scheduled',
                    message=f'Your interview for {interview.job.title} has been scheduled for {interview.scheduled_at.strftime("%B %d, %Y at %I:%M %p")}',
                    related_resource_type='Interview',
                    related_resource_id=interview.id,
                    action_url=f'/interviews/{interview.id}',
                    is_read=False
                )
        except Exception as e:
            print(f"Error creating candidate notification: {e}")
        
        # ✅ Create notification for recruiter
        try:
            if interview.recruiter:
                Notification.objects.create(
                    user=interview.recruiter,
                    notification_type='interview_scheduled',
                    title='Interview Scheduled',
                    message=f'Interview scheduled with {interview.candidate.user.full_name if interview.candidate and interview.candidate.user else "candidate"} for {interview.job.title}',
                    related_resource_type='Interview',
                    related_resource_id=interview.id,
                    action_url=f'/interviews/{interview.id}',
                    is_read=False
                )
        except Exception as e:
            print(f"Error creating recruiter notification: {e}")
    
    def perform_update(self, serializer):
        interview = serializer.save()
        
        # ✅ Create activity log for interview update
        try:
            ActivityLog.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                action='interview_updated',
                resource_type='Interview',
                resource_id=interview.id,
                details={
                    'candidate_name': interview.candidate.user.full_name if interview.candidate and interview.candidate.user else 'Unknown',
                    'job_title': interview.job.title if interview.job else 'Unknown',
                    'status': interview.status
                },
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error creating activity log: {e}")
        
        # ✅ If interview is completed, create activity log
        if interview.status == 'completed':
            try:
                ActivityLog.objects.create(
                    user=self.request.user if self.request.user.is_authenticated else None,
                    action='interview_completed',
                    resource_type='Interview',
                    resource_id=interview.id,
                    details={
                        'candidate_name': interview.candidate.user.full_name if interview.candidate and interview.candidate.user else 'Unknown',
                        'job_title': interview.job.title if interview.job else 'Unknown'
                    },
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )
                
                # Notify recruiter that interview is completed
                if interview.recruiter:
                    Notification.objects.create(
                        user=interview.recruiter,
                        notification_type='interview_completed',
                        title='Interview Completed',
                        message=f'Interview with {interview.candidate.user.full_name if interview.candidate and interview.candidate.user else "candidate"} for {interview.job.title} has been completed',
                        related_resource_type='Interview',
                        related_resource_id=interview.id,
                        action_url=f'/interviews/{interview.id}',
                        is_read=False
                    )
            except Exception as e:
                print(f"Error creating completion log/notification: {e}")
    
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
        interview.cancelled_by = request.user if request.user.is_authenticated else None
        interview.cancellation_reason = request.data.get('cancellation_reason', '')
        interview.save()
        
        # ✅ Create activity log
        try:
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='interview_cancelled',
                resource_type='Interview',
                resource_id=interview.id,
                details={
                    'candidate_name': interview.candidate.user.full_name if interview.candidate and interview.candidate.user else 'Unknown',
                    'job_title': interview.job.title if interview.job else 'Unknown',
                    'reason': interview.cancellation_reason
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error creating activity log: {e}")
        
        # ✅ Notify candidate
        try:
            if interview.candidate and interview.candidate.user:
                Notification.objects.create(
                    user=interview.candidate.user,
                    notification_type='interview_cancelled',
                    title='Interview Cancelled',
                    message=f'Your interview for {interview.job.title} has been cancelled. Reason: {interview.cancellation_reason}',
                    related_resource_type='Interview',
                    related_resource_id=interview.id,
                    is_read=False
                )
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        # ✅ Notify recruiter
        try:
            if interview.recruiter:
                Notification.objects.create(
                    user=interview.recruiter,
                    notification_type='interview_cancelled',
                    title='Interview Cancelled',
                    message=f'Interview with {interview.candidate.user.full_name if interview.candidate and interview.candidate.user else "candidate"} for {interview.job.title} has been cancelled',
                    related_resource_type='Interview',
                    related_resource_id=interview.id,
                    is_read=False
                )
        except Exception as e:
            print(f"Error creating recruiter notification: {e}")
        
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
        
        old_time = interview.scheduled_at
        interview.scheduled_at = new_time
        interview.updated_by = request.user if request.user.is_authenticated else None
        interview.save()
        
        # ✅ Create activity log
        try:
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='interview_rescheduled',
                resource_type='Interview',
                resource_id=interview.id,
                details={
                    'candidate_name': interview.candidate.user.full_name if interview.candidate and interview.candidate.user else 'Unknown',
                    'job_title': interview.job.title if interview.job else 'Unknown',
                    'old_time': str(old_time),
                    'new_time': str(new_time)
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error creating activity log: {e}")
        
        # ✅ Notify candidate
        try:
            if interview.candidate and interview.candidate.user:
                Notification.objects.create(
                    user=interview.candidate.user,
                    notification_type='interview_rescheduled',
                    title='Interview Rescheduled',
                    message=f'Your interview for {interview.job.title} has been rescheduled to {interview.scheduled_at.strftime("%B %d, %Y at %I:%M %p")}',
                    related_resource_type='Interview',
                    related_resource_id=interview.id,
                    action_url=f'/interviews/{interview.id}',
                    is_read=False
                )
        except Exception as e:
            print(f"Error creating candidate notification: {e}")
        
        # ✅ Notify recruiter
        try:
            if interview.recruiter:
                Notification.objects.create(
                    user=interview.recruiter,
                    notification_type='interview_rescheduled',
                    title='Interview Rescheduled',
                    message=f'Interview with {interview.candidate.user.full_name if interview.candidate and interview.candidate.user else "candidate"} for {interview.job.title} has been rescheduled',
                    related_resource_type='Interview',
                    related_resource_id=interview.id,
                    action_url=f'/interviews/{interview.id}',
                    is_read=False
                )
        except Exception as e:
            print(f"Error creating recruiter notification: {e}")
        
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
