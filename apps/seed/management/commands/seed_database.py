"""
Wipe the database and seed it with Lumora's content (apps/seed/data).

    python manage.py seed_database                # asks for confirmation
    python manage.py seed_database --noinput      # CI / scripts
    python manage.py seed_database --if-enabled   # container start: only when SEED_DATABASE=true
    python manage.py seed_database --force        # re-seed even if this seed is already applied

Re-running is idempotent: when the database already holds a seed of the same
content (same fingerprint), nothing is deleted or re-created.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from apps.seed.pipeline import SeedError, applied_fingerprint, content_fingerprint, seed_database


class Command(BaseCommand):
    help = "Delete ALL data and seed a clean database with Lumora's content (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--if-enabled",
            action="store_true",
            help="Do nothing unless the SEED_DATABASE setting is true (used by the container entrypoint).",
        )
        parser.add_argument("--force", action="store_true", help="Re-seed even if this seed is already applied.")
        parser.add_argument("--noinput", "--no-input", action="store_false", dest="interactive")

    def handle(self, *args, if_enabled, force, interactive, **options):
        if if_enabled and not settings.SEED_DATABASE:
            self.stdout.write("SEED_DATABASE is off — leaving the database as it is.")
            return

        if not force and applied_fingerprint() == content_fingerprint():
            self.stdout.write("This seed is already applied — nothing to do.")
            return

        if interactive:
            name = connection.settings_dict.get("NAME")
            answer = input(
                f"This deletes ALL data (including users and uploaded media) in {name!r} and re-seeds it.\n"
                "Type 'yes' to continue: "
            )
            if answer.strip().lower() != "yes":
                raise CommandError("Seeding cancelled.")

        try:
            seeded = seed_database(force=force, log=self.stdout.write)
        except SeedError as exc:
            raise CommandError(f"Seeding failed: {exc}") from exc
        if seeded:
            self.stdout.write(self.style.SUCCESS("Database seeded."))
