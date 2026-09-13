"""Keep a live public page in sync with each catalog package.

When a Package is created, its customer-facing page must exist at
`/packages/<slug>/<public_code>` before it can render on the site. That URL maps
to a `PackageFolderPage` (slug = package slug) holding a `PackageDetailPage`
(slug = package public_code) whose body starts with five focused package sections.

Rather than require an editor to hand-build that page tree (or re-run a seed
command), this handler creates and publishes it automatically on save. It runs
on every save (create-if-missing) so it self-heals a package that never got a
page. The tree-building mirrors `apps/cms/management/commands/seed_lumora.py`.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.catalog.models import Package

logger = logging.getLogger(__name__)


def _default_block_settings(anchor_id):
    return {
        "anchor_id": anchor_id,
        "background": "default",
        "spacing": "none",
        "container": "default",
        "hidden": False,
    }


def _ensure_detail_page(package):
    # Imported lazily: the cms app depends on catalog, so importing its page
    # models at module load time would create a circular import.
    from apps.cms.models import PackageDetailPage, PackageFolderPage, PackageIndexPage

    # Already has a linked detail page — nothing to do (idempotent on re-save).
    if PackageDetailPage.objects.filter(package=package).exists():
        return

    index = PackageIndexPage.objects.filter(slug="packages").first()
    if index is None:
        logger.warning(
            "No PackageIndexPage (slug='packages') found; skipping auto-creation "
            "of the detail page for package %r. Run seed_lumora or create the "
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


def _ensure_detail_page_safe(package):
    """Never let auto-creation of the public page break a Package save."""
    try:
        _ensure_detail_page(package)
    except Exception:  # pragma: no cover — defensive: log, don't propagate
        logger.exception(
            "Failed to auto-create the detail page for package %r; the package "
            "was saved. Create/repair its page in Wagtail if needed.",
            getattr(package, "slug", package.pk),
        )


@receiver(post_save, sender=Package, dispatch_uid="catalog_package_autocreate_detail_page")
def create_package_detail_page(sender, instance, created, **kwargs):
    # Runs on every save, not just creation: `_ensure_detail_page` is a cheap
    # no-op once the page exists, so this self-heals a package whose page was
    # never created (e.g. saved before the packages index existed, or a
    # transient failure during the original create).
    #
    # Defer until the package's own transaction commits: guarantees the row
    # (and its generated public_code) is persisted, and avoids orphan pages if
    # the save is rolled back.
    transaction.on_commit(lambda: _ensure_detail_page_safe(instance))
