import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Group(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=255)
    avatar      = models.ImageField(upload_to='group_avatars/', null=True, blank=True)
    description = models.TextField(blank=True)
    created_by  = models.ForeignKey(
        User,
        related_name='owned_groups',
        on_delete=models.CASCADE
    )
    category    = models.ForeignKey(
        'categories.Category',
        related_name='groups',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['created_by', 'name'],
                name='unique_group_name_per_user'
            )
        ]

    def __str__(self):
        return f"{self.name} (owner={self.created_by})"
