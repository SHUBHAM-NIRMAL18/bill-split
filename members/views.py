from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Membership
from groups.models import Group
from .serializers import (
    MembershipSerializer,
    CreateMembershipSerializer,
    UpdateMembershipSerializer
)
from .permissions import (
    IsMembershipGroupOwner,
    IsMembershipGroupOwnerOrAdmin
)
from drf_spectacular.utils import extend_schema

@extend_schema(tags=["Members"])
class MembershipListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]  # Simplified permissions
    
    def get_group(self):
        return get_object_or_404(Group, id=self.kwargs['group_id'])

    def get_queryset(self):
        group = self.get_group()
        # only allow listing if the requester is a member
        if not group.memberships.filter(user=self.request.user).exists():
            return Membership.objects.none()
        return group.memberships.all()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['group'] = self.get_group()
        return ctx

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateMembershipSerializer
        return MembershipSerializer

    def create(self, request, *args, **kwargs):
        print(f"🔍 CREATE METHOD: Starting member creation")
        print(f"🔍 Request data: {request.data}")
        print(f"🔍 Group ID: {self.kwargs['group_id']}")
        print(f"🔍 User: {request.user}")
        
        # Custom permission check for POST
        group = self.get_group()
        print(f"🔍 Found group: {group.name}")
        
        # Check if user can manage members
        is_owner = group.created_by == request.user
        is_admin = False
        
        try:
            user_membership = Membership.objects.get(group=group, user=request.user)
            is_admin = user_membership.role in [Membership.ROLE_OWNER, Membership.ROLE_ADMIN]
            print(f"🔍 User membership: {user_membership.role}")
        except Membership.DoesNotExist:
            print(f"🔍 User has no membership in this group")
        
        print(f"🔍 Permissions: is_owner={is_owner}, is_admin={is_admin}")
        
        if not (is_owner or is_admin):
            print(f"🔍 Permission denied")
            return Response(
                {"message": "You don't have permission to add members to this group."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Proceed with normal creation
        try:
            serializer = CreateMembershipSerializer(
                data=request.data,
                context=self.get_serializer_context()
            )
            print(f"🔍 Serializer created")
            
            if serializer.is_valid():
                print(f"🔍 Serializer is valid")
                membership = serializer.save()
                print(f"🔍 Membership created: {membership}")
                out = MembershipSerializer(membership)
                return Response(
                    {"message": "Member added successfully.", "member": out.data},
                    status=status.HTTP_201_CREATED
                )
            else:
                print(f"🔍 Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"🔍 Exception in create: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not qs.exists():
            return Response(
                {"message": "No members in this group.", "members": []},
                status=status.HTTP_200_OK
            )
        data = MembershipSerializer(qs, many=True).data
        return Response(
            {"message": "Members retrieved successfully.", "members": data},
            status=status.HTTP_200_OK
        )
        
    def dispatch(self, request, *args, **kwargs):
        print(f"🔍 DISPATCH: Method={request.method}, Path={request.path}")
        print(f"🔍 DISPATCH: View class={self.__class__.__name__}")
        print(f"🔍 DISPATCH: kwargs={kwargs}")
        return super().dispatch(request, *args, **kwargs)


class MembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/groups/{group_id}/members/{user_id}/   -> view member
    PUT    /api/v1/groups/{group_id}/members/{user_id}/   -> update role
    PATCH  /api/v1/groups/{group_id}/members/{user_id}/   -> partial update
    DELETE /api/v1/groups/{group_id}/members/{user_id}/   -> remove member
    """
    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [
                permissions.IsAuthenticated(),
                IsMembershipGroupOwnerOrAdmin()
            ]
        if self.request.method == 'DELETE':
            return [
                permissions.IsAuthenticated(),
                IsMembershipGroupOwner()
            ]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        return get_object_or_404(
            Membership,
            group_id=self.kwargs['group_id'],
            user__id=self.kwargs['user_id']
        )

    def retrieve(self, request, *args, **kwargs):
        member = self.get_object()
        data   = MembershipSerializer(member).data
        return Response(
            {"message": "Member retrieved successfully.", "member": data},
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        member = self.get_object()
        serializer = UpdateMembershipSerializer(
            member,
            data=request.data,
            partial=kwargs.get('partial', False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Member role updated successfully.", "member": serializer.data},
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        """
        Remove member from group (only if settled up)
        """
        membership = self.get_object()
        group = membership.group
        user_to_remove = membership.user
    
    # Check if user is settled up
        from settlements.services import SettlementService
        settlement_service = SettlementService(group)
        user_status = settlement_service.get_user_settlement_status(user_to_remove)
    
        if not user_status['can_leave_group']:
            return Response({
                'status': 'error',
                'message': 'User cannot be removed from group until all debts are settled',
                'details': {
                    'net_balance': user_status['net_balance'],
                    'pending_settlements': user_status['pending_settlements']
                }
            }, status=status.HTTP_400_BAD_REQUEST)
