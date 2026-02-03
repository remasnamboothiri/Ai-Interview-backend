from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterviewDataViewSet

router = DefaultRouter()
router.register(r'interview-data', InterviewDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
