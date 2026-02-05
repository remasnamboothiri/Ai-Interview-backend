from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes as method_permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    
    @method_permission_classes([AllowAny])
    def list(self, request):
        """GET /api/notifications/ - List all notifications"""
        try:
            user_id = request.query_params.get('user_id', None)
            
            if user_id:
                notifications = Notification.objects.filter(user_id=user_id).order_by('-created_at')
            else:
                notifications = Notification.objects.all().order_by('-created_at')
            
            serializer = NotificationSerializer(notifications, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @method_permission_classes([AllowAny])
    def retrieve(self, request, pk=None):
        """GET /api/notifications/{id}/ - Get single notification"""
        try:
            notification = Notification.objects.get(pk=pk)
            serializer = NotificationSerializer(notification)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @method_permission_classes([AllowAny])
    def create(self, request):
        """POST /api/notifications/ - Create notification"""
        try:
            serializer = NotificationSerializer(data=request.data)
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
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @method_permission_classes([AllowAny])
    def update(self, request, pk=None):
        """PUT /api/notifications/{id}/ - Update notification"""
        try:
            notification = Notification.objects.get(pk=pk)
            serializer = NotificationSerializer(notification, data=request.data, partial=True)
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
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @method_permission_classes([AllowAny])
    def destroy(self, request, pk=None):
        """DELETE /api/notifications/{id}/ - Delete notification"""
        try:
            notification = Notification.objects.get(pk=pk)
            notification.delete()
            return Response({
                'success': True,
                'message': 'Notification deleted successfully'
            })
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def mark_as_read(self, request, pk=None):
        """POST /api/notifications/{id}/mark_as_read/ - Mark notification as read"""
        try:
            notification = Notification.objects.get(pk=pk)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            
            serializer = NotificationSerializer(notification)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def mark_all_as_read(self, request):
        """POST /api/notifications/mark_all_as_read/ - Mark all notifications as read"""
        try:
            user_id = request.data.get('user_id')
            
            if not user_id:
                return Response({
                    'success': False,
                    'error': 'user_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            updated_count = Notification.objects.filter(
                user_id=user_id,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            return Response({
                'success': True,
                'message': f'{updated_count} notifications marked as read'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def unread_count(self, request):
        """GET /api/notifications/unread_count/ - Get unread notification count"""
        try:
            user_id = request.query_params.get('user_id')
            
            if not user_id:
                return Response({
                    'success': False,
                    'error': 'user_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            count = Notification.objects.filter(
                user_id=user_id,
                is_read=False
            ).count()
            
            return Response({
                'success': True,
                'unread_count': count
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)