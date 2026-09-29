"""
Clean-seed pipeline: wipe the database and rebuild it from `apps/seed/data`.

    seed_database(...)
      1. fingerprint the seed content (data + media + this file)
      2. skip if the database already holds a seed with that fingerprint
      3. delete stored media files, drop every table, run migrations
      4. in one transaction: images → destinations → packages → testimonials
         → page tree → blog → site settings → ratings, then record a SeedRun
      5. create the admin account from DJANGO_SUPERUSER_* if provided

Because step 3 always starts from an empty database, every step simply
creates records — there is no merge logic to keep in sync with the data.
"""

import hashlib
import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.images import ImageFile
from django.core.management import call_command
from django.db import connection, transaction
from wagtail import blocks
from wagtail.documents import get_document_model
from wagtail.models import Page, Site

from apps.catalog.models import (
    Destination,
    Package,
    PackageGalleryImage,
    PackageGroupPrice,
    PackageHighlight,
    PackageIncludedItem,
    PackageItineraryDay,
    Testimonial,
)
from apps.catalog.pricing import default_group_prices
from apps.catalog.ratings import recalculate_package_rating
from apps.catalog.signals import ensure_detail_page
from apps.cms.models import (
    BlogIndexPage,
    BlogPostPage,
    CheckoutPage,
    ContactPage,
    DestinationDetailPage,
    DestinationIndexPage,
    EnquiryPage,
    HomePage,
    PackageIndexPage,
    PaymentSuccessPage,
    PrivacyPage,
    StandardPage,
)
from apps.core.models import CustomImage, Video
from apps.navigation.models import (
    BrandSettings,
    FooterSettings,
    IntegrationSettings,
    NavigationSettings,
    ThemeSettings,
)
from apps.seed.data import blog, catalog, pages, site_settings
from apps.seed.data.media import IMAGES
from apps.seed.models import SeedRun

SEED_DIR = Path(__file__).resolve().parent
MEDIA_DIR = SEED_DIR / "media"
FINGERPRINT_SOURCES = ("data", "media", "pipeline.py")


class SeedError(Exception):
    pass


# --------------------------------------------------------------- fingerprint


def content_fingerprint():
    """SHA-256 over the seed data, media and pipeline — changes when the seed does."""
    digest = hashlib.sha256()
    for source in FINGERPRINT_SOURCES:
        path = SEED_DIR / source
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        for file in files:
            if "__pycache__" in file.parts:
                continue
            digest.update(file.relative_to(SEED_DIR).as_posix().encode())
            digest.update(b"\0")
            digest.update(file.read_bytes())
    return digest.hexdigest()


def applied_fingerprint():
    """Fingerprint of the seed currently in the database, if any."""
    if SeedRun._meta.db_table not in connection.introspection.table_names():
        return None
    latest = SeedRun.objects.order_by("-applied_at").first()
    return latest.fingerprint if latest else None


# --------------------------------------------------------------------- reset


def _delete_stored_media(tables, log):
    """Remove uploaded files first, so dropping the tables doesn't orphan them in storage."""
    image_model = CustomImage
    models = [image_model.get_rendition_model(), image_model, get_document_model(), Video]
    deleted = 0
    for model in models:
        if model._meta.db_table not in tables:
            continue
        storage = model._meta.get_field("file").storage
        for name in model.objects.exclude(file="").values_list("file", flat=True).iterator():
            try:
                storage.delete(name)
                deleted += 1
            except Exception as exc:  # a missing file must not block the reset
                log(f"  could not delete {name}: {exc}")
    log(f"Deleted {deleted} stored media file(s).")


def reset_database(log):
    """Drop every table (and its media files), then rebuild the schema."""
    tables = connection.introspection.table_names()
    _delete_stored_media(tables, log)
    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            if tables:
                cursor.execute(f"DROP TABLE IF EXISTS {', '.join(map(quote, tables))} CASCADE")
        elif connection.vendor == "sqlite":
            cursor.execute("PRAGMA foreign_keys = OFF")
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {quote(table)}")
            cursor.execute("PRAGMA foreign_keys = ON")
        else:
            raise SeedError(f"Database reset is not supported for {connection.vendor}.")
    log(f"Dropped {len(tables)} table(s).")
    cache.clear()
    call_command("migrate", interactive=False, verbosity=0)
    log("Migrations applied.")


# ----------------------------------------------------------- block validation


def check_stream(stream_block, raw, path):
    """Fail on block types or fields the page doesn't define (Wagtail would drop them silently)."""
    for index, item in enumerate(raw):
        child = stream_block.child_blocks.get(item["type"])
        if child is None:
            raise SeedError(f"{path}[{index}]: {item['type']!r} is not allowed here")
        _check_value(child, item["value"], f"{path}[{index}].{item['type']}")


