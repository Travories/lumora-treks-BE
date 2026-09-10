"""
Seed just the Blog: a BlogIndexPage under Home plus sample BlogPostPages.

Kept separate from `seed_lumora` so the blog can be (re)seeded on its own
without touching the package/destination catalogue.

    python manage.py seed_blog           # create (skips existing posts)
    python manage.py seed_blog --reset   # rebuild the index body + every post
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cms.management.commands.seed_lumora import Command as SeedCommand
from apps.cms.models import HomePage


class Command(BaseCommand):
    help = "Populate the CMS Blog (index page + sample posts)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Rebuild the blog index body and every sample post.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        home = HomePage.objects.first()
        if home is None:
            self.stderr.write(self.style.ERROR("No Home page found — run `seed_lumora` first."))
            return

        # Reuse the image import + blog builders from the main seeder.
        seeder = SeedCommand()
        seeder.stdout = self.stdout
        seeder.style = self.style
        seeder.reset = options["reset"]
        seeder.images = {}
        seeder.import_images()
        seeder.create_blog(home)

        self.stdout.write(self.style.SUCCESS("Seeded Blog index + posts."))
        self.stdout.write("Blog API: http://localhost:8000/api/v2/blog/")
