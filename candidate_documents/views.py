from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CandidateDocument
from .serializers import CandidateDocumentSerializer

@api_view(['GET', 'POST'])
def document_list_create(request):
    if request.method == 'GET':
        candidate_id = request.query_params.get('candidate_id')
        if candidate_id:
            documents = CandidateDocument.objects.filter(candidate_id=candidate_id)
        else:
            documents = CandidateDocument.objects.all()
        
        serializer = CandidateDocumentSerializer(documents, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': documents.count()
        })
    
    elif request.method == 'POST':
        serializer = CandidateDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Document linked successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE'])
def document_detail(request, pk):
    try:
        document = CandidateDocument.objects.get(pk=pk)
    except CandidateDocument.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CandidateDocumentSerializer(document)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'DELETE':
        document.delete()
        return Response({
            'success': True,
            'message': 'Document unlinked successfully'
        })
