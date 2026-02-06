from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Candidate
from users.models import User
from .serializers import CandidateSerializer
from activity_logs.models import ActivityLog


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@api_view(['GET', 'POST'])
def candidate_list_create(request):
    if request.method == 'GET':
        candidates = Candidate.objects.select_related('user').all()
        serializer = CandidateSerializer(candidates, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': candidates.count()
        })
    
    elif request.method == 'POST':
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'user_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if Candidate.objects.filter(user_id=user_id).exists():
            return Response({
                'success': False,
                'error': 'Candidate already exists for this user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert user_id to user before passing to serializer
        data = request.data.copy()
        data['user'] = user_id  # Change user_id to user
        serializer = CandidateSerializer(data=data)
        
        if serializer.is_valid():
            candidate = serializer.save(updated_ip=get_client_ip(request))
            
            # ✅ ADD THIS: Create activity log
            ActivityLog.objects.create(
                user=user if user else None,
                action='candidate_added',
                resource_type='Candidate',
                resource_id=candidate.id,
                details={'candidate_name': user.full_name, 'email': user.email},
                ip_address=get_client_ip(request)
            )
            
            

            return Response({
                'success': True,
                'data': CandidateSerializer(candidate).data,
                'message': 'Candidate created successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate.objects.select_related('user'), pk=pk)
    
    if request.method == 'GET':
        serializer = CandidateSerializer(candidate)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = CandidateSerializer(candidate, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_candidate = serializer.save(updated_ip=get_client_ip(request))
            
            # ✅ ADD THIS: Create activity log
            ActivityLog.objects.create(
                user=candidate.user if candidate.user else None,
                action='candidate_updated',
                resource_type='Candidate',
                resource_id=candidate.id,
                details={'candidate_name': candidate.user.full_name if candidate.user else 'Unknown'},
                ip_address=get_client_ip(request)
            )
            return Response({
                'success': True,
                'data': CandidateSerializer(updated_candidate).data,
                'message': 'Candidate updated successfully'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        candidate.delete()
        return Response({
            'success': True,
            'message': 'Candidate deleted successfully'
        })
