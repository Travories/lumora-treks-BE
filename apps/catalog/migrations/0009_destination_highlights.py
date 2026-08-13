# Generated manually for the CMS destination-content field.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_package_public_code")]

    operations = [
        migrations.AddField(
            model_name="destination",
            name="highlights",
            field=models.TextField(blank=True, help_text="One destination highlight per line."),
        ),
    ]
