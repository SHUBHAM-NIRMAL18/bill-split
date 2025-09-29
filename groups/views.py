# groups/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import Group
from .serializers import GroupSerializer
from members.models import Membership
from members.serializers import MembershipSerializer

@extend_schema(tags=["Groups"])
class GroupViewSet(viewsets.ModelViewSet):
    """
    Basic CRUD for Group + list-members action.
    """
    lookup_field       = 'id'
    permission_classes = [IsAuthenticated]
    parser_classes     = [JSONParser, FormParser, MultiPartParser]
    serializer_class   = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list_members':
            return MembershipSerializer
        return GroupSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not qs.exists():
            return Response(
                {"message": "You’re not the owner of any groups yet.", "groups": []},
                status=status.HTTP_200_OK
            )
        data = self.get_serializer(qs, many=True).data
        return Response(
            {"message": "Groups retrieved successfully.", "groups": data},
            status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        group = serializer.save(created_by=self.request.user)
        Membership.objects.create(
            user=self.request.user,
            group=group,
            role=Membership.ROLE_OWNER
        )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # calls perform_create() under the hood
        self.perform_create(ser)

        headers = self.get_success_headers(ser.data)
        return Response(
            {"message": "Group created successfully.", "group": ser.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def retrieve(self, request, *args, **kwargs):
        grp = self.get_object()
        data = self.get_serializer(grp).data
        return Response(
            {"message": "Group retrieved successfully.", "group": data},
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        partial  = kwargs.pop('partial', False)
        instance = self.get_object()
        ser      = self.get_serializer(instance, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(
            {"message": "Group updated successfully.", "group": ser.data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """Delete group (only if all members are settled up)"""
        group = self.get_object()
    
        # Check if group is fully settled
        from settlements.models import GroupSettlementSummary
        try:
            summary = GroupSettlementSummary.objects.get(group=group)
            if not summary.is_fully_settled:
                return Response({
                    'status': 'error',
                    'message': 'Group cannot be deleted until all members are settled up'
                }, status=status.HTTP_400_BAD_REQUEST)
        except GroupSettlementSummary.DoesNotExist:
        # If no summary exists, check balances directly
            from balances.models import Balance
            unsettled_members = Balance.objects.filter(
                group=group, 
                is_settled=False
            ).count()
        
            if unsettled_members > 0:
                return Response({
                    'status': 'error',
                    'message': 'Group cannot be deleted until all members are settled up'
                }, status=status.HTTP_400_BAD_REQUEST)
    

    @action(detail=True, methods=['get'], url_path='members')
    def list_members(self, request, id=None):
        members = self.get_object().memberships.all()
        if not members.exists():
            return Response(
                {"message": "No members found.", "members": []},
                status=status.HTTP_200_OK
            )
        data = MembershipSerializer(members, many=True).data
        return Response(
            {"message": "Members retrieved successfully.", "members": data},
            status=status.HTTP_200_OK
        )
