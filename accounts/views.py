from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    EmailTokenObtainPairSerializer,
    LogoutSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema



User = get_user_model()

def _set_jwt_cookies(response, access_token, refresh_token):
    """Set JWT tokens as HTTP-only cookies"""
    
    # Set access token cookie
    response.set_cookie(
        settings.SIMPLE_JWT['AUTH_COOKIE'],  # 'access_token'
        access_token,
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],  # True
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],   # 'Lax'
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],           # '/'
        secure=False,  # Set to True in production with HTTPS
    )
    
    # Set refresh token cookie
    response.set_cookie(
        settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],  # 'refresh_token'
        refresh_token,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],  # True
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],   # 'Lax'
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],           # '/'
        secure=False,  # Set to True in production with HTTPS
    )

@extend_schema(tags=["Accounts"])
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = str(RefreshToken.for_user(user))
        access  = str(RefreshToken.for_user(user).access_token)

        resp = Response(
            {
                "message": "Registration successful.",
                "user": {
                    "user_id":   str(user.id),
                    "email":     user.email,
                    "first_name":user.first_name,
                    "last_name": user.last_name,
                }
            },
            status=status.HTTP_201_CREATED
        )
        _set_jwt_cookies(resp, access, refresh)
        return resp
@extend_schema(tags=["Accounts"])
class LoginAPIView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data

        resp = Response(
            {
                "message": "Login successful.",
                "user": {
                    "user_id":   tokens["user_id"],
                    "email":     tokens["email"],
                    "full_name": tokens["full_name"],
                }
            },
            status=status.HTTP_200_OK
        )
        
        # Set JWT cookies
        _set_jwt_cookies(resp, tokens["access_token"], tokens["refresh_token"])
        return resp

@extend_schema(tags=["Accounts"])
class RefreshAPIView(TokenRefreshView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        
        if not refresh_token:
            # Try to get from request body (for compatibility)
            refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {"error": "No refresh token provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update request data with refresh token
        request.data['refresh'] = refresh_token
        
        # Call parent refresh logic
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            data = response.data
            
            # Create new response with updated cookies
            new_response = Response(
                {
                    "message": "Token refresh successful.",
                    "access_token": data.get("access"),
                    "refresh_token": data.get("refresh"),
                },
                status=response.status_code
            )
            
            # Set new JWT cookies
            _set_jwt_cookies(
                new_response, 
                data.get("access"), 
                data.get("refresh")
            )
            
            return new_response
        
        return response

@extend_schema(tags=["Accounts"])
class LogoutAPIView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        try:
            # Get refresh token from cookie
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            
            if refresh_token:
                # Blacklist the refresh token
                serializer = self.get_serializer(data={'refresh': refresh_token})
                serializer.is_valid(raise_exception=True)
                serializer.save()
            
            response = Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK
            )
            
            # Clear JWT cookies
            response.delete_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
            )
            response.delete_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
            )
            
            return response
            
        except Exception as e:
            return Response(
                {"message": f"Logout failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

@extend_schema(tags=["Accounts"])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('list', 'destroy'):
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ('retrieve', 'update', 'partial_update'):
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [perm() for perm in permission_classes]

    def get_object(self):
        obj = super().get_object()
        if self.request.user != obj and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You may only modify your own user.")
        return obj
