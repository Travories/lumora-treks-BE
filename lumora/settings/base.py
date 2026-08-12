"""
Base settings for the Lumora Treks CMS.

Everything the frontend renders is authored here: pages are built from a
StreamField of registered blocks (one block per React section component),
media lives in the Wagtail image / video library, and navigation, footer and
theme tokens live in site settings.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# lumora/settings/base.py -> lumora/settings -> lumora -> <project root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=None):
    value = os.environ.get(name)
    if not value:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "apilumora.rivetsoft.com"])

INSTALLED_APPS = [
    # Lumora apps
    "apps.core",
    "apps.catalog",
    "apps.cms",
    "apps.navigation",
    "apps.leads",
    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.api.v2",
    "wagtail",
    # Third party
    "modelcluster",
    "taggit",
    "rest_framework",
    "corsheaders",
    "django_filters",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "lumora.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

WSGI_APPLICATION = "lumora.wsgi.application"

# DATABASE_URL (postgres://user:pass@host:port/name) is the norm everywhere now;
# sqlite is only the fallback for a machine with no .env at all.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "Asia/Kathmandu")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --------------------------------------------------------------------------
# Cache Configuration (Redis for prod/dev when REDIS_URL is set)
# --------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", "")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "lumora",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "lumora-locmem",
        }
    }

# --------------------------------------------------------------------------
# Object storage for media (images/documents/videos) — S3-compatible bucket
# (AWS S3, DigitalOcean Spaces, Cloudflare R2, Backblaze B2, MinIO, …).
# Applies in dev AND prod whenever AWS_STORAGE_BUCKET_NAME is set, so a
# developer's local Wagtail admin uploads land in the same bucket as
# production — no separate "dev storage" to keep in sync.
# --------------------------------------------------------------------------
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", "")
if AWS_STORAGE_BUCKET_NAME:
    INSTALLED_APPS += ["storages"]
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", "")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", "")
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", "")
    AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL", "") or None
    # Enable signed URLs with expiration (default True) for secure/private S3 storage
    AWS_QUERYSTRING_AUTH = env_bool("AWS_QUERYSTRING_AUTH", True)
    AWS_QUERYSTRING_EXPIRE = int(env("AWS_QUERYSTRING_EXPIRE", "3600"))
    AWS_S3_FILE_OVERWRITE = False

    # Self-hosted S3-compatible servers (Garage, MinIO, …) generally need
    # path-style URLs (host/bucket/key) rather than virtual-hosted
    # (bucket.host/key) — override via AWS_S3_ADDRESSING_STYLE=virtual for
    # providers that want the AWS-style default.
    AWS_S3_ADDRESSING_STYLE = env("AWS_S3_ADDRESSING_STYLE", "path")
    STORAGES["default"] = {"BACKEND": "apps.core.storage.CachedS3Storage"}
    if AWS_S3_CUSTOM_DOMAIN and not AWS_QUERYSTRING_AUTH:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"



DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Uploaded video files can be large.
DATA_UPLOAD_MAX_MEMORY_SIZE = 256 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

# --------------------------------------------------------------------------
# Wagtail
# --------------------------------------------------------------------------
WAGTAIL_SITE_NAME = "Lumora Treks CMS"
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL", "http://localhost:8000")
WAGTAILIMAGES_IMAGE_MODEL = "core.CustomImage"
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "avif", "svg"]
WAGTAILDOCS_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "csv", "txt", "zip"]
WAGTAILSEARCH_BACKENDS = {
    "default": {"BACKEND": "wagtail.search.backends.database"},
}
WAGTAIL_ALLOW_UNICODE_SLUGS = False
WAGTAILEMBEDS_RESPONSIVE_HTML = True

# The API serves absolute URLs for media so Next.js <Image> can load them.
MEDIA_BASE_URL = env("MEDIA_BASE_URL", WAGTAILADMIN_BASE_URL)

WAGTAILAPI_BASE_URL = WAGTAILADMIN_BASE_URL
WAGTAILAPI_LIMIT_MAX = 200
WAGTAILAPI_SEARCH_ENABLED = True

# --------------------------------------------------------------------------
# API / CORS
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.api.pagination.LumoraPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"leads": "20/hour"},
    "UNAUTHENTICATED_USER": None,
}

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", "http://localhost:3000")

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://lumora.rivetsoft.com",
        "https://lumora-treks-fe.vercel.app",
    ],
)

CORS_ALLOW_CREDENTIALS = False
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", CORS_ALLOWED_ORIGINS)

# Optional shared secret for draft/preview fetches from the frontend.
PREVIEW_TOKEN = env("PREVIEW_TOKEN", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO")},
}
