from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone

# Create your models here.

User = settings.AUTH_USER_MODEL

class Invitation(models.Model):
    STATUS_PENDING  = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EXPIRED  = 'expired'
    STATUS_CHOICES  = [
        (STATUS_PENDING,  'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_EXPIRED,  'Expired'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group       = models.ForeignKey(
        'groups.Group',
        related_name='invitations',
        on_delete=models.CASCADE
    )
    email       = models.EmailField()
    token       = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invited_by  = models.ForeignKey(
        User,
        related_name='sent_invitations',
        on_delete=models.CASCADE
    )
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    sent_at     = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at  = models.DateTimeField()

    class Meta:
        unique_together = ('group', 'email')

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invite {self.email} to {self.group.name} ({self.status})"
