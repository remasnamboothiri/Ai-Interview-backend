from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CandidateEducation
from .serializers import CandidateEducationSerializer

@api_view(['GET', 'POST'])
def education_list_create(request):
    if request.method == 'GET':
        candidate_id = request.query_params.get('candidate_id')
        if candidate_id:
            education = CandidateEducation.objects.filter(candidate_id=candidate_id)
        else:
            education = CandidateEducation.objects.all()
        
        serializer = CandidateEducationSerializer(education, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': education.count()
        })
    
    elif request.method == 'POST':
        serializer = CandidateEducationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Education record created successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def education_detail(request, pk):
    try:
        education = CandidateEducation.objects.get(pk=pk)
    except CandidateEducation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Education record not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CandidateEducationSerializer(education)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = CandidateEducationSerializer(education, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Education record updated successfully'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        education.delete()
        return Response({
            'success': True,
            'message': 'Education record deleted successfully'
        })
