# idtinc

Idtinc is a small utility library for Django + Django REST Framework that provides:

- Reusable DRF serializers and custom fields (choice helpers, coordinates, BaseModelSerializer)
- Integration helpers and app configs to warn about required middleware/apps
- Optional Firebase initialization helper and AppConfig
- Query helpers for Postgres JSON, unaccent, json_agg, and storage URL helpers
- Message constants in Vietnamese for consistent API responses

This package is intended for Django projects that need common patterns and helpers extracted into a reusable library.

## Features

- `integration` AppConfig that validates required INSTALLED_APPS and MIDDLEWARE
- `firebase` helper to initialize `firebase-admin` using `FIREBASE_AUTHENTICATION` setting
- `integration.serializers.BaseModelSerializer` with `json_fields` support and nicer form-data handling
- Query helpers: `SubqueryJson`, `SubqueryJsonAgg`, `UnaccentVN`, `json_build_object`, etc.
- Storage helpers that call Django's `default_storage` (works with MinIO/backblaze backends)

## Requirements

- Python >= 3.9
- Django >= 3.2
- djangorestframework >= 3.14

Core dependencies are declared in `pyproject.toml`.

Optional extras:

- `firebase`: installs `firebase-admin` (use `pip install idtinc[firebase]`)

## Installation

Install from PyPI:

```bash
pip install idtinc
# or with firebase support
pip install idtinc[firebase]
```

## Quickstart

1. Add the package to `INSTALLED_APPS` in your Django settings:

```py
INSTALLED_APPS = [
    # ...
    "idtinc.integration",
    # optionally
    "idtinc.firebase",
]
```

2. Ensure the recommended middleware are present (or you will get a runtime warning from the AppConfig):

```py
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    # ...
    "django_currentuser.middleware.ThreadLocalUserMiddleware",
    "idtinc.integration.middleware.CustomLocaleMiddleware",
    "idtinc.integration.middleware.ExceptionMiddleware",
]
```

3. (Optional) Firebase initialization

Set `FIREBASE_AUTHENTICATION` in settings to the credentials object or path required by `firebase-admin`:

```py
# Example (path to service account JSON file):
FIREBASE_AUTHENTICATION = {
    "type": "",
    "project_id": "",
    "private_key_id": "",
    "private_key": "",
    "client_email": "",
    "client_id": "",
    "auth_uri": "",
    "token_uri": "",
    "auth_provider_x509_cert_url": "",
    "client_x509_cert_url": "",
    "universe_domain": "",
}
```

When `idtinc.firebase` AppConfig becomes ready it will call the helper that initializes the Firebase app.

4. Setup logging

```py
from idtinc.integration.logging import get_setup_logging

LOGGING = get_setup_logging()
```

## Usage examples

- BaseModelSerializer (handles form-data JSON fields):

```py
from idtinc.integration.serializers import BaseModelSerializer

class MySerializer(BaseModelSerializer):
    class Meta:
        model = MyModel
        fields = "__all__"
        json_fields = ("metadata",)
```

- Choice fields that output label/value pairs:

```py
from idtinc.integration.serializers import ChoiceField

class ItemSerializer(serializers.ModelSerializer):
    status = ChoiceField(choices=MyModel.STATUS_CHOICES)

    class Meta:
        model = MyModel
        fields = ("id", "status")
```

- Firebase helper (manual use):

```py
from idtinc.firebase.initialize import firebase_config

firebase_app = firebase_config()
```

## Configuration

Key settings used by the library:

- `FIREBASE_AUTHENTICATION` — dict for `firebase-admin` credentials (required when using `idtinc.firebase`)

The integration AppConfig will warn about missing apps/middleware but does not modify your settings automatically.

## Storage backends

The library uses Django's `default_storage` for generating storage URLs so you can plug in MinIO, Backblaze, or any Django storage backend. Example storage backends are provided under `src/idtinc/storage`.

1. MinIO Storage
```
Django Storage backend for MinIO.

Reads configuration from Django settings when not provided explicitly:
- STORAGE_MINIO_ENDPOINT
- STORAGE_MINIO_ACCESS_KEY
- STORAGE_MINIO_SECRET_KEY
- STORAGE_MINIO_SECURE
- STORAGE_MINIO_BUCKET_NAME

# For Django 4.2+
STORAGES = {
    "default": {
        "BACKEND": "django_library.core.files.storage.MinioStorage",
    },
}

# Or with options
STORAGES = {
    "default": {
        "BACKEND": "django_library.core.files.storage.MinioStorage",
        "OPTIONS": {
            "bucket_name": "",
            "endpoint": "", # s3.example.com
            "access_key": "",
            "secret_key": "",
            "secure": True,  # True or False
        },
    },
}

# For Django versions below 4.2
DEFAULT_FILE_STORAGE = "django_library.core.files.storage.MinioStorage"
```

2. Backblaze B2 Storage
```
# Django Storage backend for Backblaze B2.

Reads configuration from Django settings when not provided explicitly:
STORAGE_BACKBLAZE_APP_KEY
STORAGE_BACKBLAZE_ACCOUNT_ID
STORAGE_BACKBLAZE_BUCKET_NAME
STORAGE_BACKBLAZE_BUCKET_ID

# For Django 4.2+
STORAGES = {
    "default": {
        "BACKEND": "django_library.core.files.storage.BackblazeStorage",
    },
}

# Or with options
STORAGES = {
    "default": {
        "BACKEND": "django_library.core.files.storage.BackblazeStorage",
        "OPTIONS": {
            "app_key": "",
            "account_id": "",
            "bucket_name": "",
            "bucket_id": "",
        },
    },
}

# For Django versions below 4.2
DEFAULT_FILE_STORAGE = "django_library.core.files.storage.BackblazeStorage"
```

## Development

Run tests and linters (if present) in your local environment. See `pyproject.toml` for package metadata.

## License & Author

- Author: Kiều Văn Chương <vanchuongkieu@gmail.com>
- License: MIT

## Contributing

Issues and pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

If you'd like, I can also add short code examples for middleware usage, or generate a minimal example Django project showing integration. Which would you prefer next?
