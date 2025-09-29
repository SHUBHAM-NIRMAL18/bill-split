from django.db.models import Sum, Q
from decimal import Decimal
from collections import defaultdict
from .models import Balance, DebtSummary
from expense.models import Expense, ExpenseParticipant
from members.models import Membership

class BalanceCalculationService:
    """Service class for calculating and managing group balances"""
    
    def __init__(self, group):
        self.group = group
        
    def calculate_all_balances(self):
        """Calculate balances for all group members"""
        # Get all group members
        members = Membership.objects.filter(group=self.group).select_related('user')
        
        for membership in members:
            self.calculate_user_balance(membership.user)
            
        # After calculating individual balances, generate debt summary
        self.generate_debt_summary()
        
    def calculate_user_balance(self, user):
        """Calculate balance for a specific user in the group"""
        
        # Calculate total amount paid by user
        total_paid = Expense.objects.filter(
            group=self.group, 
            paid_by=user
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Calculate total amount owed by user
        total_owed = ExpenseParticipant.objects.filter(
            expense__group=self.group,
            user=user
        ).aggregate(
            total=Sum('share')
        )['total'] or Decimal('0.00')
        
        # Calculate net balance (positive = owed money, negative = owes money)
        net_balance = total_paid - total_owed
        
        # Check if user is settled (balance is zero)
        is_settled = net_balance == Decimal('0.00')
        
        # Update or create balance record
        balance, created = Balance.objects.update_or_create(
            user=user,
            group=self.group,
            defaults={
                'total_paid': total_paid,
                'total_owed': total_owed,
                'net_balance': net_balance,
                'is_settled': is_settled,
            }
        )
        
        return balance
        
    def generate_debt_summary(self):
        """Generate simplified debt relationships using debt minimization algorithm"""
        
        # Clear existing debt summaries for this group
        DebtSummary.objects.filter(group=self.group).delete()
        
        # Get all balances for the group
        balances = Balance.objects.filter(group=self.group)
        
        # Separate debtors (negative balance) and creditors (positive balance)
        debtors = []  # [(user, amount_owed)]
        creditors = []  # [(user, amount_to_receive)]
        
        for balance in balances:
            if balance.net_balance < 0:
                debtors.append((balance.user, abs(balance.net_balance)))
            elif balance.net_balance > 0:
                creditors.append((balance.user, balance.net_balance))
                
        # Apply debt minimization algorithm
        simplified_debts = self._minimize_debts(debtors, creditors)
        
        # Create DebtSummary records
        for debtor, creditor, amount in simplified_debts:
            DebtSummary.objects.create(
                group=self.group,
                debtor=debtor,
                creditor=creditor,
                amount=amount
            )
            
    def _minimize_debts(self, debtors, creditors):
        """
        Debt minimization algorithm to reduce number of transactions.
        Returns list of (debtor, creditor, amount) tuples.
        """
        simplified_debts = []
        
        # Convert to mutable lists
        debtors = list(debtors)
        creditors = list(creditors)
        
        i, j = 0, 0
        
        while i < len(debtors) and j < len(creditors):
            debtor, debt_amount = debtors[i]
            creditor, credit_amount = creditors[j]
            
            # Determine settlement amount
            settlement_amount = min(debt_amount, credit_amount)
            
            # Record the debt relationship
            simplified_debts.append((debtor, creditor, settlement_amount))
            
            # Update remaining amounts
            debtors[i] = (debtor, debt_amount - settlement_amount)
            creditors[j] = (creditor, credit_amount - settlement_amount)
            
            # Move to next debtor if current one is settled
            if debtors[i][1] == 0:
                i += 1
                
            # Move to next creditor if current one is settled  
            if creditors[j][1] == 0:
                j += 1
                
        return simplified_debts
        
    def get_group_balance_summary(self):
        """Get complete balance summary for the group"""
        from expense.models import Expense
        
        # Calculate group statistics
        total_expenses = Expense.objects.filter(group=self.group).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        balances = Balance.objects.filter(group=self.group).select_related('user')
        debt_summaries = DebtSummary.objects.filter(group=self.group).select_related('debtor', 'creditor')
        
        total_members = balances.count()
        settled_members = balances.filter(is_settled=True).count()
        unsettled_members = total_members - settled_members
        
        # Calculate total amount in circulation (sum of all positive balances)
        total_amount_owed = balances.filter(net_balance__gt=0).aggregate(
            total=Sum('net_balance')
        )['total'] or Decimal('0.00')
        
        return {
            'group_id': self.group.id,
            'group_name': self.group.name,
            'total_expenses': total_expenses,
            'total_members': total_members,
            'settled_members': settled_members,
            'unsettled_members': unsettled_members,
            'balances': balances,
            'simplified_debts': debt_summaries,
            'total_amount_owed': total_amount_owed,
            'number_of_transactions_needed': debt_summaries.count(),
        }
