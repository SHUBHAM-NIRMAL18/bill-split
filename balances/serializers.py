from rest_framework import serializers
from .models import Balance, DebtSummary

class BalanceSerializer(serializers.ModelSerializer):
    """Serializes user balance data for reading"""
    
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    group_id = serializers.UUIDField(source='group.id', read_only=True)
    
    class Meta:
        model = Balance
        fields = [
            'id', 'user_id', 'email', 'first_name', 'last_name', 'full_name',
            'group_id', 'total_paid', 'total_owed', 'net_balance', 
            'status', 'is_settled', 'last_calculated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_calculated', 'created_at', 'updated_at']
        
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

class DebtSummarySerializer(serializers.ModelSerializer):
    """Serializes simplified debt relationships for reading"""
    
    debtor_id = serializers.UUIDField(source='debtor.id', read_only=True)
    debtor_email = serializers.EmailField(source='debtor.email', read_only=True)
    debtor_name = serializers.SerializerMethodField()
    
    creditor_id = serializers.UUIDField(source='creditor.id', read_only=True)  
    creditor_email = serializers.EmailField(source='creditor.email', read_only=True)
    creditor_name = serializers.SerializerMethodField()
    
    group_id = serializers.UUIDField(source='group.id', read_only=True)
    
    class Meta:
        model = DebtSummary
        fields = [
            'id', 'group_id', 'debtor_id', 'debtor_email', 'debtor_name',
            'creditor_id', 'creditor_email', 'creditor_name', 'amount', 
            'is_settled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_debtor_name(self, obj):
        return f"{obj.debtor.first_name} {obj.debtor.last_name}".strip()
        
    def get_creditor_name(self, obj):
        return f"{obj.creditor.first_name} {obj.creditor.last_name}".strip()

class GroupBalanceSummarySerializer(serializers.Serializer):
    """Serializes complete group balance summary"""
    
    group_id = serializers.UUIDField()
    group_name = serializers.CharField()
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_members = serializers.IntegerField()
    settled_members = serializers.IntegerField()
    unsettled_members = serializers.IntegerField()
    
    # Individual balances
    balances = BalanceSerializer(many=True)
    
    # Simplified debts
    simplified_debts = DebtSummarySerializer(many=True)
    
    # Summary stats
    total_amount_owed = serializers.DecimalField(max_digits=12, decimal_places=2)
    number_of_transactions_needed = serializers.IntegerField()
