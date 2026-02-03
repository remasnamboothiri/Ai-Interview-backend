from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterViewSet

router = DefaultRouter()
router.register(r'', RecruiterViewSet, basename='recruiter')

urlpatterns = [
    path('', include(router.urls)),
]
