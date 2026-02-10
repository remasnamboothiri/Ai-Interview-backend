from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from .models import User
from .serializers import UserSerializer
from activity_logs.models import ActivityLog

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint - validates email/password and returns JWT tokens
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "message": "Login successful",
        "data": {
            "user": {...user data...},
            "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'success': False,
            'message': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find user by email
        user = User.objects.get(email=email)
        
        # Check if user is active
        if not user.is_active:
            return Response({
                'success': False,
                'message': 'Account is inactive'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verify password
        if not check_password(password, user.password_hash):
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Update last login
        user.last_login_at = timezone.now()
        user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims to token
        refresh['email'] = user.email
        refresh['user_type'] = user.user_type
        
        # Create activity log
        try:
            ActivityLog.objects.create(
                user=user,
                action='user_login',
                resource_type='User',
                resource_id=user.id,
                details={'email': user.email, 'user_type': user.user_type},
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error creating activity log: {e}")
        
        # Serialize user data
        serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Refresh token endpoint - gets new access token using refresh token
    
    Request body:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    
    Response:
    {
        "success": true,
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response({
            'success': False,
            'message': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        return Response({
            'success': True,
            'access': access_token
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Invalid or expired refresh token'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint - blacklists the refresh token
    
    Request body:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Create activity log
        try:
            ActivityLog.objects.create(
                user=request.user,
                action='user_logout',
                resource_type='User',
                resource_id=request.user.id,
                details={'email': request.user.email},
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            print(f"Error creating activity log: {e}")
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Logout failed'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """
    Get current authenticated user
    
    Response:
    {
        "success": true,
        "data": {...user data...}
    }
    """
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_admin_password_view(request):
    """
    TEMPORARY: Reset admin password from .env file
    This endpoint will be removed after fixing the password issue
    """
    from decouple import config
    
    # Security: Only allow if a secret key is provided
    secret = request.data.get('secret')
    if secret != 'reset-admin-2024':
        return Response({
            'success': False,
            'message': 'Unauthorized'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        admin_email = config('ADMIN_EMAIL', default='ramasnampoothiry@gmail.com')
        admin_password = config('ADMIN_PASSWORD', default='rama@admin123')
        
        admin = User.objects.get(email=admin_email)
        admin.password_hash = make_password(admin_password)
        admin.save()
        
        return Response({
            'success': True,
            'message': f'Admin password reset successfully for {admin_email}'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Admin user not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# USER CRUD ENDPOINTS
# ============================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def list(self, request):
        users = self.get_queryset()
        serializer = self.get_serializer(users, many=True)
        return Response({
            'success': True,
            'count': users.count(),
            'data': serializer.data
        })
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Hash password before saving
            password = request.data.get('password')
            if password:
                serializer.validated_data['password_hash'] = make_password(password)
            
            user = serializer.save()
            
            # Create activity log
            try:
                ActivityLog.objects.create(
                    user=user,
                    action='user_registered',
                    resource_type='User',
                    resource_id=user.id,
                    details={'email': user.email, 'user_type': user.user_type},
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            except Exception as e:
                print(f"Error creating activity log: {e}")
            
            return Response({
                'success': True,
                'message': 'User created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(user)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                # Hash password if provided
                password = request.data.get('password')
                if password:
                    serializer.validated_data['password_hash'] = make_password(password)
                
                user = serializer.save()
                
                # Create activity log
                try:
                    ActivityLog.objects.create(
                        user=user,
                        action='user_updated',
                        resource_type='User',
                        resource_id=user.id,
                        details={'email': user.email},
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                except Exception as e:
                    print(f"Error creating activity log: {e}")
                
                return Response({
                    'success': True,
                    'message': 'User updated successfully',
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
            user.delete()
            return Response({
                'success': True,
                'message': 'User deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
