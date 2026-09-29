"""
Move legacy one-per-line `Package.includes` / `excludes` text into
`PackageIncludedItem` rows — the model the admin edits and the frontend
renders — before the text columns are removed in 0015.

Only fills a kind (included / excluded) the package has no rows for, so
content already maintained as items is never duplicated or overwritten.
Reversing writes the items back into the text columns.
"""

from django.db import migrations

KINDS = (("included", "includes"), ("excluded", "excludes"))


def lines(text):
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def backfill_items(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    PackageIncludedItem = apps.get_model("catalog", "PackageIncludedItem")

    new_items = []
    for package in Package.objects.all().iterator():
        existing_kinds = set(package.included_items.values_list("kind", flat=True))
        for kind, field in KINDS:
            if kind in existing_kinds:
                continue
            new_items.extend(
                PackageIncludedItem(package=package, kind=kind, text=text[:255], sort_order=order)
                for order, text in enumerate(lines(getattr(package, field)), start=1)
            )
    PackageIncludedItem.objects.bulk_create(new_items)


def restore_text(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    for package in Package.objects.all().iterator():
        for kind, field in KINDS:
            texts = package.included_items.filter(kind=kind).order_by("sort_order").values_list("text", flat=True)
            setattr(package, field, "\n".join(texts))
        package.save(update_fields=[field for _kind, field in KINDS])


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0013_alter_package_category"),
    ]

    operations = [
        migrations.RunPython(backfill_items, restore_text),
    ]
