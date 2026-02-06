from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Recruiter
from .serializers import RecruiterSerializer
from activity_logs.models import ActivityLog


class RecruiterViewSet(viewsets.ModelViewSet):
    queryset = Recruiter.objects.all()
    serializer_class = RecruiterSerializer
    
    def list(self, request):
        """Get all recruiters"""
        recruiters = self.get_queryset()
        serializer = self.get_serializer(recruiters, many=True)
        return Response({
            'success': True,
            'count': recruiters.count(),
            'data': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """Get single recruiter by ID"""
        try:
            recruiter = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(recruiter)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Recruiter.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Recruiter not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='company/(?P<company_id>[^/.]+)')
    def by_company(self, request, company_id=None):
        """Get all recruiters for a specific company"""
        recruiters = self.get_queryset().filter(company_id=company_id)
        serializer = self.get_serializer(recruiters, many=True)
        return Response({
            'success': True,
            'count': recruiters.count(),
            'data': serializer.data
        })
    
    def create(self, request):
        """Create new recruiter (link user to company)"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            recruiter = serializer.save()
            # ✅ ADD THIS: Create activity log
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='recruiter_added',
                resource_type='Recruiter',
                resource_id=recruiter.id,
                details={
                    'user_id': recruiter.user_id,
                    'company_id': recruiter.company_id
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            
            return Response({
                'success': True,
                'message': 'Recruiter created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update existing recruiter"""
        try:
            recruiter = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(recruiter, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Recruiter updated successfully',
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Recruiter.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Recruiter not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """Delete recruiter"""
        try:
            recruiter = self.get_queryset().get(pk=pk)
            recruiter_id = recruiter.id
            user_id = recruiter.user_id
            company_id = recruiter.company_id
            recruiter.delete()
            
            # ✅ ADD THIS: Create activity log
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='recruiter_removed',
                resource_type='Recruiter',
                resource_id=recruiter_id,
                details={
                    'user_id': user_id,
                    'company_id': company_id
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({
                'success': True,
                'message': 'Recruiter deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Recruiter.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Recruiter not found'
            }, status=status.HTTP_404_NOT_FOUND)
