from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, login_view, logout_view, refresh_token_view, current_user_view, reset_admin_password_view

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/refresh/', refresh_token_view, name='refresh'),
    path('auth/me/', current_user_view, name='current-user'),
    path('auth/reset-admin-password/', reset_admin_password_view, name='reset-admin-password'),
]
