from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SettlementViewSet, SettlementRequestViewSet

router = DefaultRouter()
router.register(r'', SettlementViewSet, basename='settlement')
router.register(r'requests', SettlementRequestViewSet, basename='settlement-request')

urlpatterns = [
    path('', include(router.urls)),
]