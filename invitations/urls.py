from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import InvitationViewSet, AcceptInvitationAPIView

router = SimpleRouter()
router.register(r'', InvitationViewSet, basename='group-invitations')

urlpatterns = [
    path('', include(router.urls)),
    # FIXED: The group_id is already in the main URL pattern, just need token here
    path('accept/<uuid:token>/', AcceptInvitationAPIView.as_view(), name='invitation-accept'),
]