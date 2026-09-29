import shutil
import tempfile
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from wagtail.models import Site

from apps.catalog.models import Destination, Package
from apps.cms.models import BlogPostPage, ContactPage, DestinationDetailPage, HomePage, PackageDetailPage
from apps.seed import pipeline
from apps.seed.data import blog, catalog
from apps.seed.data.media import IMAGES
from apps.seed.models import SeedRun

MEDIA_ROOT = tempfile.mkdtemp(prefix="lumora-seed-tests-")


def tearDownModule():
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


def quiet(message):
    pass


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class SeedContentTests(TestCase):
    """The seed builds a complete, linked site. (`reset_database` is not run:
    the test database is already empty and migrated.)"""

    @classmethod
    def setUpTestData(cls):
        with override_settings(MEDIA_ROOT=MEDIA_ROOT):
            cls.summary = pipeline.Seeder(quiet).run()

    def test_creates_every_record_in_the_seed_data(self):
        self.assertEqual(self.summary["images"], len(IMAGES))
        self.assertEqual(Destination.objects.count(), len(catalog.DESTINATIONS))
        self.assertEqual(Package.objects.count(), len(catalog.PACKAGES))
        self.assertEqual(BlogPostPage.objects.live().count(), len(blog.POSTS))

    def test_every_catalog_item_has_a_public_page(self):
        self.assertEqual(PackageDetailPage.objects.live().count(), len(catalog.PACKAGES))
        self.assertEqual(DestinationDetailPage.objects.live().count(), len(catalog.DESTINATIONS))

    def test_packages_are_complete(self):
        for package in Package.objects.all():
            with self.subTest(package=package.slug):
                self.assertIsNotNone(package.image)
                self.assertIsNotNone(package.destination)
                self.assertTrue(package.itinerary.exists())
                self.assertTrue(package.gallery.exists())
                self.assertTrue(package.included_items.filter(kind="included").exists())
                self.assertTrue(package.group_pricing.exists())

    def test_package_detail_exposes_trip_facts(self):
        from apps.catalog.serializers import serialize_package

        data = serialize_package(Package.objects.get(slug="annapurna-base-camp-trek"), detail=True)
        self.assertEqual(data["max_altitude"], 4130)
        for fact in ("accommodation", "meals", "transport", "difficulty"):
            with self.subTest(fact=fact):
                self.assertTrue(data[fact])

    def test_api_serves_display_renditions_not_originals(self):
        from apps.core.serializers import serialize_image

        data = serialize_image(Package.objects.get(slug="annapurna-base-camp-trek").image)
        self.assertIn("max-1600x1600", data["url"])
        self.assertEqual(data["src"], data["url"])
        self.assertIn("original_images/", data["original_url"])

    def test_seed_content_fits_every_editorial_limit(self):
        """Editors must be able to save any seeded page or snippet unchanged."""
        from django.apps import apps as django_apps
        from wagtail.fields import StreamField
        from wagtail.models import Page

        from apps.cms.models import BlogPostPageForm

        for page in Page.objects.filter(depth__gt=1).specific():
            for field in page._meta.get_fields():
                if isinstance(field, StreamField):
                    with self.subTest(page=page.url_path, field=field.name):
                        field.stream_block.clean(getattr(page, field.name))
        for label in (
            "catalog.Package", "catalog.Destination", "catalog.Testimonial", "catalog.PackageHighlight",
            "catalog.PackageItineraryDay", "catalog.PackageIncludedItem", "catalog.PackageGalleryImage",
            "navigation.BrandSettings", "navigation.FooterSettings", "navigation.NavigationSettings",
        ):
            for obj in django_apps.get_model(label).objects.all():
                with self.subTest(obj=f"{label}:{obj.pk}"):
                    obj.clean_fields(exclude=["slug", "image", "logo", "logo_dark", "favicon", "default_share_image"])
        for post in BlogPostPage.objects.all():
            with self.subTest(post=post.slug):
                self.assertLessEqual(len(post.title), BlogPostPageForm.TITLE_MAX_LENGTH)
                post.clean_fields(exclude=["path", "depth", "url_path", "draft_title", "slug", "hero_image", "author_avatar"])

    def test_home_is_the_site_root(self):
        site = Site.objects.get(is_default_site=True)
        self.assertIsInstance(site.root_page.specific, HomePage)

    def test_contact_page_has_the_enquiry_form(self):
        body = [block.block_type for block in ContactPage.objects.get().body]
        self.assertEqual(body, ["contact_hero", "contact_form", "faq"])


class SeedValidationTests(TestCase):
    def test_unknown_block_fields_are_rejected(self):
        stream_block = ContactPage._meta.get_field("body").stream_block
        with self.assertRaisesMessage(pipeline.SeedError, "unknown field(s) headline"):
            pipeline.check_stream(stream_block, [{"type": "faq", "value": {"headline": "x"}}], "body")

    def test_blocks_not_allowed_on_the_page_are_rejected(self):
        stream_block = ContactPage._meta.get_field("body").stream_block
        with self.assertRaisesMessage(pipeline.SeedError, "'lead_form' is not allowed here"):
            pipeline.check_stream(stream_block, [{"type": "lead_form", "value": {}}], "body")

    def test_unknown_references_fail_loudly(self):
        with self.assertRaisesMessage(pipeline.SeedError, "Unknown image 'nope'"):
            pipeline.Seeder(quiet).image("nope")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@mock.patch.object(pipeline, "reset_database")
class SeedIdempotencyTests(TestCase):
    def test_same_seed_is_applied_only_once(self, reset_database):
        self.assertTrue(pipeline.seed_database(log=quiet))
        self.assertFalse(pipeline.seed_database(log=quiet))
        reset_database.assert_called_once()
        self.assertEqual(SeedRun.objects.get().fingerprint, pipeline.content_fingerprint())

    def test_changed_seed_content_is_reseeded(self, reset_database):
        SeedRun.objects.create(fingerprint="an-older-seed")
        with mock.patch.object(pipeline.Seeder, "run", return_value={}):
            self.assertTrue(pipeline.seed_database(log=quiet))
        reset_database.assert_called_once()

    def test_command_does_nothing_when_seeding_is_disabled(self, reset_database):
        out = StringIO()
        with override_settings(SEED_DATABASE=False):
            call_command("seed_database", "--if-enabled", "--noinput", stdout=out)
        reset_database.assert_not_called()
        self.assertIn("SEED_DATABASE is off", out.getvalue())


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class DisplayRenditionSignalTests(TestCase):
    def test_saving_an_image_pregenerates_its_display_rendition(self):
        from django.core.files.images import ImageFile

        from apps.core.models import CustomImage
        from apps.core.serializers import DISPLAY_RENDITION

        with self.captureOnCommitCallbacks(execute=True):
            with (pipeline.MEDIA_DIR / "patan.webp").open("rb") as handle:
                image = CustomImage(title="Patan")
                image.file = ImageFile(handle, name="patan.webp")
                image.save()
        self.assertTrue(image.renditions.filter(filter_spec=DISPLAY_RENDITION).exists())
