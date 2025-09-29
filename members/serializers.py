from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Membership

User = get_user_model()

class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    email   = serializers.EmailField(source='user.email', read_only=True)
    group_id = serializers.UUIDField(source='group.id', read_only=True)

    class Meta:
        model  = Membership
        fields = ['id','user_id','email','group_id','role','joined_at']

class CreateMembershipSerializer(serializers.Serializer):
    # FIXED: Accept email instead of user_id
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[Membership.ROLE_ADMIN, Membership.ROLE_MEMBER],
        default=Membership.ROLE_MEMBER
    )

    def validate_email(self, value):
        # Check if user exists with this email
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value.lower()

    def validate(self, data):
        group = self.context['group']
        user_email = data['email']
        
        # Get the user by email
        try:
            user = User.objects.get(email__iexact=user_email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        
        # Check if already a member
        if Membership.objects.filter(group=group, user=user).exists():
            raise serializers.ValidationError("User is already a member of this group.")
        
        return data

    def create(self, validated_data):
        group = self.context['group']
        user_email = validated_data['email']
        
        # Get user by email
        user = User.objects.get(email__iexact=user_email)
        
        return Membership.objects.create(
            group=group,
            user=user,
            role=validated_data['role']
        )

class UpdateMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Membership
        fields = ['role']

    def validate_role(self, value):
        if value == Membership.ROLE_OWNER:
            raise serializers.ValidationError("Cannot assign owner role here.")
        return value