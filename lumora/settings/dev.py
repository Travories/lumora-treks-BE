from .base import *  # noqa: F403
from .base import env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = "dev-insecure-change-me"  # noqa: S105 — local only
ALLOWED_HOSTS = ["*"]

# Any localhost port may talk to the CMS while developing.
CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Static files: serve straight from disk in dev (no manifest/hashing).
# Media (`default`): base.py already points it at the S3-compatible bucket
# when AWS_STORAGE_BUCKET_NAME is set — falls back to local FileSystemStorage
# (see lumora/urls.py) only when no bucket is configured.
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
if not AWS_STORAGE_BUCKET_NAME:
    STORAGES["default"] = {"BACKEND": "django.core.files.storage.FileSystemStorage"}

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
