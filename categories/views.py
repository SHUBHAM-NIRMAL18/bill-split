from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Category
from .serializers import CategorySerializer

from drf_spectacular.utils import extend_schema

@extend_schema(tags=["Categories"])
class CategoryViewSet(ModelViewSet):
    """
    ViewSet for managing categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'id']
    ordering = ['name']