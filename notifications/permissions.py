from rest_framework.permissions import BasePermission

class DebugAllowAny(BasePermission):
    def has_permission(self, request, view):
        print(f"DEBUG: has_permission called")
        print(f"DEBUG: request.user = {request.user}")
        print(f"DEBUG: request.user.is_authenticated = {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else 'N/A'}")
        print(f"DEBUG: view = {view}")
        return True
