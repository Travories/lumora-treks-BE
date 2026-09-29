from django.apps import AppConfig


class SeedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seed"
    label = "seed"
    verbose_name = "Seed data"
