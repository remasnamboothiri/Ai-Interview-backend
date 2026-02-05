from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, permission_classes as method_permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer, NotificationDetailSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message', 'notification_type']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        elif self.action == 'retrieve':
            return NotificationDetailSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        queryset = Notification.objects.select_related('user')
        
        # Filter by user_id if provided
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by notification type
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter out expired notifications
        exclude_expired = self.request.query_params.get('exclude_expired', 'false')
        if exclude_expired.lower() == 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset
    
    @method_permission_classes([AllowAny])
    def list(self, request):
        """GET /api/notifications/ - List notifications with pagination"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'data': serializer.data
                })
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
                'count': queryset.count()
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
            notification = self.get_object()
            serializer = self.get_serializer(notification)
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
            serializer = self.get_serializer(data=request.data)
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
        """PUT/PATCH /api/notifications/{id}/ - Update notification"""
        try:
            notification = self.get_object()
            serializer = self.get_serializer(notification, data=request.data, partial=True)
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
            notification = self.get_object()
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
            notification = self.get_object()
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            
            serializer = self.get_serializer(notification)
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
                'message': f'{updated_count} notifications marked as read',
                'updated_count': updated_count
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
    
    @action(detail=False, methods=['delete'], permission_classes=[AllowAny])
    def clear_all(self, request):
        """DELETE /api/notifications/clear_all/ - Delete all notifications for a user"""
        try:
            user_id = request.query_params.get('user_id')
            
            if not user_id:
                return Response({
                    'success': False,
                    'error': 'user_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            deleted_count = Notification.objects.filter(user_id=user_id).count()
            Notification.objects.filter(user_id=user_id).delete()
            
            return Response({
                'success': True,
                'message': f'{deleted_count} notifications deleted',
                'deleted_count': deleted_count
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)