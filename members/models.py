from django.db import models
import uuid
from django.conf import settings

User = settings.AUTH_USER_MODEL

# Create your models here.
class Membership(models.Model):
    ROLE_OWNER   = 'owner'
    ROLE_ADMIN   = 'admin'
    ROLE_MEMBER  = 'member'
    ROLE_CHOICES = [
        (ROLE_OWNER,  'Owner'),
        (ROLE_ADMIN,  'Admin'),
        (ROLE_MEMBER, 'Member'),
    ]

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user      = models.ForeignKey(User, related_name='memberships', on_delete=models.CASCADE)
    group     = models.ForeignKey('groups.Group', related_name='memberships', on_delete=models.CASCADE)
    role      = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user.email} in {self.group.name} as {self.role}"
