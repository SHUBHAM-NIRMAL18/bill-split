# Update your expense/serializers.py

from rest_framework import serializers
from .models import Expense, ExpenseParticipant
from django.utils import timezone

class ExpenseParticipantSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    email   = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ExpenseParticipant
        fields = ['id', 'user_id', 'email', 'share', 'percentage']

class CreateExpenseParticipantSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    share = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

class ExpenseSerializer(serializers.ModelSerializer):
    group_id = serializers.UUIDField(source='group.id', read_only=True)
    paid_by_id = serializers.UUIDField(source='paid_by.id', read_only=True)
    participants = ExpenseParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'group_id', 'title', 'amount', 'date', 'notes',
            'paid_by_id', 'split_type', 'created_at', 'updated_at', 'participants'
        ]

class CreateExpenseSerializer(serializers.ModelSerializer):
    participants = CreateExpenseParticipantSerializer(many=True, write_only=True)

    class Meta:
        model = Expense
        fields = [
            'group', 'title', 'amount', 'date', 'notes',
            'paid_by', 'split_type', 'participants'
        ]

    def validate(self, data):
        split_type = data.get('split_type')
        participants = self.initial_data.get('participants')
        amount = data.get('amount')

        if not participants:
            raise serializers.ValidationError({'participants': 'Participants required.'})

        if split_type == Expense.SPLIT_UNEQUAL:
            total = sum([float(p['share']) for p in participants])
            if round(total, 2) != float(amount):
                raise serializers.ValidationError({'participants': 'Total shares must equal expense amount.'})

        if split_type == Expense.SPLIT_PERCENT:
            total = sum([float(p['percentage']) for p in participants])
            if round(total, 2) != 100.0:
                raise serializers.ValidationError({'participants': 'Percentages must sum to 100.'})

        return data

    def create(self, validated_data):
        participants_data = self.initial_data.get('participants')
        expense = Expense.objects.create(**validated_data)

        for p in participants_data:
            user_id = p['user_id']
            share = p.get('share', 0)
            percentage = p.get('percentage', None)
            ExpenseParticipant.objects.create(
                expense=expense,
                user_id=user_id,
                share=share,
                percentage=percentage
            )
        return expense

    # FIXED: Add explicit update method for nested fields
    def update(self, instance, validated_data):
        # Remove participants from validated_data since we handle them separately
        participants_data = self.initial_data.get('participants', [])
        
        # Update basic expense fields
        instance.title = validated_data.get('title', instance.title)
        instance.amount = validated_data.get('amount', instance.amount)
        instance.date = validated_data.get('date', instance.date)
        instance.notes = validated_data.get('notes', instance.notes)
        instance.paid_by = validated_data.get('paid_by', instance.paid_by)
        instance.split_type = validated_data.get('split_type', instance.split_type)
        instance.save()

        # Handle participants update
        if participants_data:
            # Delete existing participants
            ExpenseParticipant.objects.filter(expense=instance).delete()
            
            # Create new participants
            for p in participants_data:
                user_id = p['user_id']
                share = p.get('share', 0)
                percentage = p.get('percentage', None)
                ExpenseParticipant.objects.create(
                    expense=instance,
                    user_id=user_id,
                    share=share,
                    percentage=percentage
                )
        
        return instance