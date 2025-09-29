from .models import Activity

class ActivityService:
    """Simple service for creating activity logs"""
    
    @staticmethod
    def log_activity(group, user, activity_type, description, metadata=None):
        """Create an activity log entry"""
        return Activity.objects.create(
            group=group,
            user=user,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {}
        )
        
    @staticmethod
    def log_expense_created(group, user, expense):
        """Log expense creation"""
        return ActivityService.log_activity(
            group=group,
            user=user,
            activity_type='expense_created',
            description=f"Created expense '{expense.title}' for ${expense.amount}",
            metadata={
                'expense_id': str(expense.id),
                'amount': str(expense.amount),
                'expense_title': expense.title
            }
        )
        
    @staticmethod
    def log_expense_updated(group, user, expense):
        """Log expense update"""
        return ActivityService.log_activity(
            group=group,
            user=user,
            activity_type='expense_updated',
            description=f"Updated expense '{expense.title}'",
            metadata={
                'expense_id': str(expense.id),
                'expense_title': expense.title
            }
        )
        
    @staticmethod
    def log_expense_deleted(group, user, expense_title, amount):
        """Log expense deletion"""
        return ActivityService.log_activity(
            group=group,
            user=user,
            activity_type='expense_deleted',
            description=f"Deleted expense '{expense_title}' (${amount})",
            metadata={
                'expense_title': expense_title,
                'amount': str(amount)
            }
        )
        
    @staticmethod
    def log_settlement_created(group, user, settlement):
        """Log settlement creation"""
        return ActivityService.log_activity(
            group=group,
            user=user,
            activity_type='settlement_created',
            description=f"Created settlement: {settlement.payer.email} pays {settlement.receiver.email} ${settlement.amount}",
            metadata={
                'settlement_id': str(settlement.id),
                'amount': str(settlement.amount),
                'payer_email': settlement.payer.email,
                'receiver_email': settlement.receiver.email
            }
        )
        
    @staticmethod
    def log_settlement_confirmed(group, user, settlement):
        """Log settlement confirmation"""
        return ActivityService.log_activity(
            group=group,
            user=user,
            activity_type='settlement_confirmed',
            description=f"Confirmed settlement of ${settlement.amount} from {settlement.payer.email}",
            metadata={
                'settlement_id': str(settlement.id),
                'amount': str(settlement.amount),
                'payer_email': settlement.payer.email
            }
        )
        
    @staticmethod
    def log_member_joined(group, user):
        """Log member joining group"""
        return ActivityService.log_activity(
            group=group,
            user=user,
            activity_type='member_joined',
            description=f"{user.email} joined the group",
            metadata={
                'user_email': user.email
            }
        )
        
    @staticmethod
    def log_member_left(group, user):
        """Log member leaving group"""
        return ActivityService.log_activity(
            group=group,
            user=user,
            activity_type='member_left',
            description=f"{user.email} left the group",
            metadata={
                'user_email': user.email
            }
        )
