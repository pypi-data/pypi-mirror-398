

try:
    from firebase_admin import _apps, credentials, get_app, initialize_app
except ImportError as e:
    raise RuntimeError(
        "idtinc.firebase requires 'firebase-admin'. "
        "Install with: pip install idtinc[firebase]"
    ) from e


class FirebaseConfig:

    def __init__(self, authentication):
        if not authentication:
            raise ValueError("FIREBASE_AUTHENTICATION setting is required.")

        self.authentication = authentication

    @property
    def certificate(self):
        return credentials.Certificate(self.authentication)

    def initialize_app(self):
        return initialize_app(self.certificate)


def firebase_config():
    if not _apps:
        from django.conf import settings

        authentication = getattr(settings, "FIREBASE_AUTHENTICATION", None)
        if not authentication:
            raise ValueError("FIREBASE_AUTHENTICATION setting is required.")
        
        if not isinstance(authentication, dict):
            raise ValueError("FIREBASE_AUTHENTICATION must be a dictionary.")

        config = FirebaseConfig(authentication)
        firebase_app = config.initialize_app()
    else:
        firebase_app = get_app()

    return firebase_app
