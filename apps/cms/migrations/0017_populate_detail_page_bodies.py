"""Populate empty `body` StreamFields on destination/package detail pages.

Detail pages created before the body-seeding logic (see `seed_lumora`) were
published with their catalog data but an EMPTY `body`. The frontend detail
routes call `notFound()` whenever `body` is empty
(`src/app/destinations/[slug]/page.tsx`, `.../packages/[slug]/[code]/page.tsx`),
so every individual destination/package rendered "Page not found".

This data migration writes the same section blocks `seed_lumora` would, but
only for pages whose `body` is still empty — so it's idempotent and never
disturbs pages an editor has already filled in. It mirrors the block payloads
in `apps/cms/management/commands/seed_lumora.py`.
"""

import uuid

from django.db import migrations


def _settings(anchor_id=""):
    """Mirror seed_lumora.Command.settings(anchor_id, spacing="none")."""
    return {
        "anchor_id": anchor_id,
        "background": "default",
        "spacing": "none",
        "container": "default",
        "hidden": False,
    }


def _block(block_type, value):
    return {"type": block_type, "value": value, "id": str(uuid.uuid4())}


def _destination_body():
    return [
        _block("destination_header", {"settings": _settings("destination-header")}),
        _block("destination_overview", {"settings": _settings("destination-overview")}),
        _block("destination_packages", {"settings": _settings("destination-packages")}),
    ]


def _package_body(package_slug):
    return [
        _block("package_header", {"settings": _settings("package-header")}),
        _block("package_overview", {"settings": _settings("package-overview")}),
        _block(
            "package_booking",
            {
                "reserve_href": f"/enquiry?package={package_slug}",
                "settings": _settings("package-booking"),
            },
        ),
        _block("package_itinerary", {"settings": _settings("package-itinerary")}),
        _block("package_reviews", {"settings": _settings("package-reviews")}),
    ]


def populate_detail_bodies(apps, schema_editor):
    DestinationDetailPage = apps.get_model("cms", "DestinationDetailPage")
    PackageDetailPage = apps.get_model("cms", "PackageDetailPage")

    dest_field = DestinationDetailPage._meta.get_field("body")
    for page in DestinationDetailPage.objects.all():
        if page.body:  # already has sections — leave editor content untouched
            continue
        page.body = dest_field.stream_block.to_python(_destination_body())
        page.save(update_fields=["body"])

    pkg_field = PackageDetailPage._meta.get_field("body")
    for page in PackageDetailPage.objects.select_related("package").all():
        if page.body:
            continue
        page.body = pkg_field.stream_block.to_python(_package_body(page.package.slug))
        page.save(update_fields=["body"])


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0016_alter_blogpostpage_body"),
    ]

    operations = [
        migrations.RunPython(populate_detail_bodies, migrations.RunPython.noop),
    ]
