from django.apps import AppConfig

from .initialize import firebase_config


class IdtincFirebaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name_plural = "Idtinc Firebase"
    verbose_name = "Idtinc Firebase"
    name = "idtinc.firebase"

    def ready(self):
        firebase_config()
