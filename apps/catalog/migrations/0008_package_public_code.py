import secrets
import string

from django.db import migrations, models


def assign_public_codes(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    alphabet = string.ascii_lowercase + string.digits
    assigned = set(Package.objects.exclude(public_code__isnull=True).values_list("public_code", flat=True))
    for package in Package.objects.filter(public_code__isnull=True).iterator():
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(5))
            if code not in assigned:
                package.public_code = code
                package.save(update_fields=["public_code"])
                assigned.add(code)
                break


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_travelerreview")]

    operations = [
        migrations.AddField(
            model_name="package",
            name="public_code",
            field=models.CharField(blank=True, max_length=5, null=True, unique=True),
        ),
        migrations.RunPython(assign_public_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="package",
            name="public_code",
            field=models.CharField(editable=False, help_text="Stable public package reference used in customer-facing URLs.", max_length=5, unique=True),
        ),
    ]
