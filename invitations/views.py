# Update your invitations/views.py

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from members.models import Membership
from groups.models import Group  # Add this import
from .models import Invitation
from .serializers import CreateInvitationSerializer, InvitationSerializer
from rest_framework import status

class InvitationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """
    GET  /groups/{group_id}/invitations/   → list pending invites
    POST /groups/{group_id}/invitations/   → send new invite(s)
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateInvitationSerializer
        return InvitationSerializer

    def get_queryset(self):
        return Invitation.objects.filter(
            group_id=self.kwargs['group_id'],
            status=Invitation.STATUS_PENDING
        )

    # FIXED: Add serializer context with group
    def get_serializer_context(self):
        context = super().get_serializer_context()
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        context['group'] = group
        return context

    def perform_create(self, serializer):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)  # Get group object
        emails = serializer.validated_data['emails']

        # Only owners/admins can invite
        if not Membership.objects.filter(
            group_id=group_id,
            user=self.request.user,
            role__in=[Membership.ROLE_OWNER, Membership.ROLE_ADMIN]
        ).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not allowed to invite to this group.")

        created = []
        for email in emails:
            inv = Invitation.objects.create(
                group_id=group_id,
                email=email,
                invited_by=self.request.user,
                expires_at=timezone.now() + timezone.timedelta(days=7)
            )
            created.append(inv)
            
            # UPDATED: Use PUBLIC invitation URL (no dashboard route)
            frontend_base_url = "http://localhost:3000"  # Change this to your domain in production
            public_invitation_url = f"{frontend_base_url}/invitations/{group_id}/{inv.token}"
            
            # Enhanced email content
            email_subject = f"You're invited to join '{group.name}' on Bill Split"
            email_message = f"""
    Hi there!

    {self.request.user.email} has invited you to join the group "{group.name}" on Bill Split.

    With this group, you can:
    • Split expenses with friends
    • Track who owes what  
    • Settle up easily
    • Keep everything transparent

    Click the link below to accept your invitation:
    {public_invitation_url}

    This invitation expires in 7 days.

    If you don't have an account yet, you'll be able to create one when you click the link.

    Happy splitting!
    The Bill Split Team
            """
            
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        return created

    # FIXED: Override create to return proper response
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitations = self.perform_create(serializer)
        
        # Return the created invitations
        response_serializer = InvitationSerializer(invitations, many=True, context=self.get_serializer_context())
        return Response(
            {
                "message": f"Successfully sent {len(invitations)} invitation(s)",
                "data": response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )

class AcceptInvitationAPIView(APIView):
    """
    POST /api/v1/groups/{group_id}/invitations/accept/{token}/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id=None, token=None, *args, **kwargs):
        # 1) Find the pending invitation
        invitation = get_object_or_404(
            Invitation,
            group_id=group_id,
            token=token,
            status=Invitation.STATUS_PENDING
        )

        # 2) Check expiration
        if invitation.expires_at < timezone.now():
            return Response(
                {"detail": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Verify the invitee's email matches the logged-in user
        if invitation.email.lower() != request.user.email.lower():
            return Response(
                {"detail": "This invitation is not for your account."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4) Add membership if not exists
        if not Membership.objects.filter(
            group_id=group_id,
            user=request.user
        ).exists():
            Membership.objects.create(
                group_id=group_id,
                user=request.user,
                role=Membership.ROLE_MEMBER
            )

        # 5) Mark invitation accepted
        invitation.status = Invitation.STATUS_ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save()

        return Response(
            {"message": "Invitation accepted successfully."},
            status=status.HTTP_200_OK
        )
        
        
