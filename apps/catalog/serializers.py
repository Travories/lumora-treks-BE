"""Dict serializers for catalog snippets, shared by blocks and REST endpoints."""

from apps.core.serializers import serialize_image


def serialize_destination(destination, detail=False):
    if destination is None:
        return None
    data = {
        "id": destination.pk,
        "slug": destination.slug,
        "title": destination.title,
        "subtitle": destination.subtitle,
        "image": serialize_image(destination.image),
        "region": destination.region,
        "layout": destination.default_layout,
        "href": destination.href,
        "is_featured": destination.is_featured,
    }
    if detail:
        data.update(
            {
                "description": destination.description,
                "best_season": destination.best_season,
                "packages": [
                    serialize_package(package)
                    for package in destination.packages.filter(is_active=True)
                ],
            }
        )
    return data


def serialize_package(package, detail=False):
    """
    Card-level payload matches the frontend `TravelPackage` type
    (id / title / image / rating / duration / peopleCount / price).
    """
    if package is None:
        return None
    data = {
        "id": package.pk,
        "slug": package.slug,
        "title": package.title,
        "category": package.category,
        "summary": package.summary,
        "image": serialize_image(package.image),
        "rating": float(package.rating),
        "review_count": package.review_count,
        "duration": package.duration,
        "duration_days": package.duration_days,
        "people_count": package.people_count,
        "price": float(package.price),
        "discount_price": float(package.discount_price) if package.discount_price is not None else None,
        "currency": package.currency,
        "difficulty": package.difficulty,
        "is_popular": package.is_popular,
        "source": package.source,
        "external_id": package.external_id,
        "booking_url": package.booking_url,
        "href": f"/packages/{package.slug}",
    }
    if detail:
        data.update(
            {
                "description": package.description,
                "destination": serialize_destination(package.destination),
                "highlights": [
                    {"text": item.text, "icon": item.icon} for item in package.highlights.all()
                ],
                "itinerary": [
                    {
                        "day_label": day.day_label or f"Day {index}",
                        "title": day.title,
                        "description": day.description,
                        "image": serialize_image(day.image, ["card"]),
                    }
                    for index, day in enumerate(package.itinerary.all(), start=1)
                ],
                "gallery": [
                    {"image": serialize_image(item.image), "caption": item.caption}
                    for item in package.gallery.all()
                ],
                "includes": package.includes_list,
                "excludes": package.excludes_list,
                "testimonials": [
                    serialize_testimonial(testimonial) for testimonial in package.testimonials.all()
                ],
            }
        )
    return data


def serialize_testimonial(testimonial):
    if testimonial is None:
        return None
    return {
        "id": testimonial.pk,
        "quote": testimonial.quote,
        "author_name": testimonial.author_name,
        "author_role": testimonial.author_role,
        "avatar": serialize_image(testimonial.avatar, ["thumb", "square"]),
        "rating": testimonial.rating,
        "package": testimonial.package.title if testimonial.package_id else None,
        "is_featured": testimonial.is_featured,
    }
