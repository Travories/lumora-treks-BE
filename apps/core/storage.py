from django.core.cache import cache
from whitenoise.storage import CompressedManifestStaticFilesStorage

try:
    from storages.backends.s3 import S3Storage
except ImportError:
    S3Storage = object


class NonStrictCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """
    Extends WhiteNoise's CompressedManifestStaticFilesStorage with manifest_strict = False
    so missing staticfiles manifest entries do not throw 500 Server Errors.
    """
    manifest_strict = False


class CachedS3Storage(S3Storage):
    """
    Extends S3Storage to cache presigned/signed S3 URLs in Redis / Django Cache,
    preventing repeated boto3 URL signing operations on every request.
    """

    def url(self, name, parameters=None, expire=None, http_method=None):
        if not name:
            return ""

        # If querystring auth (signing) is disabled, rely on parent URL generation
        if not getattr(self, "querystring_auth", True):
            return super().url(name, parameters=parameters, expire=expire, http_method=http_method)

        cache_expire = expire or getattr(self, "querystring_expire", 3600)
        # Cache for slightly less than the expiration time (e.g., 90% of duration) to ensure safety
        cache_ttl = max(60, int(cache_expire * 0.9))
        cache_key = f"s3_url:{name}:{cache_expire}"

        try:
            cached_url = cache.get(cache_key)
            if cached_url:
                return cached_url
        except Exception:
            pass

        signed_url = super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        try:
            cache.set(cache_key, signed_url, cache_ttl)
        except Exception:
            pass  # Fallback gracefully if cache server is unavailable
        return signed_url
