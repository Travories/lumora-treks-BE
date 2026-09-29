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
    A private bucket behind stable media URLs.

    Signed S3 URLs expire (AWS_QUERYSTRING_EXPIRE), so any page, CDN or image
    optimizer that caches one ends up with a broken image. Instead, public
    website media (images, renditions, videos) gets a permanent URL —
    `/api/v2/media/<name>` — whose view redirects to a freshly signed URL.
    Everything else (e.g. documents, served through Wagtail's own view) keeps
    a directly signed URL.
    """

    PROXIED_PREFIXES = ("original_images/", "images/", "videos/")

    def url(self, name, parameters=None, expire=None, http_method=None):
        if not name:
            return ""
        if not getattr(self, "querystring_auth", True):
            # Public bucket: plain, already-stable URLs.
            return super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        if name.startswith(self.PROXIED_PREFIXES) and not (parameters or expire or http_method):
            from django.urls import reverse

            return reverse("media-redirect", args=[name])
        return self.signed_url(name, parameters=parameters, expire=expire, http_method=http_method)

    def signed_url(self, name, parameters=None, expire=None, http_method=None):
        """A presigned URL, cached so boto3 doesn't re-sign on every request."""
        cache_expire = expire or getattr(self, "querystring_expire", 3600)
        # Cache for 90% of the lifetime: a cached URL always has ≥10% left.
        cache_ttl = max(60, int(cache_expire * 0.9))
        cache_key = f"s3_url:{name}:{cache_expire}"
        if parameters is None and http_method is None:
            try:
                cached_url = cache.get(cache_key)
                if cached_url:
                    return cached_url
            except Exception:
                pass

        signed = super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        if parameters is None and http_method is None:
            try:
                cache.set(cache_key, signed, cache_ttl)
            except Exception:
                pass  # Fall back gracefully if the cache server is unavailable
        return signed
