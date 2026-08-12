from .base import *  # noqa: F403
from .base import env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = "dev-insecure-change-me"  # noqa: S105 — local only
ALLOWED_HOSTS = ["*"]

# Any localhost port may talk to the CMS while developing.
CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Serve uploaded media through Django in development (see lumora/urls.py).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
