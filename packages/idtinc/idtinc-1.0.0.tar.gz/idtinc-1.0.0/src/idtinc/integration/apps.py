import warnings

from django.apps import AppConfig


class IdtincIntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name_plural = "Idtinc Integration"
    verbose_name = "Idtinc Integration"
    name = "idtinc.integration"

    REQUIRED_APPS = [
        "drf_yasg",
        "corsheaders",
        "rest_framework",
        "django_currentuser",
        "rest_framework_simplejwt",
    ]

    REQUIRED_MIDDLEWARE = [
        "django_currentuser.middleware.ThreadLocalUserMiddleware",
        "idtinc.integration.middleware.CustomLocaleMiddleware",
        "idtinc.integration.middleware.ExceptionMiddleware",
        "corsheaders.middleware.CorsMiddleware",
    ]

    def ready(self):
        from django.conf import settings

        missing_apps = [app for app in self.REQUIRED_APPS if app not in settings.INSTALLED_APPS]

        if missing_apps:
            warnings.warn(f"[idtinc.integration] Missing INSTALLED_APPS: {missing_apps}", RuntimeWarning)

        missing_middlewares = [mw for mw in self.REQUIRED_MIDDLEWARE if mw not in settings.MIDDLEWARE]

        if missing_middlewares:
            warnings.warn(f"[idtinc.integration] Missing MIDDLEWARE: {missing_middlewares}", RuntimeWarning)