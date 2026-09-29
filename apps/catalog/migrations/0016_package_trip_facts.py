"""
Trip facts on packages (max altitude, accommodation, meals, transport) and
required editorial fields (summary, description, difficulty, itinerary day
descriptions).

Existing packages get empty facts; editors are asked for them the next time
the package is saved. A blank difficulty becomes "moderate".
"""

import wagtail.fields
from django.db import migrations, models


def fill_blank_difficulty(apps, schema_editor):
    apps.get_model("catalog", "Package").objects.filter(difficulty="").update(difficulty="moderate")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0015_remove_legacy_link_and_inclusion_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="max_altitude",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="Highest point of the trip in metres, e.g. 4130. Leave empty for low-altitude tours.",
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="accommodation",
            field=models.CharField(
                default="",
                max_length=200,
                help_text='Where travellers sleep, e.g. "Mountain teahouses (twin share)".',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="package",
            name="meals",
            field=models.CharField(
                default="", max_length=200, help_text='Which meals are covered, e.g. "Daily breakfast".'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="package",
            name="transport",
            field=models.CharField(
                default="",
                max_length=200,
                help_text='How travellers get around, e.g. "Private jeep to the trailhead".',
            ),
            preserve_default=False,
        ),
        migrations.RunPython(fill_blank_difficulty, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="package",
            name="difficulty",
            field=models.CharField(
                choices=[
                    ("easy", "Easy"),
                    ("moderate", "Moderate"),
                    ("challenging", "Challenging"),
                    ("strenuous", "Strenuous"),
                ],
                default="moderate",
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name="package",
            name="summary",
            field=models.TextField(help_text="One or two sentences shown on package cards."),
        ),
        migrations.AlterField(
            model_name="package",
            name="description",
            field=wagtail.fields.RichTextField(help_text="The Overview on the package page."),
        ),
        migrations.AlterField(
            model_name="packageitineraryday",
            name="description",
            field=models.TextField(help_text="What happens this day — shown under the day's title."),
        ),
        migrations.AlterField(
            model_name="packageitineraryday",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="+",
                to="core.customimage",
                help_text="Optional photo shown beside this day.",
            ),
        ),
    ]
