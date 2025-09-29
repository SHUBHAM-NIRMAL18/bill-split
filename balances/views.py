from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from django.shortcuts import get_object_or_404

from groups.models import Group
from members.models import Membership
from .models import Balance, DebtSummary
from .serializers import (
    BalanceSerializer, 
    DebtSummarySerializer, 
    GroupBalanceSummarySerializer
)
from .services import BalanceCalculationService

class BalanceViewSet(GenericViewSet, ListModelMixin):
    """
    ViewSet for managing group balances.
    Provides endpoints for viewing and calculating balances.
    """
    
    serializer_class = BalanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter balances by group and ensure user has access"""
        group = self.get_group()
        return Balance.objects.filter(group=group).select_related('user', 'group')
        
    def get_group(self):
        """Get group and verify user has access"""
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        
        # Verify user is a member of the group
        if not Membership.objects.filter(group=group, user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not a member of this group.")
            
        return group
        
    def list(self, request, *args, **kwargs):
        """List all balances for the group"""
        group = self.get_group()
        
        # Ensure balances are up to date
        balance_service = BalanceCalculationService(group)
        balance_service.calculate_all_balances()
        
        # Get updated queryset
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Balances retrieved successfully',
            'data': serializer.data
        })
        
    @action(detail=False, methods=['post'])
    def recalculate(self, request, group_id=None):
        """Force recalculation of all balances"""
        group = self.get_group()
        
        # Recalculate all balances
        balance_service = BalanceCalculationService(group)
        balance_service.calculate_all_balances()
        
        return Response({
            'status': 'success',
            'message': 'Balances recalculated successfully'
        })
        
    @action(detail=False, methods=['get'])
    def summary(self, request, group_id=None):
        """Get complete balance summary for the group"""
        group = self.get_group()
        
        # Ensure balances are up to date
        balance_service = BalanceCalculationService(group)
        balance_service.calculate_all_balances()
        
        # Get summary data
        summary_data = balance_service.get_group_balance_summary()
        serializer = GroupBalanceSummarySerializer(summary_data)
        
        return Response({
            'status': 'success',
            'message': 'Balance summary retrieved successfully',
            'data': serializer.data
        })
        
    @action(detail=False, methods=['get'])
    def debts(self, request, group_id=None):
        """Get simplified debt relationships"""
        group = self.get_group()
        
        # Ensure debt summaries are up to date
        balance_service = BalanceCalculationService(group)
        balance_service.calculate_all_balances()
        
        # Get debt summaries
        debt_summaries = DebtSummary.objects.filter(group=group).select_related('debtor', 'creditor')
        serializer = DebtSummarySerializer(debt_summaries, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Debt relationships retrieved successfully',
            'data': serializer.data
        })