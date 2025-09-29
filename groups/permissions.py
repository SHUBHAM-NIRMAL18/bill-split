from rest_framework import permissions
from .models import Membership

class IsGroupOwner(permissions.BasePermission):
    """
    Allows access only to the group owner.
    """
    def has_object_permission(self, request, view, obj):
        try:
            membership = Membership.objects.get(group=obj, user=request.user)
            return membership.role == Membership.ROLE_OWNER
        except Membership.DoesNotExist:
            return False

class IsGroupOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access to group owner or any admin in the group.
    """
    def has_object_permission(self, request, view, obj):
        try:
            membership = Membership.objects.get(group=obj, user=request.user)
            return membership.role in (
                Membership.ROLE_OWNER,
                Membership.ROLE_ADMIN
            )
        except Membership.DoesNotExist:
            return False
