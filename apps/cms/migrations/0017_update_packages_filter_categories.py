"""Refresh the /packages filter tabs to the current category list.

The `package_listing` block on the Packages index page stores its own
`categories` list (the filter tabs), which overrides the frontend default.
Environments seeded before the category list grew still show the old three
tabs. Re-seeding without --reset won't fix this (the page body already
exists, so the seed skips it), so we rewrite the stored list here.

Idempotent: only touches `package_listing` blocks whose `categories` differ
from the target list. Mirrors the list in `seed_lumora`.
"""

from django.db import migrations


PACKAGE_CATEGORIES = [
    "Trekking",
    "Trail Run",
    "Hiking",
    "Day Excursions",
    "Religious Tour",
    "Nepal's Wild Life",
    "6000m Peak Climbing",
    "Sightseeing",
    "Paragliding",
]


def update_packages_filter_categories(apps, schema_editor):
    PackageIndexPage = apps.get_model("cms", "PackageIndexPage")
    field = PackageIndexPage._meta.get_field("body")

    for page in PackageIndexPage.objects.all():
        raw = list(page.body.raw_data)
        changed = False
        for block in raw:
            if block.get("type") != "package_listing":
                continue
            value = block.setdefault("value", {})
            if value.get("categories") != PACKAGE_CATEGORIES:
                value["categories"] = list(PACKAGE_CATEGORIES)
                changed = True
        if changed:
            page.body = field.stream_block.to_python(raw)
            page.save(update_fields=["body"])


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0016_alter_blogpostpage_body"),
    ]

    operations = [
        migrations.RunPython(
            update_packages_filter_categories, migrations.RunPython.noop
        ),
    ]
