"""Backfill default group-pricing tiers for packages that have none.

Packages created before group pricing existed (or on environments seeded
before it) have no `PackageGroupPrice` rows, so `package_data.group_pricing`
serializes empty and the frontend booking card can't offer per-group prices.

This data migration adds the same default tiers `seed_lumora` writes (see
`apps.catalog.pricing.default_group_prices`), but only for packages missing
them — so it's idempotent and never overwrites hand-edited pricing. The band
table is inlined to keep the migration self-contained.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


# Mirror of apps.catalog.pricing.GROUP_PRICE_BANDS at the time of writing.
GROUP_PRICE_BANDS = (
    (1, 1, Decimal("1.00")),
    (2, 3, Decimal("0.90")),
    (4, 7, Decimal("0.85")),
    (8, None, Decimal("0.80")),
)


def _default_tiers(base_price):
    price = Decimal(str(base_price))
    return [
        {
            "min_people": minimum,
            "max_people": maximum,
            "price_per_person": int(
                (price * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            ),
            "sort_order": order,
        }
        for order, (minimum, maximum, multiplier) in enumerate(GROUP_PRICE_BANDS, start=1)
    ]


def populate_group_pricing(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    PackageGroupPrice = apps.get_model("catalog", "PackageGroupPrice")

    for package in Package.objects.all():
        if PackageGroupPrice.objects.filter(package=package).exists():
            continue  # already priced — leave editor content untouched
        PackageGroupPrice.objects.bulk_create(
            PackageGroupPrice(package=package, **tier)
            for tier in _default_tiers(package.price)
        )


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0012_alter_packagegroupprice_price_per_person"),
    ]

    operations = [
        migrations.RunPython(populate_group_pricing, migrations.RunPython.noop),
    ]
