from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterviewScreenshotViewSet

router = DefaultRouter()
router.register(r'', InterviewScreenshotViewSet, basename='interview-screenshot')

urlpatterns = [
    path('', include(router.urls)),
]
