from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Expense, ExpenseParticipant
from .serializers import (
    ExpenseSerializer,
    CreateExpenseSerializer,
)
from groups.models import Group

from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(tags=['Expenses']),
    create=extend_schema(tags=['Expenses']),
    retrieve=extend_schema(tags=['Expenses']),
    update=extend_schema(tags=['Expenses']),
    partial_update=extend_schema(tags=['Expenses']),
    destroy=extend_schema(tags=['Expenses']),
)
class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return Expense.objects.filter(group_id=group_id)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateExpenseSerializer
        return ExpenseSerializer

    def perform_create(self, serializer):
        """Create expense and return it for further use"""
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)

        # Save the expense with the group
        expense = serializer.save(group=group)
        
        # ✅ Handle participants here (single source of truth)
        participants_data = self.request.data.get('participants', [])
        
        for p in participants_data:
            ExpenseParticipant.objects.create(
                expense=expense,
                user_id=p['user_id'],
                share=p.get('share', 0),
                percentage=p.get('percentage')
            )
        
        return expense

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the expense instance from perform_create
        expense = self.perform_create(serializer)
        
        # Log the activity
        from activities.services import ActivityService
        ActivityService.log_expense_created(expense.group, request.user, expense)

        return Response(
            {"message": "Expense created successfully."},
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        expense = self.get_object()
        serializer = self.get_serializer(expense)
        return Response(
            {"message": "Expense retrieved.", "expense": serializer.data},
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        expense = self.get_object()
        serializer = self.get_serializer(expense, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Log the activity before updating
        from activities.services import ActivityService
        ActivityService.log_expense_updated(expense.group, request.user, expense)

        # Use the serializer's update method (which now handles participants properly)
        updated_expense = serializer.save()
        
        # Return the updated expense with participants
        response_serializer = ExpenseSerializer(updated_expense)
        return Response(
            {"message": "Expense updated.", "expense": response_serializer.data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        expense = self.get_object()
        expense_title = expense.title
        expense_amount = expense.amount
        group = expense.group
        
        # Delete the expense
        self.perform_destroy(expense)
        
        # Log the deletion
        from activities.services import ActivityService
        ActivityService.log_expense_deleted(group, request.user, expense_title, expense_amount)
        
        return Response(
            {"message": "Expense deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )