from django.apps import AppConfig


app_name = 'core' # Nombre de la aplicación

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Registrar señales (login merge cart)
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
