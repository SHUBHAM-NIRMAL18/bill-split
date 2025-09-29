from django.apps import AppConfig

class SettlementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settlements'
    verbose_name = 'Settlements'
    
    def ready(self):
        import settlements.signals