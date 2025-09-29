from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Settlement, SettlementRequest, GroupSettlementSummary

class SettlementSerializer(serializers.ModelSerializer):
    """Serializes settlement data for reading"""
    
    payer_id = serializers.UUIDField(source='payer.id', read_only=True)
    payer_email = serializers.EmailField(source='payer.email', read_only=True)
    payer_name = serializers.SerializerMethodField()
    
    receiver_id = serializers.UUIDField(source='receiver.id', read_only=True)
    receiver_email = serializers.EmailField(source='receiver.email', read_only=True)
    receiver_name = serializers.SerializerMethodField()
    
    initiated_by_id = serializers.UUIDField(source='initiated_by.id', read_only=True)
    initiated_by_email = serializers.EmailField(source='initiated_by.email', read_only=True)
    
    confirmed_by_id = serializers.UUIDField(source='confirmed_by.id', read_only=True)
    confirmed_by_email = serializers.EmailField(source='confirmed_by.email', read_only=True)
    
    group_id = serializers.UUIDField(source='group.id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = Settlement
        fields = [
            'id', 'group_id', 'group_name', 'payer_id', 'payer_email', 'payer_name',
            'receiver_id', 'receiver_email', 'receiver_name', 'amount', 'method', 
            'notes', 'status', 'initiated_by_id', 'initiated_by_email',
            'confirmed_by_id', 'confirmed_by_email', 'settled_at', 'confirmed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'settled_at', 'confirmed_at', 'created_at', 'updated_at']
        
    def get_payer_name(self, obj):
        return f"{obj.payer.first_name} {obj.payer.last_name}".strip()
        
    def get_receiver_name(self, obj):
        return f"{obj.receiver.first_name} {obj.receiver.last_name}".strip()

class CreateSettlementSerializer(serializers.ModelSerializer):
    """Handles settlement creation"""
    
    payer = serializers.UUIDField()
    receiver = serializers.UUIDField()
    
    class Meta:
        model = Settlement
        fields = [
            'payer', 'receiver', 'amount', 'method', 'notes'
        ]
        
    def validate(self, attrs):
        """Validate settlement data"""
        if attrs['payer'] == attrs['receiver']:
            raise serializers.ValidationError("Payer and receiver cannot be the same person.")
            
        if attrs['amount'] <= 0:
            raise serializers.ValidationError("Settlement amount must be positive.")
            
        return attrs
        
    def create(self, validated_data):
        """Create settlement with proper user resolution"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get the group from context
        group = self.context['group']
        request_user = self.context['request'].user
        
        # Resolve user objects
        payer = User.objects.get(id=validated_data['payer'])
        receiver = User.objects.get(id=validated_data['receiver'])
        
        # Create settlement
        settlement = Settlement.objects.create(
            group=group,
            payer=payer,
            receiver=receiver,
            amount=validated_data['amount'],
            method=validated_data['method'],
            notes=validated_data.get('notes', ''),
            initiated_by=request_user,
            status='pending'
        )
        
        return settlement

class SettlementRequestSerializer(serializers.ModelSerializer):
    """Serializes settlement request data"""
    
    requested_by_id = serializers.UUIDField(source='requested_by.id', read_only=True)
    requested_by_email = serializers.EmailField(source='requested_by.email', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    
    requested_to_id = serializers.UUIDField(source='requested_to.id', read_only=True)
    requested_to_email = serializers.EmailField(source='requested_to.email', read_only=True)
    requested_to_name = serializers.SerializerMethodField()
    
    group_id = serializers.UUIDField(source='group.id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = SettlementRequest
        fields = [
            'id', 'group_id', 'group_name', 'requested_by_id', 'requested_by_email', 
            'requested_by_name', 'requested_to_id', 'requested_to_email', 'requested_to_name',
            'amount', 'message', 'status', 'response_message', 'is_expired',
            'expires_at', 'responded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'expires_at', 'responded_at', 'created_at', 'updated_at']
        
    def get_requested_by_name(self, obj):
        return f"{obj.requested_by.first_name} {obj.requested_by.last_name}".strip()
        
    def get_requested_to_name(self, obj):
        return f"{obj.requested_to.first_name} {obj.requested_to.last_name}".strip()

class CreateSettlementRequestSerializer(serializers.ModelSerializer):
    """Handles settlement request creation"""
    
    requested_to = serializers.UUIDField()
    
    class Meta:
        model = SettlementRequest
        fields = ['requested_to', 'amount', 'message']
        
    def validate(self, attrs):
        """Validate settlement request data"""
        request_user = self.context['request'].user
        
        if attrs['requested_to'] == request_user.id:
            raise serializers.ValidationError("You cannot request settlement from yourself.")
            
        if attrs['amount'] <= 0:
            raise serializers.ValidationError("Settlement amount must be positive.")
            
        return attrs
        
    def create(self, validated_data):
        """Create settlement request with expiration"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        group = self.context['group']
        request_user = self.context['request'].user
        
        requested_to = User.objects.get(id=validated_data['requested_to'])
        
        # Set expiration to 7 days from now
        expires_at = timezone.now() + timedelta(days=7)
        
        settlement_request = SettlementRequest.objects.create(
            group=group,
            requested_by=request_user,
            requested_to=requested_to,
            amount=validated_data['amount'],
            message=validated_data.get('message', ''),
            expires_at=expires_at
        )
        
        return settlement_request

class GroupSettlementSummarySerializer(serializers.ModelSerializer):
    """Serializes group settlement summary"""
    
    group_id = serializers.UUIDField(source='group.id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = GroupSettlementSummary
        fields = [
            'id', 'group_id', 'group_name', 'total_settlements', 'total_amount_settled',
            'pending_settlements', 'is_fully_settled', 'last_settlement_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
