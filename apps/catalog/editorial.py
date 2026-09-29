"""
Cross-links between catalog snippets and their public Wagtail pages.

Every Package and Destination has two halves an editor works with:

* the snippet (Packages / Destinations in the sidebar) holds the data —
  price, itinerary, gallery, inclusions, region, highlights;
* the auto-created detail page (Pages) holds the screen layout and SEO.

These helpers feed `apps.core.panels.RelatedLinksPanel` so each half links to
the other, plus the related listings (packages in a destination, enquiries
and testimonials for a package).
"""

from django.urls import reverse
from django.utils.http import urlencode
from wagtail.admin.admin_url_finder import AdminURLFinder

from apps.core.panels import RelatedAction, RelatedItem


def _edit_url(obj, request):
    return AdminURLFinder(request.user).get_edit_url(obj) if obj is not None else None


def _listing_url(model, request, **filters):
    viewset = getattr(model, "snippet_viewset", None)
    if viewset is None or not viewset.permission_policy.user_has_any_permission(
        request.user, {"add", "change", "delete", "view"}
    ):
        return None
    url = reverse(viewset.get_url_name("list"))
    return f"{url}?{urlencode(filters)}" if filters else url


def detail_page_for(obj):
    """The auto-created public page for a Package / Destination, if any."""
    try:
        return obj.detail_page
    except obj.__class__.detail_page.RelatedObjectDoesNotExist:
        return None


def _public_page_item(page, request, *, hidden_reason="", missing_text):
    if page is None:
        return RelatedItem("Public page", missing_text)

    actions = []
    page_edit_url = _edit_url(page, request)
    if page_edit_url:
        actions.append(RelatedAction("Edit page sections & SEO", page_edit_url))
    if page.live and not hidden_reason:
        actions.append(RelatedAction("View on site", page.full_url, icon="link-external", external=True))

    description = page.url or ""
    if hidden_reason:
        description = f"{description} — {hidden_reason}"
    elif not page.live:
        description = f"{description} — page is not published"
    return RelatedItem("Public page", description, actions)


def package_related_items(package, request):
    if package is None or not package.pk:
        return [
            RelatedItem(
                "Public page",
                "Created and published automatically when you first save this package.",
            )
        ]

    from apps.catalog.models import Testimonial
    from apps.leads.models import LeadSubmission

    items = [
        _public_page_item(
            detail_page_for(package),
            request,
            hidden_reason="" if package.is_active else "hidden because the package is not active",
            missing_text="Not created yet. Save the package again to create it.",
        )
    ]

    if package.destination_id:
        destination_url = _edit_url(package.destination, request)
        items.append(
            RelatedItem(
                "Destination",
                package.destination.title,
                [RelatedAction("Edit destination", destination_url)] if destination_url else [],
            )
        )

    leads = LeadSubmission.objects.filter(package=package)
    leads_url = _listing_url(LeadSubmission, request, package=package.pk)
    if leads_url:
        new_count = leads.filter(status="new").count()
        items.append(
            RelatedItem(
                "Enquiries",
                f"{leads.count()} total, {new_count} new",
                [RelatedAction("View enquiries", leads_url, icon="mail")],
            )
        )

    testimonials_url = _listing_url(Testimonial, request, package=package.pk)
    if testimonials_url:
        items.append(
            RelatedItem(
                "Testimonials",
                f"{package.testimonials.count()} linked to this package",
                [RelatedAction("View testimonials", testimonials_url, icon="openquote")],
            )
        )
    return items


def destination_related_items(destination, request):
    if destination is None or not destination.pk:
        return []

    from apps.catalog.models import Package

    items = [
        _public_page_item(
            detail_page_for(destination),
            request,
            missing_text="No destination page. Create one under Pages › Destinations if it should be public.",
        )
    ]
    packages_url = _listing_url(Package, request, destination=destination.pk)
    if packages_url:
        items.append(
            RelatedItem(
                "Packages",
                f"{destination.packages.count()} in this destination",
                [RelatedAction("View packages", packages_url, icon="tag")],
            )
        )
    return items


def package_page_related_items(page, request):
    """Shown on a package detail page: the page layout lives here, the data doesn't."""

    package = getattr(page, "package", None) if page.package_id else None
    if package is None:
        return []
    edit_url = _edit_url(package, request)
    return [
        RelatedItem(
            "Package details",
            "Price, itinerary, gallery, inclusions and highlights are edited on the package.",
            [RelatedAction(f"Edit “{package.title}”", edit_url, icon="tag")] if edit_url else [],
        )
    ]


def destination_page_related_items(page, request):
    destination = getattr(page, "destination", None) if page.destination_id else None
    if destination is None:
        return []
    edit_url = _edit_url(destination, request)
    items = [
        RelatedItem(
            "Destination details",
            "Title, image, region, season and highlights are edited on the destination.",
            [RelatedAction(f"Edit “{destination.title}”", edit_url, icon="globe")] if edit_url else [],
        )
    ]
    from apps.catalog.models import Package

    packages_url = _listing_url(Package, request, destination=destination.pk)
    if packages_url:
        items.append(
            RelatedItem(
                "Packages",
                f"{destination.packages.count()} in this destination",
                [RelatedAction("View packages", packages_url, icon="tag")],
            )
        )
    return items
