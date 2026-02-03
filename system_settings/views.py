from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import SystemSetting
from .serializers import SystemSettingSerializer
from rest_framework.permissions import AllowAny


class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [AllowAny]
    
    def list(self, request):
        """GET /api/system-settings/ - List all settings"""
        is_public = request.query_params.get('is_public', None)
        
        settings = SystemSetting.objects.all()
        
        if is_public is not None:
            settings = settings.filter(is_public=is_public.lower() == 'true')
        
        serializer = SystemSettingSerializer(settings, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """GET /api/system-settings/{id}/ - Get single setting"""
        try:
            setting = SystemSetting.objects.get(pk=pk)
            serializer = SystemSettingSerializer(setting)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except SystemSetting.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Setting not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        """POST /api/system-settings/ - Create setting"""
        serializer = SystemSettingSerializer(data=request.data)
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
        """PUT /api/system-settings/{id}/ - Update setting"""
        try:
            setting = SystemSetting.objects.get(pk=pk)
            serializer = SystemSettingSerializer(setting, data=request.data, partial=True)
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
        except SystemSetting.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Setting not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """DELETE /api/system-settings/{id}/ - Delete setting"""
        try:
            setting = SystemSetting.objects.get(pk=pk)
            setting.delete()
            return Response({
                'success': True,
                'message': 'Setting deleted successfully'
            })
        except SystemSetting.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Setting not found'
            }, status=status.HTTP_404_NOT_FOUND)
