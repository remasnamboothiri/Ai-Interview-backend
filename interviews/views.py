from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Interview
import logging

from activity_logs.models import ActivityLog
from notifications.models import Notification
from interview_data.models import InterviewConversation
from .result_generator import generate_interview_result  #newly added

from .serializers import (
    InterviewSerializer,
    InterviewDetailSerializer,
    InterviewCreateSerializer,
    InterviewUpdateSerializer
)

# Import AI Interview Service
from .ai_interview_service import AIInterviewService
from .email_service import InterviewEmailService

logger = logging.getLogger(__name__)

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
        try:
            # Start with basic queryset
            queryset = Interview.objects.all()
            
            # Try to optimize with select_related, but catch any errors
            try:
                queryset = queryset.select_related(
                    'job', 'candidate', 'candidate__user', 'agent', 'recruiter',
                    'job__company', 'created_by'
                )
            except Exception as e:
                logger.warning(f"Could not use select_related: {e}")
            
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
            
            logger.info(f"Returning queryset with {queryset.count()} interviews")
            return queryset
        except Exception as e:
            logger.error(f"Error in get_queryset: {e}")
            logger.exception("Full traceback:")
            return Interview.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Override create to add detailed error logging"""
        try:
            logger.info(f"Creating interview with data: {request.data}")
            logger.info(f"User: {request.user}")
            logger.info(f"User has pk: {hasattr(request.user, 'pk') and request.user.pk}")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error creating interview: {str(e)}")
            logger.exception("Full traceback:")
            return Response(
                {'error': str(e), 'detail': 'Failed to create interview'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        from threading import Thread
        
        try:
            interview = serializer.save()
            
            # ✅ Create activity log
            try:
                user = self.request.user if self.request.user and self.request.user.pk else None
                ActivityLog.objects.create(
                    user=user,
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
            
            # ✅ Send interview invitation email IN BACKGROUND THREAD
            def send_email_async():
                try:
                    InterviewEmailService.send_interview_invitation(interview.id)
                    logger.info(f"Interview invitation email sent for interview {interview.id}")
                except Exception as e:
                    logger.error(f"Error sending interview invitation email: {e}")
                    print(f"Error sending interview invitation email: {e}")
            
            # Start email sending in background thread to avoid timeout
            Thread(target=send_email_async, daemon=True).start()
            
        except Exception as e:
            print(f"Error in perform_create: {e}")
            import traceback
            traceback.print_exc()
            raise

    
    def perform_update(self, serializer):
        interview = serializer.save()
        
        # ✅ Create activity log for interview update
        try:
            user = self.request.user if self.request.user and self.request.user.pk else None
            ActivityLog.objects.create(
                user=user,
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
                user = self.request.user if self.request.user and self.request.user.pk else None
                ActivityLog.objects.create(
                    user=user,
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
        interview.cancelled_by = request.user if request.user and request.user.pk else None
        interview.cancellation_reason = request.data.get('cancellation_reason', '')
        interview.save()
        
        # ✅ Create activity log
        try:
            user = request.user if request.user and request.user.pk else None
            ActivityLog.objects.create(
                user=user,
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
        interview.updated_by = request.user if request.user and request.user.pk else None
        interview.save()
        
        # ✅ Create activity log
        try:
            user = request.user if request.user and request.user.pk else None
            ActivityLog.objects.create(
                user=user,
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
    def test(self, request):
        """Test endpoint to verify API is working"""
        return Response({
            'status': 'ok',
            'user_has_pk': hasattr(request.user, 'pk') and request.user.pk is not None,
            'user': str(request.user),
            'interview_count': Interview.objects.count()
        })
    
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
    
    # ========================================
    # AI INTERVIEW ENDPOINTS
    # ========================================
    
    @action(detail=True, methods=['post'])
    def start_interview(self, request, pk=None):
        """
        Start AI interview - Initialize conversation and return first question
        POST /api/interviews/{id}/start_interview/
        """
        try:
            interview = self.get_object()
            
            # ✅ BETTER: Allow starting if scheduled OR in_progress (for resume/refresh)
            if interview.status not in ['scheduled', 'in_progress']:
                return Response(
                    {'error': f'Interview cannot be started. Current status: {interview.status}. Only scheduled or in-progress interviews can be started.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update interview status to in_progress
            if interview.status == 'scheduled':
                interview.status = 'in_progress'
                interview.save()
            
            # Initialize AI Interview Service
            ai_service = AIInterviewService(interview.id)
            
            # Start interview and get first question
            result = ai_service.start_interview()
            
            # Save AI's first message to interview_conversations
            InterviewConversation.objects.create(
                interview=interview,
                speaker='ai',
                message=result['message']
            )
            
            logger.info(f"Interview {interview.id} started successfully")
            
            return Response({
                'success': True,
                'interview_id': interview.id,
                'status': interview.status,
                **result
            })
            
        except Interview.DoesNotExist:
            return Response(
                {'error': 'Interview not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error starting interview: {str(e)}")
            return Response(
                {'error': f'Failed to start interview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send candidate's answer and get AI's response
        POST /api/interviews/{id}/send_message/
        Body: {"message": "candidate's answer"}
        """
        try:
            interview = self.get_object()
            
            # Check if interview is in progress
            if interview.status != 'in_progress':
                return Response(
                    {'error': f'Interview is not in progress. Current status: {interview.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get candidate's message
            candidate_message = request.data.get('message')
            if not candidate_message:
                return Response(
                    {'error': 'message field is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save candidate's message
            InterviewConversation.objects.create(
                interview=interview,
                speaker='candidate',
                message=candidate_message
            )
            
            # Get AI response
            ai_service = AIInterviewService(interview.id)
            result = ai_service.send_message(candidate_message)
            
            # Save AI's response
            InterviewConversation.objects.create(
                interview=interview,
                speaker='ai',
                message=result['message']
            )
            
            # If interview is complete, update status
            if result.get('is_complete'):
                interview.status = 'completed'
                interview.save()
                logger.info(f"Interview {interview.id} completed")
            
            return Response({
                'success': True,
                'interview_id': interview.id,
                **result
            })
            
        except Interview.DoesNotExist:
            return Response(
                {'error': 'Interview not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return Response(
                {'error': f'Failed to process message: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # @action(detail=True, methods=['post'])
    # def end_interview(self, request, pk=None):
    #     """
    #     End the interview
    #     POST /api/interviews/{id}/end_interview/
    #     """
    #     try:
    #         interview = self.get_object()
            
    #         # Update interview status
    #         if interview.status == 'in_progress':
    #             interview.status = 'completed'
    #             interview.save()
            
    #         # Get AI service summary
    #         ai_service = AIInterviewService(interview.id)
    #         result = ai_service.end_interview()
            
    #         # Create activity log
    #         try:
    #             user = request.user if request.user and request.user.pk else None
    #             ActivityLog.objects.create(
    #                 user=user,
    #                 action='interview_completed',
    #                 resource_type='Interview',
    #                 resource_id=interview.id,
    #                 details={
    #                     'candidate_name': interview.candidate.user.full_name if interview.candidate and interview.candidate.user else 'Unknown',
    #                     'job_title': interview.job.title if interview.job else 'Unknown',
    #                     'questions_asked': result.get('total_questions_asked', 0)
    #                 },
    #                 ip_address=request.META.get('REMOTE_ADDR')
    #             )
    #         except Exception as e:
    #             logger.error(f"Error creating activity log: {e}")
            
    #         logger.info(f"Interview {interview.id} ended successfully")
            
    #         return Response({
    #             'success': True,
    #             'interview_id': interview.id,
    #             'status': interview.status,
    #             **result
    #         })
            
    #     except Interview.DoesNotExist:
    #         return Response(
    #             {'error': 'Interview not found'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )
    #     except Exception as e:
    #         logger.error(f"Error ending interview: {str(e)}")
    #         return Response(
    #             {'error': f'Failed to end interview: {str(e)}'},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )
    @action(detail=True, methods=['post'])
    def end_interview(self, request, pk=None):
        """End the interview and generate result"""
        try:
            interview = self.get_object()
            
            if interview.status == 'in_progress':
                interview.status = 'completed'
                interview.save()
            
            user = request.user if request.user and request.user.pk else None
            try:
                result = generate_interview_result(interview.id, user)
                result_data = {
                    'overall_score': float(result.overall_score),
                    'recommendation': result.recommendation,
                    'result_id': result.id,
                }
            except Exception as e:
                logger.error(f"Result generation failed: {e}")
                result_data = {'result_generation_error': str(e)}
            
            try:
                user_log = request.user if request.user and request.user.pk else None
                ActivityLog.objects.create(
                    user=user_log,
                    action='interview_completed',
                    resource_type='Interview',
                    resource_id=interview.id,
                    details={
                        'candidate_name': interview.candidate.user.full_name if interview.candidate and interview.candidate.user else 'Unknown',
                        'job_title': interview.job.title if interview.job else 'Unknown',
                    },
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            except Exception as e:
                logger.error(f"Error creating activity log: {e}")
            
            return Response({
                'success': True,
                'interview_id': interview.id,
                'status': interview.status,
                'message': 'Interview completed and result generated.',
                **result_data
            })
            
        except Interview.DoesNotExist:
            return Response({'error': 'Interview not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error ending interview: {str(e)}")
            return Response({'error': f'Failed to end interview: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)