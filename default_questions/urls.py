from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DefaultQuestionViewSet

router = DefaultRouter()
router.register(r'default-questions', DefaultQuestionViewSet, basename='default-questions')

urlpatterns = [
    path('', include(router.urls)),
]
