from django.db import transaction, models
from django.utils import timezone
from decimal import Decimal

from .models import Settlement, SettlementRequest, GroupSettlementSummary

class SettlementService:
    """Service class for managing settlements"""
    
    def __init__(self, group):
        self.group = group
        
    def create_settlement(self, payer, receiver, amount, method='cash', notes='', initiated_by=None):
        """Create a new settlement"""
        with transaction.atomic():
            settlement = Settlement.objects.create(
                group=self.group,
                payer=payer,
                receiver=receiver,
                amount=amount,
                method=method,
                notes=notes,
                initiated_by=initiated_by or payer,
                status='pending'
            )
            
            # Update group settlement summary
            self._update_group_summary()
            
            return settlement
            
    def confirm_settlement(self, settlement, confirmed_by):
        """Confirm a pending settlement"""
        if settlement.status != 'pending':
            raise ValueError("Only pending settlements can be confirmed.")
            
        with transaction.atomic():
            settlement.status = 'confirmed'
            settlement.confirmed_by = confirmed_by
            settlement.confirmed_at = timezone.now()
            settlement.save()
            
            # Update balances
            from balances.services import BalanceCalculationService
            balance_service = BalanceCalculationService(self.group)
            balance_service.calculate_all_balances()
            
            # Update group summary
            self._update_group_summary()
            
            return settlement
            
    def reject_settlement(self, settlement, rejected_by):
        """Reject a pending settlement"""
        if settlement.status != 'pending':
            raise ValueError("Only pending settlements can be rejected.")
            
        settlement.status = 'rejected'
        settlement.confirmed_by = rejected_by
        settlement.confirmed_at = timezone.now()
        settlement.save()
        
        return settlement
        
    def settle_all_debts(self, user):
        """Create settlements for all of user's debts"""
        from balances.models import DebtSummary
        
        # Get all debts where user is the debtor
        debts = DebtSummary.objects.filter(
            group=self.group,
            debtor=user,
            is_settled=False
        )
        
        settlements = []
        with transaction.atomic():
            for debt in debts:
                settlement = self.create_settlement(
                    payer=debt.debtor,
                    receiver=debt.creditor,
                    amount=debt.amount,
                    initiated_by=user
                )
                settlements.append(settlement)
                
        return settlements
        
    def _update_group_summary(self):
        """Update or create group settlement summary"""
        summary, created = GroupSettlementSummary.objects.get_or_create(
            group=self.group
        )
        summary.update_summary()
        
    def get_user_settlement_status(self, user):
        """Get settlement status for a specific user"""
        from balances.models import Balance
        
        try:
            balance = Balance.objects.get(group=self.group, user=user)
            return {
                'is_settled': balance.is_settled,
                'net_balance': balance.net_balance,
                'can_leave_group': balance.is_settled,
                'pending_settlements': Settlement.objects.filter(
                    group=self.group,
                    status='pending'
                ).filter(
                    models.Q(payer=user) | models.Q(receiver=user)
                ).count()
            }
        except Balance.DoesNotExist:
            return {
                'is_settled': True,
                'net_balance': Decimal('0.00'),
                'can_leave_group': True,
                'pending_settlements': 0
            }

class SettlementRequestService:
    """Service class for managing settlement requests"""
    
    def __init__(self, group):
        self.group = group
        
    def create_request(self, requested_by, requested_to, amount, message=''):
        """Create a settlement request"""
        from datetime import timedelta
        
        # Check for existing pending request
        existing_request = SettlementRequest.objects.filter(
            group=self.group,
            requested_by=requested_by,
            requested_to=requested_to,
            status='pending'
        ).first()
        
        if existing_request:
            raise ValueError("You already have a pending settlement request with this user.")
            
        expires_at = timezone.now() + timedelta(days=7)
        
        settlement_request = SettlementRequest.objects.create(
            group=self.group,
            requested_by=requested_by,
            requested_to=requested_to,
            amount=amount,
            message=message,
            expires_at=expires_at
        )
        
        return settlement_request
        
    def accept_request(self, request_obj, response_message=''):
        """Accept a settlement request and create settlement"""
        if request_obj.status != 'pending':
            raise ValueError("Only pending requests can be accepted.")
            
        if request_obj.is_expired:
            raise ValueError("This settlement request has expired.")
            
        with transaction.atomic():
            # Create settlement
            settlement_service = SettlementService(self.group)
            settlement = settlement_service.create_settlement(
                payer=request_obj.requested_by,
                receiver=request_obj.requested_to,
                amount=request_obj.amount,
                initiated_by=request_obj.requested_by
            )
            
            # Update request
            request_obj.status = 'accepted'
            request_obj.response_message = response_message
            request_obj.responded_at = timezone.now()
            request_obj.settlement = settlement
            request_obj.save()
            
            return settlement
            
    def reject_request(self, request_obj, response_message=''):
        """Reject a settlement request"""
        if request_obj.status != 'pending':
            raise ValueError("Only pending requests can be rejected.")
            
        request_obj.status = 'rejected'
        request_obj.response_message = response_message
        request_obj.responded_at = timezone.now()
        request_obj.save()
        
        return request_obj