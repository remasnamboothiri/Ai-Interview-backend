from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet
from .test_views import TestNotificationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'test-notifications', TestNotificationViewSet, basename='test-notification')

urlpatterns = [
    path('', include(router.urls)),
]
