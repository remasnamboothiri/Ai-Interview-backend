from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import InterviewResult
from .serializers import InterviewResultSerializer, InterviewResultCreateSerializer, InterviewResultUpdateSerializer

class InterviewResultViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = InterviewResult.objects.select_related(
            'interview', 'primary_session', 'result_reviewed_by', 'created_by', 'updated_by'
        ).all()
        
        interview_id = self.request.query_params.get('interview', None)
        recommendation = self.request.query_params.get('recommendation', None)
        
        if interview_id:
            queryset = queryset.filter(interview_id=interview_id)
        if recommendation:
            queryset = queryset.filter(recommendation=recommendation)
            
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InterviewResultCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InterviewResultUpdateSerializer
        return InterviewResultSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_reviewed(self, request, pk=None):
        result = self.get_object()
        result.result_reviewed_at = timezone.now()
        result.result_reviewed_by = request.user
        result.save()
        serializer = self.get_serializer(result)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_interview(self, request):
        interview_id = request.query_params.get('interview_id')
        if not interview_id:
            return Response({'error': 'interview_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = InterviewResult.objects.get(interview_id=interview_id)
            serializer = self.get_serializer(result)
            return Response(serializer.data)
        except InterviewResult.DoesNotExist:
            return Response({'error': 'Result not found'}, status=status.HTTP_404_NOT_FOUND)
