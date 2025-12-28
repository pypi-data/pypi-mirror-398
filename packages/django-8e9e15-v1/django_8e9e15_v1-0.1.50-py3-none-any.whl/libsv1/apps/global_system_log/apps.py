from django.apps import AppConfig


class ModuleAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'libsv1.apps.global_system_log'

    def ready(self):
        from .tasks import start_scheduler

        start_scheduler()