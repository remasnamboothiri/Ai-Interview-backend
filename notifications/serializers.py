from rest_framework import serializers
from .models import Notification
from users.serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_name', 'user_email', 'notification_type', 
            'title', 'message', 'related_resource_type', 'related_resource_id',
            'action_url', 'is_read', 'read_at', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'user_name', 'user_email']

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'user', 'notification_type', 'title', 'message', 
            'related_resource_type', 'related_resource_id', 'action_url', 'expires_at'
        ]

class NotificationDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'created_at']