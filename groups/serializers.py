from rest_framework import serializers
from .models import Group
from categories.models import Category


class GroupSerializer(serializers.ModelSerializer):
    created_by = serializers.EmailField(source='created_by.email', read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )
    category_name = serializers.ReadOnlyField(source='category.name')
    class Meta:
        model  = Group
        fields = [
            'id', 'name', 'avatar', 'description','category', 'category_name',
            'created_by', 'created_at', 'updated_at'
        ]

    def validate_name(self, value):
        user = self.context['request'].user
        qs = Group.objects.filter(created_by=user, name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("You already have a group with this name.")
        return value

    def validate_avatar(self, file):
        if not file:
            return None
        if file.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Avatar must be no larger than 2 MB.")
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in ('jpg','jpeg','png','gif'):
            raise serializers.ValidationError("Avatar must be JPG, PNG, or GIF.")
        return file
