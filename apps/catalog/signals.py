"""Keep a live public page in sync with each catalog package.

When a Package is created, its customer-facing page must exist at
`/packages/<slug>/<public_code>` before it can render on the site. That URL maps
to a `PackageFolderPage` (slug = package slug) holding a `PackageDetailPage`
(slug = package public_code) whose body starts with five focused package sections.

Rather than require an editor to hand-build that page tree (or re-run a seed
command), this handler creates and publishes it automatically on save. It runs
on every save (create-if-missing) so it self-heals a package that never got a
page. `seed_database` uses the same function for seeded packages.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.catalog.models import Destination, Package, Testimonial

logger = logging.getLogger(__name__)


def _default_block_settings(anchor_id):
    return {
        "anchor_id": anchor_id,
        "background": "default",
        "spacing": "none",
        "container": "default",
        "hidden": False,
    }


def ensure_detail_page(package):
    """Create and publish the package's public page if it doesn't exist yet."""

    # Imported lazily: the cms app depends on catalog, so importing its page
    # models at module load time would create a circular import.
    from apps.cms.models import PackageDetailPage, PackageFolderPage, PackageIndexPage

    # Already has a linked detail page — keep its URL and title in step with
    # the package (idempotent on re-save).
    detail = PackageDetailPage.objects.filter(package=package).first()
    if detail is not None:
        sync_detail_page(package, detail)
        return

    index = PackageIndexPage.objects.filter(slug="packages").first()
    if index is None:
        logger.warning(
            "No PackageIndexPage (slug='packages') found; skipping auto-creation "
            "of the detail page for package %r. Run seed_database or create the "
            "packages index page.",
            package.slug,
        )
        return

    # A page may already occupy `/packages/<slug>/` — e.g. a StandardPage the
    # seed command builds for the same catalogue URL. Wagtail enforces unique
    # slugs per parent regardless of page type, so don't try to add a second
    # one: the URL already resolves, so there's nothing to self-heal here.
    existing = index.get_children().filter(slug=package.slug).first()
    if existing is not None and existing.specific_class is not PackageFolderPage:
        logger.info(
            "Slug %r under the packages index is already used by a %s; skipping "
            "auto-creation of the package folder/detail page.",
            package.slug,
            existing.specific_class.__name__ if existing.specific_class else "page",
        )
        return

    folder = existing.specific if existing is not None else None
    if folder is None:
        folder = PackageFolderPage(title=package.title, slug=package.slug)
        index.add_child(instance=folder)

    # Same guard one level down for the detail page's slug (public_code).
    if folder.get_children().filter(slug=package.public_code).exists():
        return

    detail = PackageDetailPage(
        title=package.title,
        slug=package.public_code,
        package=package,
        body=[
            {
                "type": "package_header",
                "value": {"settings": _default_block_settings("package-header")},
            },
            {
                "type": "package_overview",
                "value": {"settings": _default_block_settings("package-overview")},
            },
            {
                "type": "package_booking",
                "value": {
                    "reserve_href": f"/enquiry?package={package.slug}",
                    "settings": _default_block_settings("package-booking"),
                },
            },
            {
                "type": "package_itinerary",
                "value": {"settings": _default_block_settings("package-itinerary")},
            },
            {
                "type": "package_reviews",
                "value": {"settings": _default_block_settings("package-reviews")},
            },
        ],
    )
    folder.add_child(instance=detail)
    detail.save_revision().publish()


def sync_detail_page(package, detail):
    """Follow slug / title edits so `package.public_url` keeps resolving.

    The folder page's slug is the `/packages/<slug>/` URL segment; Wagtail
    rewrites the detail page's url_path when the folder's slug changes. Titles
    are updated in place (no new revision) so an editor's unpublished draft of
    the page's sections is left alone.
    """

    from apps.cms.models import PackageFolderPage

    folder = detail.get_parent().specific
    if isinstance(folder, PackageFolderPage) and (
        folder.slug != package.slug or folder.title != package.title
    ):
        if folder.slug != package.slug and folder.get_siblings(inclusive=False).filter(slug=package.slug).exists():
            logger.warning(
                "Cannot move package %r to /packages/%s/: another page already uses that slug.",
                package.pk,
                package.slug,
            )
        else:
            folder.slug = package.slug
            folder.title = folder.draft_title = package.title
            folder.save()

    if detail.title != package.title:
        type(detail).objects.filter(pk=detail.pk).update(title=package.title, draft_title=package.title)


def ensure_destination_page(destination):
    """Create and publish a destination's public page if it doesn't exist yet."""

    from apps.cms.models import DestinationDetailPage, DestinationIndexPage

    page = DestinationDetailPage.objects.filter(destination=destination).first()
    if page is not None:
        if page.slug != destination.slug and not page.get_siblings(inclusive=False).filter(slug=destination.slug).exists():
            page.slug = destination.slug
            page.save()
        if page.title != destination.title:
            DestinationDetailPage.objects.filter(pk=page.pk).update(
                title=destination.title, draft_title=destination.title
            )
        return

    index = DestinationIndexPage.objects.filter(slug="destinations").first()
    if index is None:
        logger.warning(
            "No DestinationIndexPage (slug='destinations') found; skipping auto-creation "
            "of the page for destination %r.",
            destination.slug,
        )
        return
    if index.get_children().filter(slug=destination.slug).exists():
        return

    page = DestinationDetailPage(
        title=destination.title,
        slug=destination.slug,
        destination=destination,
        body=[
            {
                "type": "destination_header",
                "value": {"settings": _default_block_settings("destination-header")},
            },
            {
                "type": "destination_overview",
                "value": {"settings": _default_block_settings("destination-overview")},
            },
            {
                "type": "destination_packages",
                "value": {"settings": _default_block_settings("destination-packages")},
            },
        ],
    )
    index.add_child(instance=page)
    page.save_revision().publish()


def _ensure_destination_page_safe(destination):
    try:
        ensure_destination_page(destination)
    except Exception:  # pragma: no cover — defensive: log, don't propagate
        logger.exception(
            "Failed to auto-create the page for destination %r; the destination "
            "was saved. Create/repair its page in Wagtail if needed.",
            getattr(destination, "slug", destination.pk),
        )


@receiver(post_save, sender=Destination, dispatch_uid="catalog_destination_autocreate_page")
def create_destination_page(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    transaction.on_commit(lambda: _ensure_destination_page_safe(instance))


def _ensure_detail_page_safe(package):
    """Never let auto-creation of the public page break a Package save."""
    try:
        ensure_detail_page(package)
    except Exception:  # pragma: no cover — defensive: log, don't propagate
        logger.exception(
            "Failed to auto-create the detail page for package %r; the package "
            "was saved. Create/repair its page in Wagtail if needed.",
            getattr(package, "slug", package.pk),
        )


@receiver(post_save, sender=Package, dispatch_uid="catalog_package_autocreate_detail_page")
def create_package_detail_page(sender, instance, created, **kwargs):
    # Runs on every save, not just creation: `ensure_detail_page` is a cheap
    # no-op once the page exists, so this self-heals a package whose page was
    # never created (e.g. saved before the packages index existed, or a
    # transient failure during the original create).
    #
    # Defer until the package's own transaction commits: guarantees the row
    # (and its generated public_code) is persisted, and avoids orphan pages if
    # the save is rolled back.
    transaction.on_commit(lambda: _ensure_detail_page_safe(instance))


# --------------------------------------------------------------- testimonials
# Testimonials count towards a package's rating and review count (see
# apps/catalog/ratings.py), so keep the stored aggregate current when editors
# add, edit, move or delete one.


@receiver(pre_save, sender=Testimonial, dispatch_uid="catalog_testimonial_remember_package")
def remember_testimonial_package(sender, instance, **kwargs):
    instance._previous_package_id = (
        Testimonial.objects.filter(pk=instance.pk).values_list("package_id", flat=True).first()
        if instance.pk
        else None
    )


def _recalculate_ratings(package_ids):
    from apps.catalog.ratings import recalculate_package_rating

    for package in Package.objects.filter(pk__in=[pk for pk in package_ids if pk]):
        recalculate_package_rating(package)


@receiver(post_save, sender=Testimonial, dispatch_uid="catalog_testimonial_update_rating")
@receiver(post_delete, sender=Testimonial, dispatch_uid="catalog_testimonial_delete_rating")
def update_testimonial_package_rating(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    package_ids = {instance.package_id, getattr(instance, "_previous_package_id", None)}
    transaction.on_commit(lambda: _recalculate_ratings(package_ids))
