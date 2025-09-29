from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/categories/', include('categories.urls')),

    # FIXED: Put specific nested routes BEFORE general groups route
    path('api/v1/groups/<uuid:group_id>/members/', include('members.urls')),
    path('api/v1/groups/<uuid:group_id>/invitations/', include('invitations.urls')),
    path('api/v1/groups/<uuid:group_id>/expenses/', include('expense.urls')),
    path('api/v1/groups/<uuid:group_id>/balances/', include('balances.urls')),
    path('api/v1/groups/<uuid:group_id>/settlements/', include('settlements.urls')),
    path('api/v1/groups/<uuid:group_id>/activities/', include('activities.urls')),
    
    # General groups route comes LAST
    path('api/v1/groups/', include('groups.urls')),

    # Swagger schema and UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)