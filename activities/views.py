from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from groups.models import Group
from members.models import Membership
from .models import Activity
from .serializers import ActivitySerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=["Activities"])
class ActivityViewSet(ReadOnlyModelViewSet):
    """
    Read-only ViewSet for group activities.
    Only provides list and retrieve operations.
    """
    
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter activities by group"""
        group = self.get_group()
        return Activity.objects.filter(group=group).select_related('user', 'group')
        
    def get_group(self):
        """Get group and verify user access"""
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        
        # Verify user is a member
        if not Membership.objects.filter(group=group, user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not a member of this group.")
            
        return group
        
    def list(self, request, *args, **kwargs):
        """List activities with optional filtering"""
        queryset = self.get_queryset()
        
        # Filter by activity type if provided
        activity_type = request.query_params.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        # Limit results (default 50, max 100)
        limit = min(int(request.query_params.get('limit', 50)), 100)
        queryset = queryset[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Activities retrieved successfully',
            'data': serializer.data
        })
