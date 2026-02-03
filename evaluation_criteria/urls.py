from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvaluationCriteriaViewSet

router = DefaultRouter()
router.register(r'evaluation-criteria', EvaluationCriteriaViewSet, basename='evaluation-criteria')

urlpatterns = [
    path('', include(router.urls)),
]
