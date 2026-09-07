from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "apps.catalog"
    label = "catalog"
    verbose_name = "Catalog (packages, destinations, testimonials)"

    def ready(self):
        from apps.catalog import signals  # noqa: F401
