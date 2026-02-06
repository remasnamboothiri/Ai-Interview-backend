from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Job
from .serializers import JobSerializer
from activity_logs.models import ActivityLog
from notifications.models import Notification


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    
    def list(self, request):
        """GET /api/jobs/ - List all jobs"""
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """GET /api/jobs/{id}/ - Get single job"""
        try:
            job = Job.objects.get(pk=pk)
            serializer = JobSerializer(job)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Job.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Job not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        """POST /api/jobs/ - Create new job"""
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()
            
            
            # ✅ Create activity log
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='job_created',
                resource_type='Job',
                resource_id=job.id,
                details={'job_title': job.title, 'company_id': job.company_id},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # ✅ Create notification for recruiter
            if job.recruiter_id:
                Notification.objects.create(
                    user_id=job.recruiter_id,
                    notification_type='job_created',
                    title='Job Created Successfully',
                    message=f'Your job posting "{job.title}" has been created',
                    related_resource_type='Job',
                    related_resource_id=job.id,
                    action_url=f'/jobs/{job.id}',
                    is_read=False
                )
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """PUT /api/jobs/{id}/ - Update job"""
        try:
            job = Job.objects.get(pk=pk)
            serializer = JobSerializer(job, data=request.data, partial=True)
            if serializer.is_valid():
                job = serializer.save()
                
                
                # ✅ Create activity log
                ActivityLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='job_updated',
                    resource_type='Job',
                    resource_id=job.id,
                    details={'job_title': job.title, 'old_status': old_status, 'new_status': job.status},
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            
                # ✅ If job was published, create notification
                if old_status != 'active' and job.status == 'active':
                    ActivityLog.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        action='job_published',
                        resource_type='Job',
                        resource_id=job.id,
                        details={'job_title': job.title},
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                return Response({
                    'success': True,
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Job.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Job not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """DELETE /api/jobs/{id}/ - Delete job"""
        try:
            job = Job.objects.get(pk=pk)
            job_title = job.title
            job_id = job.id
            job.delete()
            
            # ✅ Create activity log
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='job_deleted',
                resource_type='Job',
                resource_id=job_id,
                details={'job_title': job_title},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({
                'success': True,
                'message': 'Job deleted successfully'
            })
        except Job.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Job not found'
            }, status=status.HTTP_404_NOT_FOUND)
