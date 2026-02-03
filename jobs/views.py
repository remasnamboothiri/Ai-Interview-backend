from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Job
from .serializers import JobSerializer

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
            serializer.save()
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
                serializer.save()
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
            job.delete()
            return Response({
                'success': True,
                'message': 'Job deleted successfully'
            })
        except Job.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Job not found'
            }, status=status.HTTP_404_NOT_FOUND)
