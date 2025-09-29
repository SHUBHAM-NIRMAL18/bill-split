from django.db import models

# Create your models here.
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from groups.models import Group

User = get_user_model()

class Balance(models.Model):
    """
    Tracks calculated balance for each user in each group.
    Positive balance = user is owed money
    Negative balance = user owes money
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='balances')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='balances')
    
    # Financial calculations
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_owed = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Status tracking
    is_settled = models.BooleanField(default=False)
    last_calculated = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'group')
        ordering = ['-net_balance', 'user__email']
        
    def __str__(self):
        return f"{self.user.email} in {self.group.name}: {self.net_balance}"
        
    @property
    def status(self):
        """Return balance status as string"""
        if self.net_balance == 0:
            return 'settled'
        elif self.net_balance > 0:
            return 'owed'
        else:
            return 'owes'

class DebtSummary(models.Model):
    """
    Simplified debt relationships after debt minimization algorithm.
    Shows the minimum number of transactions needed to settle all debts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='debt_summaries')
    
    # Who owes money
    debtor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debts')
    # Who is owed money  
    creditor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credits')
    
    # Amount to be transferred
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking
    is_settled = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('group', 'debtor', 'creditor')
        ordering = ['-amount', 'debtor__email']
        
    def __str__(self):
        return f"{self.debtor.email} owes {self.creditor.email} ${self.amount}"
