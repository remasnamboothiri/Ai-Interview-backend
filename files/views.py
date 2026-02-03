from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import File
from .serializers import FileSerializer

@api_view(['GET', 'POST'])
def file_list_create(request):
    if request.method == 'GET':
        files = File.objects.filter(deleted_at__isnull=True)
        serializer = FileSerializer(files, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': files.count()
        })
    
    elif request.method == 'POST':
        # Basic file upload (simplified version)
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'File uploaded successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE'])
def file_detail(request, pk):
    try:
        file = File.objects.get(pk=pk, deleted_at__isnull=True)
    except File.DoesNotExist:
        return Response({
            'success': False,
            'message': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = FileSerializer(file)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'DELETE':
        from django.utils import timezone
        file.deleted_at = timezone.now()
        file.save()
        return Response({
            'success': True,
            'message': 'File deleted successfully'
        })
