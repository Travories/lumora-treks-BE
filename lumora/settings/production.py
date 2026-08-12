from .base import *  # noqa: F403
from .base import env, env_bool

DEBUG = False

# Fail loudly instead of shipping the development key.
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production")

# base.py already builds DATABASES from DATABASE_URL (falling back to sqlite
# when unset, e.g. on a bare CI box) — in production we require Postgres.
if not env("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL must be set in production (sqlite is dev-only)")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "SAMEORIGIN"

# Media in production: point these at S3/Cloudinary via django-storages if used.
if env("AWS_STORAGE_BUCKET_NAME"):
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}  # noqa: F405
