from django.contrib.staticfiles.storage import (ManifestStaticFilesStorage,
                                                StaticFilesStorage)


class StaticFilesStorage(StaticFilesStorage):
    def __new__(cls, *args, **kwargs):
        from django.conf import settings
        
        if not getattr(settings, "DEBUG", True):
            return ManifestStaticFilesStorage(*args, **kwargs)

        return super().__new__(cls, *args, **kwargs)