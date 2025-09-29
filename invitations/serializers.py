# invitations/serializers.py

from rest_framework import serializers
from django.urls import reverse
from .models import Invitation
from members.models import Membership

class CreateInvitationSerializer(serializers.Serializer):
    emails = serializers.ListField(child=serializers.EmailField())

    def validate_emails(self, emails):
        group = self.context['group']
        user  = self.context['request'].user

        # 1) No duplicates in the batch
        if len(emails) != len(set(emails)):
            raise serializers.ValidationError("Duplicate emails in list.")

        # 2) Only group owners/admins may invite
        if not Membership.objects.filter(
            group=group,
            user=user,
            role__in=[Membership.ROLE_OWNER, Membership.ROLE_ADMIN]
        ).exists():
            raise serializers.ValidationError("You are not authorized to invite to this group.")

        # 3) Can't re-invite existing members or pending invitations
        for email in emails:
            if Membership.objects.filter(group=group, user__email__iexact=email).exists():
                raise serializers.ValidationError(f"{email} is already a member.")
            if Invitation.objects.filter(
                group=group,
                email__iexact=email,
                status=Invitation.STATUS_PENDING
            ).exists():
                raise serializers.ValidationError(f"{email} has already been invited.")
        return emails


class InvitationSerializer(serializers.ModelSerializer):
    invited_by      = serializers.EmailField(source='invited_by.email', read_only=True)
    invitation_link = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            'id',
            'group',
            'email',
            'token',
            'invited_by',
            'status',
            'sent_at',
            'accepted_at',
            'expires_at',
            'invitation_link',
        ]
        read_only_fields = [
            'id',
            'token',
            'invited_by',
            'status',
            'sent_at',
            'accepted_at',
            'expires_at',
            'invitation_link',
        ]

    def get_invitation_link(self, obj):
        request = self.context.get('request')
        path    = reverse(
                     'invitation-accept',
                     args=[str(obj.group.id), str(obj.token)]
                  )
        return request.build_absolute_uri(path)
