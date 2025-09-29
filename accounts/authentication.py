from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from cookies
    instead of Authorization header
    """
    
    def authenticate(self, request):
        # Try to get token from cookie first
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        
        if raw_token is None:
            # Fallback to header-based authentication
            return super().authenticate(request)
        
        # Validate the token
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        return (user, validated_token)