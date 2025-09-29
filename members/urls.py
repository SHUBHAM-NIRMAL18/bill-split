from django.urls import path
from .views import MembershipListCreateView, MembershipDetailView

urlpatterns = [
    path('', MembershipListCreateView.as_view(), name='member-list-create'),
    path('<uuid:user_id>/', MembershipDetailView.as_view(), name='member-detail'),
]
