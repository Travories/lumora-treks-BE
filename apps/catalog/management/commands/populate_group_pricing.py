"""Populate sensible whole-number group prices for packages without tiers."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Package, PackageGroupPrice
from apps.catalog.pricing import default_group_prices


class Command(BaseCommand):
    help = "Add default 0%, 10%, 15% and 20% group-price tiers to packages that have none."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Create the missing tiers.")

    def handle(self, *args, **options):
        packages = list(Package.objects.filter(group_pricing__isnull=True).order_by("pk"))
        for package in packages:
            prices = [tier["price_per_person"] for tier in default_group_prices(package.price)]
            self.stdout.write(f"{package.pk}: {package.title} -> {prices}")

        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to populate."))
            return

        with transaction.atomic():
            PackageGroupPrice.objects.bulk_create(
                PackageGroupPrice(package=package, **tier)
                for package in packages
                for tier in default_group_prices(package.price)
            )

        self.stdout.write(self.style.SUCCESS(f"Populated group pricing for {len(packages)} packages."))
