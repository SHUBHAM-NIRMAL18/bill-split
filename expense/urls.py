# expense/urls.py

from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ExpenseViewSet

router = SimpleRouter()
router.register(r'', ExpenseViewSet, basename='group-expenses')

urlpatterns = [
    path('', include(router.urls)),
]
