from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    RefreshAPIView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [

    path('register/',        RegisterAPIView.as_view(),    name='register'),
    path('login/',           LoginAPIView.as_view(),       name='login'),
    path('logout/',          LogoutAPIView.as_view(),      name='logout'),
    path('token/refresh/',   RefreshAPIView.as_view(),     name='token_refresh'),


    path('', include(router.urls)),
]
