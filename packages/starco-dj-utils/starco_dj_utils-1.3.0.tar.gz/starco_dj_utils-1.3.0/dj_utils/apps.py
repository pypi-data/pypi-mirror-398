from django.apps import AppConfig


class DjUtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dj_utils'
    def ready(self):
        from . import handlers
        from core import tasks_config