def _check_value(block, value, path):
    if isinstance(block, blocks.StructBlock) and isinstance(value, dict):
        unknown = set(value) - set(block.child_blocks)
        if unknown:
            raise SeedError(f"{path}: unknown field(s) {', '.join(sorted(unknown))}")
        for name, child_value in value.items():
            _check_value(block.child_blocks[name], child_value, f"{path}.{name}")
    elif isinstance(block, blocks.ListBlock) and isinstance(value, list):
        for index, item in enumerate(value):
            _check_value(block.child_block, item, f"{path}[{index}]")
    elif isinstance(block, blocks.StreamBlock) and isinstance(value, list):
        check_stream(block, value, path)


# -------------------------------------------------------------------- seeding


class Seeder:
    """Builds the seed content into an empty, migrated database."""

    def __init__(self, log):
        self.log = log
        self.images = {}
        self.destinations = {}
        self.packages = {}

    # References used by the data modules ---------------------------------

    def image(self, key):
        return self._lookup(self.images, key, "image").pk

    def destination(self, slug):
        return self._lookup(self.destinations, slug, "destination").pk

    def package(self, slug):
        return self._lookup(self.packages, slug, "package").pk

    @staticmethod
    def _lookup(registry, key, kind):
        try:
            return registry[key]
        except KeyError:
            raise SeedError(f"Unknown {kind} {key!r} referenced in seed data") from None

    # Steps ---------------------------------------------------------------

    def run(self):
        self.seed_images()
        self.seed_destinations()
        self.seed_packages()
        self.seed_testimonials()
        home = self.seed_home()
        blog_index = self.seed_site_pages(home)
        self.seed_blog(blog_index)
        self.seed_settings()
        for package in self.packages.values():
            recalculate_package_rating(package)
        return {
            "images": len(self.images),
            "destinations": len(self.destinations),
            "packages": len(self.packages),
            "testimonials": Testimonial.objects.count(),
            "blog_posts": BlogPostPage.objects.count(),
            "pages": Page.objects.filter(depth__gt=1).count(),
        }

    def seed_images(self):
        for key, meta in IMAGES.items():
            path = MEDIA_DIR / f"{key}.webp"
            if not path.exists():
                raise SeedError(f"Missing seed image file {path}")
            with path.open("rb") as handle:
                image = CustomImage(title=meta["title"], alt_text=meta["alt"], credit=meta["credit"])
                image.file = ImageFile(handle, name=path.name)
                image.save()
            self.images[key] = image
        self.log(f"Images: {len(self.images)}")

    def seed_destinations(self):
        for order, data in enumerate(catalog.DESTINATIONS):
            self.destinations[data["slug"]] = Destination.objects.create(
                slug=data["slug"],
                title=data["title"],
                subtitle=data["subtitle"],
                description=data["description"],
                highlights="\n".join(data["highlights"]),
                image=self._lookup(self.images, data["image"], "image"),
                region=data["region"],
                best_season=data["best_season"],
                default_layout=data["layout"],
                is_featured=True,
                sort_order=order,
            )
        self.log(f"Destinations: {len(self.destinations)}")

    def seed_packages(self):
        for order, data in enumerate(catalog.PACKAGES):
            package = Package.objects.create(
                slug=data["slug"],
                title=data["title"],
                category=data["category"],
                destination=self._lookup(self.destinations, data["destination"], "destination"),
                image=self._lookup(self.images, data["image"], "image"),
                summary=data["summary"],
                description=f"<p>{data['description']}</p>",
                duration=data["duration"],
                duration_days=data["duration_days"],
                price=data["price"],
                difficulty=data["difficulty"],
                people_count=data["people_count"],
                max_altitude=data["max_altitude"],
                accommodation=data["accommodation"],
                meals=data["meals"],
                transport=data["transport"],
                is_popular=data["is_popular"],
                sort_order=order,
            )
            PackageHighlight.objects.bulk_create(
                PackageHighlight(package=package, text=text, sort_order=index)
                for index, text in enumerate(data["highlights"], start=1)
            )
            PackageItineraryDay.objects.bulk_create(
                PackageItineraryDay(package=package, day_label=label, title=title, description=text, sort_order=index)
                for index, (label, title, text) in enumerate(data["itinerary"], start=1)
            )
            PackageIncludedItem.objects.bulk_create(
                [
                    PackageIncludedItem(package=package, kind=kind, text=text, sort_order=index)
                    for kind, items in (("included", data["included"]), ("excluded", data["excluded"]))
                    for index, text in enumerate(items, start=1)
                ]
            )
            PackageGalleryImage.objects.bulk_create(
                PackageGalleryImage(
                    package=package,
                    image=self._lookup(self.images, key, "image"),
                    caption=f"{package.title} — photo {index}",
                    sort_order=index,
                )
                for index, key in enumerate(data["gallery"], start=1)
            )
            PackageGroupPrice.objects.bulk_create(
                PackageGroupPrice(package=package, **tier) for tier in default_group_prices(package.price)
            )
            self.packages[package.slug] = package
        self.log(f"Packages: {len(self.packages)}")

    def seed_testimonials(self):
        for order, data in enumerate(catalog.TESTIMONIALS):
            Testimonial.objects.create(
                author_name=data["author_name"],
                author_role=data["author_role"],
                quote=data["quote"],
                rating=data["rating"],
                package=self._lookup(self.packages, data["package"], "package") if data["package"] else None,
                is_featured=data["is_featured"],
                sort_order=order,
            )

    def seed_home(self):
        root = Page.get_first_root_node()
        # Wagtail's migrations create a placeholder page (and a Site pointing
        # at it); replace both with the Lumora home page.
        for placeholder in root.get_children():
            placeholder.delete()
        home = self.add_page(root, HomePage, body=pages.home_body(self), **pages.HOME)
        Site.objects.all().delete()
        Site.objects.create(hostname="localhost", port=80, root_page=home, is_default_site=True, site_name="Lumora Treks")
        return home

    def seed_site_pages(self, home):
        self.add_page(home, PackageIndexPage, **pages.packages_index(self))
        destinations_index = self.add_page(home, DestinationIndexPage, **pages.destinations_index(self))
        blog_index = self.add_page(home, BlogIndexPage, body=blog.index_body(self), **blog.INDEX)
        self.add_page(home, ContactPage, **pages.contact(self))
        self.add_page(home, PrivacyPage, **pages.privacy(self))
        self.add_page(home, StandardPage, **pages.terms(self))
        self.add_page(home, EnquiryPage, **pages.enquiry(self))
        checkout = self.add_page(home, CheckoutPage, **pages.checkout(self))
        self.add_page(checkout, PaymentSuccessPage, **pages.payment_success(self))

        for destination in self.destinations.values():
            self.add_page(
                destinations_index,
                DestinationDetailPage,
                title=destination.title,
                slug=destination.slug,
                destination=destination,
                body=pages.destination_detail_body(self),
            )
        # Package pages come from the same code path that creates them when an
        # editor adds a package, so seeded and hand-made packages match.
        for package in self.packages.values():
            ensure_detail_page(package)
        self.log(f"Pages: {Page.objects.filter(depth__gt=1).count()}")
        return blog_index

    def seed_blog(self, index):
        for data in blog.POSTS:
            author_name, author_role = blog.AUTHORS[data["author"]]
            self.add_page(
                index,
                BlogPostPage,
                title=data["title"],
                slug=data["slug"],
                excerpt=data["excerpt"],
                hero_image=self._lookup(self.images, data["image"], "image"),
                category=data["category"],
                featured=data["featured"],
                published_date=data["published"],
                author_name=author_name,
                author_role=author_role,
                author_avatar=self._lookup(self.images, "avatar-1", "image"),
                read_time_minutes=data["read_minutes"],
                article_body=self.checked(BlogPostPage, "article_body", blog.article_body(data["title"], self)),
                body=blog.post_body(self),
            )
        self.log(f"Blog posts: {len(blog.POSTS)}")

    def seed_settings(self):
        for model, values in (
            (BrandSettings, site_settings.BRAND),
            (NavigationSettings, site_settings.NAVIGATION),
            (FooterSettings, site_settings.FOOTER),
        ):
            instance = model.load()
            for field, value in values.items():
                if isinstance(value, list):
                    value = self.checked(model, field, value)
                setattr(instance, field, value)
            instance.save()
        ThemeSettings.load()
        IntegrationSettings.load()

    # Helpers ---------------------------------------------------------------

    def checked(self, model, field_name, raw):
        check_stream(model._meta.get_field(field_name).stream_block, raw, f"{model.__name__}.{field_name}")
        return raw

    def add_page(self, parent, page_class, body=None, **fields):
        page = page_class(**fields)
        if body is not None:
            page.body = self.checked(page_class, "body", body)
        parent.add_child(instance=page)
        page.save_revision().publish()
        return page


# ------------------------------------------------------------------ superuser


def ensure_superuser(log):
    """Create the admin account from Django's standard DJANGO_SUPERUSER_* variables."""
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    if not (username and password):
        log("No DJANGO_SUPERUSER_USERNAME/PASSWORD set — create an admin with `createsuperuser`.")
        return None
    User = get_user_model()
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, os.environ.get("DJANGO_SUPERUSER_EMAIL", ""), password)
        log(f"Created admin user {username!r}.")
    return username


# ------------------------------------------------------------------- entry


def seed_database(*, force=False, log=print):
    """Reset and seed unless this exact seed is already applied. Returns True if it seeded."""
    fingerprint = content_fingerprint()
    if not force and applied_fingerprint() == fingerprint:
        log(f"Seed {fingerprint[:12]} is already applied — nothing to do.")
        return False

    log(f"Seeding {fingerprint[:12]}: resetting the database…")
    reset_database(log)
    with transaction.atomic():
        summary = Seeder(log).run()
        SeedRun.objects.create(fingerprint=fingerprint, summary=summary)
    ensure_superuser(log)
    log(f"Seed complete: {summary}")
    return True
