from rest_framework import serializers
from .models import Activity

class ActivitySerializer(serializers.ModelSerializer):
    """Serializes activity data for reading"""
    
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    group_id = serializers.UUIDField(source='group.id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            'id', 'group_id', 'group_name', 'user_id', 'user_email', 'user_name',
            'activity_type', 'activity_type_display', 'description', 'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
