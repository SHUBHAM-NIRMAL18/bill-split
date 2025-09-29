from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Membership
from groups.models import Group

class IsMembershipGroupOwner(permissions.BasePermission):
    """
    Only the owner of the group that this Membership belongs to may modify or delete it.
    """
    def has_permission(self, request, view):
        # For list/create operations, check if user is group owner
        if hasattr(view, 'kwargs') and 'group_id' in view.kwargs:
            try:
                group = Group.objects.get(id=view.kwargs['group_id'])
                return group.created_by == request.user
            except Group.DoesNotExist:
                return False
        return True
    
    def has_object_permission(self, request, view, obj):
        return (
            obj.group.created_by == request.user
        )

class IsMembershipGroupOwnerOrAdmin(permissions.BasePermission):
    """
    Allows action if the requester is the group owner or an admin within that group.
    """
    def has_permission(self, request, view):
        # For list/create operations, check if user is group owner or admin
        if hasattr(view, 'kwargs') and 'group_id' in view.kwargs:
            try:
                group = Group.objects.get(id=view.kwargs['group_id'])
                
                # Check if user is the group owner
                if group.created_by == request.user:
                    return True
                
                # Check if user is an admin member
                try:
                    caller_mem = Membership.objects.get(
                        group=group,
                        user=request.user
                    )
                    return caller_mem.role in (
                        Membership.ROLE_OWNER,
                        Membership.ROLE_ADMIN,
                    )
                except Membership.DoesNotExist:
                    return False
                    
            except Group.DoesNotExist:
                return False
        return True
    
    def has_object_permission(self, request, view, obj):
        try:
            # Check if user is the group owner
            if obj.group.created_by == request.user:
                return True
                
            # Check if user is an admin member
            caller_mem = Membership.objects.get(
                group=obj.group,
                user=request.user
            )
            return caller_mem.role in (
                Membership.ROLE_OWNER,
                Membership.ROLE_ADMIN,
            )
        except Membership.DoesNotExist:
            return False