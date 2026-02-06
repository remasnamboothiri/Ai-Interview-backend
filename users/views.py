from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def list(self, request):
        users = self.get_queryset()
        serializer = self.get_serializer(users, many=True)
        return Response({
            'success': True,
            'count': users.count(),
            'data': serializer.data
        })
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
             # ✅ ADD THIS: Create activity log
            ActivityLog.objects.create(
                user=user,
                action='user_registered',
                resource_type='User',
                resource_id=user.id,
                details={'email': user.email, 'user_type': user.user_type},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({
                'success': True,
                'message': 'User created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(user)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                user = serializer.save()
                
                # ✅ ADD THIS: Create activity log
                ActivityLog.objects.create(
                    user=user,
                    action='user_updated',
                    resource_type='User',
                    resource_id=user.id,
                    details={'email': user.email},
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                return Response({
                    'success': True,
                    'message': 'User updated successfully',
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
            user.delete()
            return Response({
                'success': True,
                'message': 'User deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
