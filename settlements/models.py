from django.db import models

# Create your models here.
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from groups.models import Group

User = get_user_model()

class Settlement(models.Model):
    """
    Represents a settlement transaction between two users in a group.
    Records when debts are marked as paid/settled.
    """
    
    SETTLEMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]
    
    SETTLEMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('digital_wallet', 'Digital Wallet'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='settlements')
    
    # Who paid money
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    # Who received money
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_received')
    
    # Settlement details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=SETTLEMENT_METHOD_CHOICES, default='cash')
    notes = models.TextField(blank=True, help_text="Optional notes about the settlement")
    
    # Status tracking
    status = models.CharField(max_length=10, choices=SETTLEMENT_STATUS_CHOICES, default='pending')
    
    # Settlement participants (who initiated and who needs to confirm)
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlements_initiated')
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='settlements_confirmed')
    
    # Timestamps
    settled_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-settled_at']
        
    def __str__(self):
        return f"{self.payer.email} paid {self.receiver.email} ${self.amount} in {self.group.name}"
        
    def clean(self):
        """Validate settlement data"""
        if self.payer == self.receiver:
            raise ValidationError("Payer and receiver cannot be the same person.")
            
        if self.amount <= 0:
            raise ValidationError("Settlement amount must be positive.")
            
        # Ensure both users are members of the group
        from members.models import Membership
        if not Membership.objects.filter(group=self.group, user=self.payer).exists():
            raise ValidationError("Payer is not a member of this group.")
            
        if not Membership.objects.filter(group=self.group, user=self.receiver).exists():
            raise ValidationError("Receiver is not a member of this group.")
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update balances when settlement is confirmed
        if self.status == 'confirmed' and not self.pk:
            self._update_balances()
            
    def _update_balances(self):
        """Update balance records after settlement is confirmed"""
        from balances.services import BalanceCalculationService
        service = BalanceCalculationService(self.group)
        service.calculate_all_balances()

class SettlementRequest(models.Model):
    """
    Tracks requests to settle specific debts between users.
    Used when one user wants to settle up with another.
    """
    
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='settlement_requests')
    
    # Users involved
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlement_requests_made')
    requested_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlement_requests_received')
    
    # Request details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, help_text="Optional message for the settlement request")
    
    # Status tracking
    status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES, default='pending')
    response_message = models.TextField(blank=True, help_text="Response message from the requested user")
    
    # Related settlement (when accepted)
    settlement = models.OneToOneField(Settlement, on_delete=models.SET_NULL, null=True, blank=True, related_name='request')
    
    # Timestamps
    expires_at = models.DateTimeField(help_text="When this request expires")
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Settlement request: {self.requested_by.email} -> {self.requested_to.email} for ${self.amount}"
        
    @property
    def is_expired(self):
        """Check if the settlement request has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at and self.status == 'pending'

class GroupSettlementSummary(models.Model):
    """
    Tracks overall settlement status for a group.
    Provides quick access to settlement statistics.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='settlement_summary')
    
    # Settlement statistics
    total_settlements = models.IntegerField(default=0)
    total_amount_settled = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_settlements = models.IntegerField(default=0)
    
    # Group settlement status
    is_fully_settled = models.BooleanField(default=False)
    last_settlement_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settlement Summary for {self.group.name}"
        
    def update_summary(self):
        """Update settlement statistics for the group"""
        confirmed_settlements = Settlement.objects.filter(
            group=self.group, 
            status='confirmed'
        )
        
        self.total_settlements = confirmed_settlements.count()
        self.total_amount_settled = confirmed_settlements.aggregate(
            total=models.Sum('amount')
        )['total'] or 0.00
        
        self.pending_settlements = Settlement.objects.filter(
            group=self.group, 
            status='pending'
        ).count()
        
        # Check if group is fully settled
        from balances.models import Balance
        self.is_fully_settled = not Balance.objects.filter(
            group=self.group, 
            is_settled=False
        ).exists()
        
        # Get last settlement date
        last_settlement = confirmed_settlements.first()
        self.last_settlement_date = last_settlement.confirmed_at if last_settlement else None
        
        self.save()
