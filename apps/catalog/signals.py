"""Keep a live public page in sync with each catalog package.

When a Package is created, its customer-facing page must exist at
`/packages/<slug>/<public_code>` before it can render on the site. That URL maps
to a `PackageFolderPage` (slug = package slug) holding a `PackageDetailPage`
(slug = package public_code) whose body is a single `package_detail` block.

Rather than require an editor to hand-build that page tree (or re-run a seed
command), this handler creates and publishes it automatically on first save.
The tree-building mirrors `apps/cms/management/commands/seed_lumora.py`.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.catalog.models import Package

logger = logging.getLogger(__name__)


def _default_block_settings():
    return {
        "anchor_id": "",
        "background": "default",
        "spacing": "md",
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

    folder = (
        index.get_children().type(PackageFolderPage).filter(slug=package.slug).first()
    )
    if folder is None:
        folder = PackageFolderPage(title=package.title, slug=package.slug)
        index.add_child(instance=folder)
    else:
        folder = folder.specific

    detail = PackageDetailPage(
        title=package.title,
        slug=package.public_code,
        package=package,
        body=[
            {
                "type": "package_detail",
                "value": {
                    "package": package.pk,
                    "reserve_href": f"/enquiry?package={package.slug}",
                    "settings": _default_block_settings(),
                },
            }
        ],
    )
    folder.add_child(instance=detail)
    detail.save_revision().publish()


@receiver(post_save, sender=Package, dispatch_uid="catalog_package_autocreate_detail_page")
def create_package_detail_page(sender, instance, created, **kwargs):
    if not created:
        return
    # Defer until the package's own transaction commits: guarantees the row
    # (and its generated public_code) is persisted, and avoids orphan pages if
    # the save is rolled back.
    transaction.on_commit(lambda: _ensure_detail_page(instance))
