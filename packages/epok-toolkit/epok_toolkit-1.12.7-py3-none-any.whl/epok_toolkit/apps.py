from django.apps import AppConfig
from django.conf import settings

class EpokToolkitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'epok_toolkit'

    def ready(self):
        # Importar tus settings por defecto
        from . import default_settings

        for setting in dir(default_settings):
            if setting.isupper() and not hasattr(settings, setting):
                setattr(settings, setting, getattr(default_settings, setting))