from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("leads", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="leadsubmission",
            name="consent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leadsubmission",
            name="consent_given",
            field=models.BooleanField(default=False),
        ),
    ]
