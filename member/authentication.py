from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomJWTAuthentication(JWTAuthentication):
    """Custom JWT Authentication untuk tambahan validasi"""
    
    def get_user(self, validated_token):
        """Override untuk tambahan check"""
        try:
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            
            # Tambahan validasi
            if not user.is_active:
                raise InvalidToken('User account is disabled')
                
            return user
        except User.DoesNotExist:
            raise InvalidToken('User not found')