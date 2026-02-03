from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import JobApplication
from .serializers import (
    JobApplicationSerializer, 
    JobApplicationDetailSerializer, 
    JobApplicationCreateSerializer
)

class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    permission_classes = []
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['candidate__user__full_name', 'candidate__user__email', 'job__title']
    ordering_fields = ['created_at', 'applied_at', 'application_status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return JobApplicationCreateSerializer
        elif self.action in ['retrieve', 'list']:
            return JobApplicationDetailSerializer if self.action == 'retrieve' else JobApplicationSerializer
        return JobApplicationSerializer
    
    def get_queryset(self):
        queryset = JobApplication.objects.select_related(
            'job', 'candidate', 'candidate__user', 'job__company', 'created_by'
        )
        return queryset

    # def get_queryset(self):
    #     queryset = JobApplication.objects.select_related(
    #         'job', 'candidate', 'candidate__user', 'job__company', 'created_by'
    #     )
    
    #     user = self.request.user
    
    #     # Admin can see everything
    #     if user.user_type in ['admin', 'super_admin']:
    #         return queryset
    
    #     # Recruiter can see their company's applications
    #     if hasattr(user, 'recruiter'):
    #         return queryset.filter(job__company=user.recruiter.company)
    
    #     # Candidate can see only their applications
    #     if hasattr(user, 'candidate'):
    #         return queryset.filter(candidate=user.candidate)
    
    #     # Others see nothing
    #     return queryset.none()
    

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_job(self, request):
        """Get applications for a specific job"""
        job_id = request.query_params.get('job_id')
        if not job_id:
            return Response({'error': 'job_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        applications = self.get_queryset().filter(job_id=job_id)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_candidate(self, request):
        """Get applications for a specific candidate"""
        candidate_id = request.query_params.get('candidate_id')
        if not candidate_id:
            return Response({'error': 'candidate_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        applications = self.get_queryset().filter(candidate_id=candidate_id)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update application status"""
        application = self.get_object()
        new_status = request.data.get('application_status')
        
        if new_status not in dict(JobApplication.APPLICATION_STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.application_status = new_status
        application.updated_by = request.user
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)