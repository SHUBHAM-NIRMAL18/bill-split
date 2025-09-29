from django.db import models

# Create your models here.
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from groups.models import Group

User = get_user_model()

class Activity(models.Model):
    """
    Simple activity tracking for group actions.
    Tracks what happened, who did it, and when.
    """
    
    ACTIVITY_TYPES = [
        ('expense_created', 'Expense Created'),
        ('expense_updated', 'Expense Updated'),
        ('expense_deleted', 'Expense Deleted'),
        ('settlement_created', 'Settlement Created'),
        ('settlement_confirmed', 'Settlement Confirmed'),
        ('settlement_rejected', 'Settlement Rejected'),
        ('member_joined', 'Member Joined'),
        ('member_left', 'Member Left'),
        ('member_added', 'Member Added'),
        ('member_removed', 'Member Removed'),
        ('group_created', 'Group Created'),
        ('group_updated', 'Group Updated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    
    # Activity details
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Optional metadata (JSON field for flexibility)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'
        
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} in {self.group.name}"
