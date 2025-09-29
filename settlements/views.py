from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from django.shortcuts import get_object_or_404
from django.db.models import Q

from groups.models import Group
from members.models import Membership
from .models import Settlement, SettlementRequest, GroupSettlementSummary
from .serializers import (
    SettlementSerializer, CreateSettlementSerializer,
    SettlementRequestSerializer, CreateSettlementRequestSerializer,
    GroupSettlementSummarySerializer
)
from .services import SettlementService, SettlementRequestService

class SettlementViewSet(ModelViewSet):
    """ViewSet for managing settlements"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateSettlementSerializer
        return SettlementSerializer
        
    def get_queryset(self):
        """Filter settlements by group"""
        group = self.get_group()
        return Settlement.objects.filter(group=group).select_related(
            'payer', 'receiver', 'initiated_by', 'confirmed_by', 'group'
        )
        
    def get_group(self):
        """Get group and verify user access"""
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        
        # Verify user is a member
        if not Membership.objects.filter(group=group, user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not a member of this group.")
            
        return group
        
    def get_serializer_context(self):
        """Add group and request to serializer context"""
        context = super().get_serializer_context()
        context['group'] = self.get_group()
        context['request'] = self.request
        return context
        
    def list(self, request, *args, **kwargs):
        """List settlements with optional filtering"""
        queryset = self.get_queryset()
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Filter by user involvement
        user_filter = request.query_params.get('user')
        if user_filter == 'me':
            queryset = queryset.filter(
                Q(payer=request.user) | Q(receiver=request.user)
            )
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Settlements retrieved successfully',
            'data': serializer.data
        })
        
    def create(self, request, *args, **kwargs):
        """Create a new settlement"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settlement = serializer.save()
        
        response_serializer = SettlementSerializer(settlement)
        return Response({
            'status': 'success',
            'message': 'Settlement created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
        
    @action(detail=True, methods=['post'])
    def confirm(self, request, group_id=None, pk=None):
        """Confirm a pending settlement"""
        settlement = self.get_object()
        
        if settlement.status != 'pending':
            return Response({
                'status': 'error',
                'message': 'Only pending settlements can be confirmed'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Only the receiver can confirm
        if settlement.receiver != request.user:
            return Response({
                'status': 'error',
                'message': 'Only the receiver can confirm this settlement'
            }, status=status.HTTP_403_FORBIDDEN)
            
        service = SettlementService(settlement.group)
        confirmed_settlement = service.confirm_settlement(settlement, request.user)
        
        serializer = self.get_serializer(confirmed_settlement)
        return Response({
            'status': 'success',
            'message': 'Settlement confirmed successfully',
            'data': serializer.data
        })
        
    @action(detail=True, methods=['post'])
    def reject(self, request, group_id=None, pk=None):
        """Reject a pending settlement"""
        settlement = self.get_object()
        
        if settlement.status != 'pending':
            return Response({
                'status': 'error',
                'message': 'Only pending settlements can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Only the receiver can reject
        if settlement.receiver != request.user:
            return Response({
                'status': 'error',
                'message': 'Only the receiver can reject this settlement'
            }, status=status.HTTP_403_FORBIDDEN)
            
        service = SettlementService(settlement.group)
        rejected_settlement = service.reject_settlement(settlement, request.user)
        
        serializer = self.get_serializer(rejected_settlement)
        return Response({
            'status': 'success',
            'message': 'Settlement rejected successfully',
            'data': serializer.data
        })
        
    @action(detail=False, methods=['post'])
    def settle_all(self, request, group_id=None):
        """Create settlements for all user's debts"""
        group = self.get_group()
        service = SettlementService(group)
        
        try:
            settlements = service.settle_all_debts(request.user)
            serializer = self.get_serializer(settlements, many=True)
            
            return Response({
                'status': 'success',
                'message': f'Created {len(settlements)} settlements',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SettlementRequestViewSet(GenericViewSet, ListModelMixin, CreateModelMixin):
    """ViewSet for managing settlement requests"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateSettlementRequestSerializer
        return SettlementRequestSerializer
        
    def get_queryset(self):
        """Filter settlement requests by group"""
        group = self.get_group()
        return SettlementRequest.objects.filter(group=group).select_related(
            'requested_by', 'requested_to', 'group'
        )
        
    def get_group(self):
        """Get group and verify user access"""
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        
        if not Membership.objects.filter(group=group, user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not a member of this group.")
            
        return group
        
    def get_serializer_context(self):
        """Add group and request to serializer context"""
        context = super().get_serializer_context()
        context['group'] = self.get_group()
        context['request'] = self.request
        return context
        
    def list(self, request, *args, **kwargs):
        """List settlement requests"""
        queryset = self.get_queryset()
        
        # Filter by involvement
        involvement = request.query_params.get('involvement')
        if involvement == 'sent':
            queryset = queryset.filter(requested_by=request.user)
        elif involvement == 'received':
            queryset = queryset.filter(requested_to=request.user)
            
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Settlement requests retrieved successfully',
            'data': serializer.data
        })
        
    def create(self, request, *args, **kwargs):
        """Create a settlement request"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settlement_request = serializer.save()
        
        response_serializer = SettlementRequestSerializer(settlement_request)
        return Response({
            'status': 'success',
            'message': 'Settlement request created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
        
    @action(detail=True, methods=['post'])
    def accept(self, request, group_id=None, pk=None):
        """Accept a settlement request"""
        settlement_request = self.get_object()
        
        if settlement_request.requested_to != request.user:
            return Response({
                'status': 'error',
                'message': 'You can only accept requests sent to you'
            }, status=status.HTTP_403_FORBIDDEN)
            
        if settlement_request.status != 'pending':
            return Response({
                'status': 'error',
                'message': 'Only pending requests can be accepted'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        response_message = request.data.get('response_message', '')
        
        try:
            service = SettlementRequestService(settlement_request.group)
            settlement = service.accept_request(settlement_request, response_message)
            
            settlement_serializer = SettlementSerializer(settlement)
            return Response({
                'status': 'success',
                'message': 'Settlement request accepted and settlement created',
                'data': settlement_serializer.data
            })
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
    @action(detail=True, methods=['post'])
    def reject(self, request, group_id=None, pk=None):
        """Reject a settlement request"""
        settlement_request = self.get_object()
        
        if settlement_request.requested_to != request.user:
            return Response({
                'status': 'error',
                'message': 'You can only reject requests sent to you'
            }, status=status.HTTP_403_FORBIDDEN)
            
        if settlement_request.status != 'pending':
            return Response({
                'status': 'error',
                'message': 'Only pending requests can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        response_message = request.data.get('response_message', '')
        
        service = SettlementRequestService(settlement_request.group)
        rejected_request = service.reject_request(settlement_request, response_message)
        
        serializer = self.get_serializer(rejected_request)
        return Response({
            'status': 'success',
            'message': 'Settlement request rejected',
            'data': serializer.data
        })