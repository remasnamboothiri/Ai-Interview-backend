from rest_framework_simplejwt.authentication import JWTAuthentication
from users.models import User


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token.get("user_id")
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None