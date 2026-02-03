from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import permission_classes as method_permission_classes
from rest_framework.response import Response
from .models import ActivityLog
from .serializers import ActivityLogSerializer
from rest_framework.permissions import AllowAny


class ActivityLogViewSet(viewsets.ModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'head', 'options']
    
    @method_permission_classes([AllowAny])
    def list(self, request):
        """GET /api/activity-logs/ - List all activity logs"""
        user_id = request.query_params.get('user_id', None)
        action = request.query_params.get('action', None)
        
        logs = ActivityLog.objects.all()
        
        if user_id:
            logs = logs.filter(user_id=user_id)
        if action:
            logs = logs.filter(action=action)
        
        serializer = ActivityLogSerializer(logs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @method_permission_classes([AllowAny])
    def create(self, request):
        """POST /api/activity-logs/ - Create activity log"""
        serializer = ActivityLogSerializer(data=request.data)
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
