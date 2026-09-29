"""
Accommodation, meals and transport move from the package to each itinerary
day, where travellers actually need them.

Existing values are copied onto every day of their package (editors can then
refine them per day) before the package-level fields are removed. Reversing
copies the first day's values back to the package.
"""

from django.db import migrations

import apps.core.fields

FACTS = ("accommodation", "meals", "transport")


def copy_package_facts_to_days(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    PackageItineraryDay = apps.get_model("catalog", "PackageItineraryDay")
    for package in Package.objects.all().iterator():
        values = {fact: getattr(package, fact) for fact in FACTS if getattr(package, fact)}
        if values:
            PackageItineraryDay.objects.filter(package=package).update(**values)


def copy_first_day_facts_to_package(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    for package in Package.objects.all().iterator():
        first_day = package.itinerary.order_by("sort_order").first()
        if first_day:
            for fact in FACTS:
                setattr(package, fact, getattr(first_day, fact))
            package.save(update_fields=list(FACTS))


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0017_editorial_character_limits"),
    ]

    operations = [
        migrations.AddField(
            model_name="packageitineraryday",
            name="accommodation",
            field=apps.core.fields.LimitedCharField(
                blank=True,
                help_text='Where travellers sleep, e.g. "Teahouse in Ghandruk".',
                max_length=200,
                ui_max_length=35,
            ),
        ),
        migrations.AddField(
            model_name="packageitineraryday",
            name="meals",
            field=apps.core.fields.LimitedCharField(
                blank=True, help_text='Meals included this day, e.g. "Breakfast".', max_length=200, ui_max_length=30
            ),
        ),
        migrations.AddField(
            model_name="packageitineraryday",
            name="transport",
            field=apps.core.fields.LimitedCharField(
                blank=True, help_text='How travellers get around, e.g. "On foot".', max_length=200, ui_max_length=50
            ),
        ),
        migrations.RunPython(copy_package_facts_to_days, copy_first_day_facts_to_package),
        # A default lets the reverse migration re-add the columns over existing rows.
        *[
            migrations.AlterField(
                model_name="package",
                name=fact,
                field=apps.core.fields.LimitedCharField(default="", max_length=200),
            )
            for fact in FACTS
        ],
        migrations.RemoveField(model_name="package", name="accommodation"),
        migrations.RemoveField(model_name="package", name="meals"),
        migrations.RemoveField(model_name="package", name="transport"),
    ]
