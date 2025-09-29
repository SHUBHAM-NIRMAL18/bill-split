from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Settlement, GroupSettlementSummary

@receiver(post_save, sender=Settlement)
def update_settlement_summary_on_save(sender, instance, created, **kwargs):
    """Update group settlement summary when settlement is saved"""
    summary, created = GroupSettlementSummary.objects.get_or_create(
        group=instance.group
    )
    summary.update_summary()

@receiver(post_delete, sender=Settlement)
def update_settlement_summary_on_delete(sender, instance, **kwargs):
    """Update group settlement summary when settlement is deleted"""
    try:
        summary = GroupSettlementSummary.objects.get(group=instance.group)
        summary.update_summary()
    except GroupSettlementSummary.DoesNotExist:
        pass