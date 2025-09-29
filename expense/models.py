from django.db import models
from django.conf import settings
import uuid

# Create your models here.
User = settings.AUTH_USER_MODEL

class Expense(models.Model):
    SPLIT_EQUAL     = 'equal'
    SPLIT_UNEQUAL   = 'unequal'
    SPLIT_PERCENT   = 'percentage'
    SPLIT_CHOICES = [
        (SPLIT_EQUAL,     'Equally'),
        (SPLIT_UNEQUAL,   'Unequally'),
        (SPLIT_PERCENT,   'Percentage'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group       = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='expenses')
    title       = models.CharField(max_length=255)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    date        = models.DateField()
    paid_by     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses')
    split_type  = models.CharField(max_length=10, choices=SPLIT_CHOICES)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.amount}) in {self.group.name}"


class ExpenseParticipant(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense    = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='participants')
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    share      = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # for split_type = percentage

    class Meta:
        unique_together = ('expense', 'user')

    def __str__(self):
        return f"{self.user.email} owes {self.share} for {self.expense.title}"
