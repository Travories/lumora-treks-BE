"""Package rating aggregates shared by the reviews API and the seed pipeline."""

from django.db.models import Count, Sum

from apps.catalog.models import PackageRatingSummary


def package_rating_values(package):
    """Review totals for a package across traveler reviews and testimonials."""

    traveler = package.traveler_reviews.aggregate(total=Count("id"), total_rating=Sum("rating"))
    testimonials = package.testimonials.aggregate(total=Count("id"), total_rating=Sum("rating"))
    total = (traveler["total"] or 0) + (testimonials["total"] or 0)
    rating_sum = (traveler["total_rating"] or 0) + (testimonials["total_rating"] or 0)
    distribution = {
        rating: package.traveler_reviews.filter(rating=rating).count()
        + package.testimonials.filter(rating=rating).count()
        for rating in range(1, 6)
    }
    return {
        "total_reviews": total,
        "rating_sum": rating_sum,
        "average_rating": round(rating_sum / total, 1) if total else 0,
        "one_star": distribution[1],
        "two_star": distribution[2],
        "three_star": distribution[3],
        "four_star": distribution[4],
        "five_star": distribution[5],
    }


def recalculate_package_rating(package):
    """Keep package cards and rating breakdowns correct after review changes."""

    values = package_rating_values(package)
    PackageRatingSummary.objects.update_or_create(
        package=package,
        defaults=values,
    )
    package.rating = values["average_rating"]
    package.review_count = values["total_reviews"]
    package.save(update_fields=["rating", "review_count"])
