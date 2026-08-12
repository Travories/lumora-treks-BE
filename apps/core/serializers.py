"""
Plain-dict serializers shared by the block API representations and the DRF
endpoints, so an image always looks the same wherever it appears in the API.
"""

from django.conf import settings

# Rendition specs generated for every image exposed through the API.
# Keep these in sync with the `sizes` attributes used by the Next.js frontend.
IMAGE_RENDITIONS = {
    "thumb": "fill-400x300|format-webp|webpquality-80",
    "card": "fill-800x600|format-webp|webpquality-82",
    "square": "fill-800x800|format-webp|webpquality-82",
    "wide": "fill-1600x900|format-webp|webpquality-82",
    "hero": "width-2400|format-webp|webpquality-82",
}


def absolute_url(url):
    """Turn /media/... into http://host/media/... so Next.js can load it."""
    if not url:
        return None
    if url.startswith(("http://", "https://", "//", "data:")):
        return url
    base = (getattr(settings, "MEDIA_BASE_URL", "") or "").rstrip("/")
    return f"{base}{url}" if base else url


def serialize_image(image, renditions=None):
    """
    Serialize a CustomImage into the shape the frontend consumes.

    Returns None for an empty chooser so blocks can render conditionally.
    """
    if image is None:
        return None

    specs = IMAGE_RENDITIONS if renditions is None else {
        name: IMAGE_RENDITIONS[name] for name in renditions if name in IMAGE_RENDITIONS
    }

    data = {
        "id": image.pk,
        "title": image.title,
        "alt": getattr(image, "default_alt_text", image.title),
        "caption": getattr(image, "caption", ""),
        "credit": getattr(image, "credit", ""),
        "width": image.width,
        "height": image.height,
        "url": absolute_url(image.file.url),
        "focal_point": _focal_point(image),
        "renditions": {},
    }

    for name, spec in specs.items():
        try:
            rendition = image.get_rendition(spec)
        except Exception:  # pragma: no cover — a broken source file must not 500 the API
            continue
        data["renditions"][name] = {
            "url": absolute_url(rendition.url),
            "width": rendition.width,
            "height": rendition.height,
        }

    # Convenience: the rendition most templates want, already flattened.
    default = data["renditions"].get("card") or data["renditions"].get("wide")
    data["src"] = default["url"] if default else data["url"]
    return data


def _focal_point(image):
    if not image.has_focal_point():
        return None
    point = image.get_focal_point()
    return {
        "x": point.x,
        "y": point.y,
        "width": point.width,
        "height": point.height,
        # CSS object-position friendly percentages
        "left_pct": round(point.x / image.width * 100, 2) if image.width else 50,
        "top_pct": round(point.y / image.height * 100, 2) if image.height else 50,
    }


def serialize_video(video):
    if video is None:
        return None
    return {
        "id": video.pk,
        "title": video.title,
        "source": video.source,
        "url": absolute_url(video.url),
        "caption": video.caption,
        "poster": serialize_image(video.poster, ["card", "wide"]),
        "autoplay": video.autoplay,
        "loop": video.loop,
        "muted": video.muted,
        "controls": video.show_controls,
    }


def serialize_document(document):
    if document is None:
        return None
    return {
        "id": document.pk,
        "title": document.title,
        "url": absolute_url(document.url),
        "filename": document.filename,
        "file_size": document.get_file_size(),
    }


def serialize_page_ref(page):
    """A lightweight page reference — enough for the frontend to build a link."""
    if page is None:
        return None
    return {
        "id": page.pk,
        "title": page.title,
        "slug": page.slug,
        "type": page.specific_class._meta.label_lower if page.specific_class else None,
        "url": page.get_url() or f"/{page.slug}/",
        "full_url": page.get_full_url(),
    }
