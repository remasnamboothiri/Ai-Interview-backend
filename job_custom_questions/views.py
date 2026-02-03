from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import JobCustomQuestion
from .serializers import JobCustomQuestionSerializer

class JobCustomQuestionViewSet(viewsets.ModelViewSet):
    queryset = JobCustomQuestion.objects.all()
    serializer_class = JobCustomQuestionSerializer
    
    def list(self, request):
        """GET /api/job-custom-questions/ - List all custom questions"""
        # Filter by job_id if provided
        job_id = request.query_params.get('job_id', None)
        if job_id:
            questions = JobCustomQuestion.objects.filter(job_id=job_id)
        else:
            questions = JobCustomQuestion.objects.all()
        
        serializer = JobCustomQuestionSerializer(questions, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """GET /api/job-custom-questions/{id}/ - Get single question"""
        try:
            question = JobCustomQuestion.objects.get(pk=pk)
            serializer = JobCustomQuestionSerializer(question)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except JobCustomQuestion.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Question not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        """POST /api/job-custom-questions/ - Create new question"""
        serializer = JobCustomQuestionSerializer(data=request.data)
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
        """PUT /api/job-custom-questions/{id}/ - Update question"""
        try:
            question = JobCustomQuestion.objects.get(pk=pk)
            serializer = JobCustomQuestionSerializer(question, data=request.data, partial=True)
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
        except JobCustomQuestion.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Question not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """DELETE /api/job-custom-questions/{id}/ - Delete question"""
        try:
            question = JobCustomQuestion.objects.get(pk=pk)
            question.delete()
            return Response({
                'success': True,
                'message': 'Question deleted successfully'
            })
        except JobCustomQuestion.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Question not found'
            }, status=status.HTTP_404_NOT_FOUND)
