from django.core.management.base import BaseCommand
from django.utils import timezone
from settlements.models import SettlementRequest

class Command(BaseCommand):
    help = 'Mark expired settlement requests as expired'
    
    def handle(self, *args, **options):
        now = timezone.now()
        expired_requests = SettlementRequest.objects.filter(
            status='pending',
            expires_at__lt=now
        )
        
        count = expired_requests.update(status='expired')
        
        self.stdout.write(
            self.style.SUCCESS(f'Marked {count} settlement requests as expired')
        )
