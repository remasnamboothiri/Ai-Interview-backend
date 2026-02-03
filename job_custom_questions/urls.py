from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobCustomQuestionViewSet

router = DefaultRouter()
router.register(r'job-custom-questions', JobCustomQuestionViewSet, basename='job-custom-questions')

urlpatterns = [
    path('', include(router.urls)),
]
