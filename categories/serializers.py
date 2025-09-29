from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    groups_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'groups_count']
        read_only_fields = ['id']

    def get_groups_count(self, obj):
        return obj.groups.count()

    def validate_name(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Category name must be at least 5 characters long.")
        return value.strip().title()