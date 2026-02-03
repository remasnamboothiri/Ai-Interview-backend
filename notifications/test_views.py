from rest_framework import viewsets
from .models import Notification
from .serializers import NotificationSerializer
from .permissions import DebugAllowAny

class TestNotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [DebugAllowAny]
