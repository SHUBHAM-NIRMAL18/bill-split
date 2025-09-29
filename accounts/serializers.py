from django.contrib.auth import get_user_model, password_validation
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import uuid
from .models import User

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name",
            "avatar", "is_active", "is_staff", "date_joined", "updated_at"
        )
        read_only_fields = ("id", "date_joined", "updated_at", "is_staff")


class RegisterSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Optional profile picture (JPEG, PNG or GIF; max 2 MB)."
    )
    password1 = serializers.CharField(
        write_only=True, min_length=8, style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, min_length=8, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "avatar",
            "password1",
            "password2",
        )

    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_avatar(self, file):
        if file is None:
            return None

        max_size = 2 * 1024 * 1024 
        if file.size > max_size:
            raise serializers.ValidationError("Avatar size should not exceed 2 MB.")
        content_type = file.content_type
        if content_type not in ("image/jpeg", "image/png", "image/gif"):
            raise serializers.ValidationError(
                "Unsupported file type. Use JPEG, PNG or GIF."
            )
        return file

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match"})
        user = User(email=data["email"])
        try:
            password_validation.validate_password(data["password1"], user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password1': list(e.messages)})
        return data

    def create(self, validated_data):
        avatar = validated_data.pop("avatar", None)
        username = validated_data["email"]
        user = User.objects.create_user(
            id=uuid.uuid4(),
            username=username,
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password1"],
            avatar=avatar,
        )
        return user

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD
    default_error_messages = {
        'no_active_account': _('No account found with these credentials.')
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"]   = str(user.id)
        token["email"]     = user.email
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        return {
            "access_token":  data["access"],
            "refresh_token": data["refresh"],
            "user_id":       str(self.user.id),
            "email":         self.user.email,
            "full_name":     self.user.get_full_name(),
        }

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            RefreshToken(attrs["refresh"]).verify()
        except TokenError as e:
            raise serializers.ValidationError({"refresh": str(e)})
        return attrs

    def save(self, **kwargs):
        RefreshToken(self.validated_data["refresh"]).blacklist()
