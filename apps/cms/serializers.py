"""Dict serializers for CMS page types exposed through custom REST endpoints."""

from apps.core.serializers import serialize_image


def serialize_blog_post(page, detail=False):
    """Card-level payload matching the frontend `BlogPostData` type.

    `detail=True` additionally emits the prose `article_body` (heading /
    paragraph / quote / image blocks) and SEO metadata for the article page.
    """
    if page is None:
        return None

    published = page.published_date or (
        page.last_published_at.date() if page.last_published_at else None
    )

    data = {
        "id": page.pk,
        "slug": page.slug,
        "title": page.title,
        "excerpt": page.excerpt or "",
        "image": serialize_image(page.hero_image),
        "category": page.category or "",
        "author": {
            "name": page.author_name or "",
            "avatar": serialize_image(page.author_avatar),
            "role": page.author_role or "",
        },
        "date": published.isoformat() if published else None,
        "read_time_minutes": page.read_time_minutes,
        "featured": page.featured,
        "href": f"/blog/{page.slug}",
    }

    if detail:
        data["body"] = page.article_body.stream_block.get_api_representation(page.article_body)
        data["seo"] = page.seo

    return data
