import io

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from wagtail.models import Page

from apps.accounts.models import TravelerProfile
from apps.catalog.models import Package, PackageGroupPrice, TravelerReview
from apps.catalog.serializers import serialize_package
from apps.catalog.pricing import default_group_prices
from apps.cms.models import HomePage, PackageDetailPage, PackageFolderPage, PackageIndexPage


class PackageReviewApiTests(APITestCase):
    def setUp(self):
        self.package = Package.objects.create(title="Everest Base Camp", price=1000)
        User = get_user_model()
        self.author = User.objects.create_user(username="author", email="asha@example.com")
        TravelerProfile.objects.create(user=self.author, full_name="Asha Rai")
        self.other = User.objects.create_user(username="other", email="bikash@example.com")
        TravelerProfile.objects.create(user=self.other, full_name="Bikash Lama")
        self.url = f"{reverse('package-reviews')}?package={self.package.slug}"

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")

    def test_new_package_starts_unrated(self):
        self.assertEqual(float(self.package.rating), 0.0)
        self.assertEqual(self.package.review_count, 0)

    def test_review_requires_login_to_create(self):
        response = self.client.post(self.url, {"rating": 5, "body": "A wonderful and memorable trek."}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_guest_can_list_reviews(self):
        TravelerReview.objects.create(
            package=self.package,
            user=self.author,
            rating=5,
            body="A wonderful and memorable trek.",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["items"][0]["author_name"], "Asha Rai")
        self.assertFalse(response.data["items"][0]["is_mine"])

    def test_user_can_create_update_delete_then_create_review_again(self):
        self.authenticate(self.author)
        created = self.client.post(self.url, {"rating": 5, "body": "A wonderful and memorable trek."}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.data["review"]["is_mine"])
        self.assertEqual(TravelerReview.objects.count(), 1)

        duplicate = self.client.post(self.url, {"rating": 4, "body": "Still a wonderful and memorable trek."}, format="json")
        self.assertEqual(duplicate.status_code, 409)

        updated = self.client.patch(self.url, {"rating": 4, "body": "A thoughtful, well-organized mountain experience."}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["review"]["rating"], 4)
        self.package.refresh_from_db()
        self.assertEqual(float(self.package.rating), 4.0)
        self.assertEqual(self.package.review_count, 1)

        deleted = self.client.delete(self.url)
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(TravelerReview.objects.exists())

        recreated = self.client.post(self.url, {"rating": 3, "body": "A solid trip with a few rough edges."}, format="json")
        self.assertEqual(recreated.status_code, 201)
        self.assertEqual(TravelerReview.objects.count(), 1)

    def test_current_users_review_is_pinned_first_and_listing_is_paginated(self):
        TravelerReview.objects.create(package=self.package, user=self.other, rating=4, body="Beautiful trails and very kind guides.")
        TravelerReview.objects.create(package=self.package, user=self.author, rating=5, body="Excellent pace, views, and local support throughout.")
        self.authenticate(self.author)

        response = self.client.get(f"{self.url}&limit=1&offset=0")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["total_count"], 2)
        self.assertEqual(response.data["items"][0]["author_name"], "Asha Rai")
        self.assertTrue(response.data["items"][0]["is_mine"])
        self.assertEqual(response.data["summary"]["total"], 2)
        self.assertEqual(response.data["summary"]["distribution"]["5"], 1)


class PackageGroupPricingTests(TestCase):
    def setUp(self):
        self.package = Package.objects.create(title="Everest Base Camp", price=1560)

    def test_group_price_requires_sensible_bounds_and_positive_price(self):
        invalid_range = PackageGroupPrice(
            package=self.package,
            min_people=4,
            max_people=3,
            price_per_person=1400,
        )
        with self.assertRaises(ValidationError) as range_error:
            invalid_range.full_clean()
        self.assertIn("max_people", range_error.exception.message_dict)

        invalid_price = PackageGroupPrice(
            package=self.package,
            min_people=1,
            max_people=1,
            price_per_person=0,
        )
        with self.assertRaises(ValidationError) as price_error:
            invalid_price.full_clean()
        self.assertIn("price_per_person", price_error.exception.message_dict)

    def test_package_payload_contains_ordered_group_pricing(self):
        PackageGroupPrice.objects.create(
            package=self.package,
            min_people=4,
            max_people=7,
            price_per_person=1220,
            sort_order=2,
        )
        PackageGroupPrice.objects.create(
            package=self.package,
            min_people=1,
            max_people=1,
            price_per_person=1560,
            sort_order=1,
        )
        PackageGroupPrice.objects.create(
            package=self.package,
            min_people=8,
            max_people=None,
            price_per_person=1140,
            sort_order=3,
        )

        expected = [
            {"min_people": 1, "max_people": 1, "price_per_person": 1560.0},
            {"min_people": 4, "max_people": 7, "price_per_person": 1220.0},
            {"min_people": 8, "max_people": None, "price_per_person": 1140.0},
        ]
        self.assertEqual(serialize_package(self.package)["group_pricing"], expected)
        self.assertEqual(serialize_package(self.package, detail=True)["group_pricing"], expected)

    def test_default_group_prices_are_whole_numbers_with_10_to_20_percent_reductions(self):
        tiers = default_group_prices(400.23)

        self.assertEqual(
            [tier["price_per_person"] for tier in tiers],
            [400, 360, 340, 320],
        )
        self.assertTrue(all(isinstance(tier["price_per_person"], int) for tier in tiers))

    def test_population_command_is_dry_run_then_idempotent(self):
        call_command("populate_group_pricing", stdout=io.StringIO())
        self.assertEqual(self.package.group_pricing.count(), 0)

        call_command("populate_group_pricing", "--apply", stdout=io.StringIO())
        self.assertEqual(self.package.group_pricing.count(), 4)

        output = io.StringIO()
        call_command("populate_group_pricing", "--apply", stdout=output)
        self.assertIn("Populated group pricing for 0 packages.", output.getvalue())
        self.assertEqual(self.package.group_pricing.count(), 4)


class PackageDetailPageAutoCreateTests(TestCase):
    """The post_save signal in apps/catalog/signals.py should publish a live
    detail page at /packages/<slug>/<public_code> whenever a package is created."""

    def _build_packages_index(self):
        root = Page.get_first_root_node()
        # Wagtail's migrations seed a default page at slug "home"; use a distinct
        # slug so this fixture's HomePage doesn't collide with it.
        home = HomePage(title="Home", slug="home-test")
        root.add_child(instance=home)
        index = PackageIndexPage(title="Packages", slug="packages")
        home.add_child(instance=index)
        return index

    def test_creating_package_publishes_folder_and_detail_pages(self):
        index = self._build_packages_index()

        with self.captureOnCommitCallbacks(execute=True):
            package = Package.objects.create(title="Annapurna Base Camp", price=650)

        # Re-fetch the index: the in-memory instance still caches numchild=0, so
        # treebeard's get_children() would short-circuit via is_leaf().
        index.refresh_from_db()
        folder = index.get_children().type(PackageFolderPage).get(slug=package.slug).specific
        detail = PackageDetailPage.objects.get(package=package)
        self.assertEqual(detail.get_parent().specific, folder)
        self.assertEqual(detail.slug, package.public_code)
        self.assertTrue(detail.live)
        self.assertEqual(
            [block.block_type for block in detail.body],
            [
                "package_header",
                "package_overview",
                "package_booking",
                "package_itinerary",
                "package_reviews",
            ],
        )
        self.assertEqual(
            detail.body[2].value["reserve_href"],
            f"/enquiry?package={package.slug}",
        )

    def test_auto_creation_is_idempotent_and_scoped_per_package(self):
        index = self._build_packages_index()

        with self.captureOnCommitCallbacks(execute=True):
            first = Package.objects.create(title="Everest Base Camp", price=1200)
            second = Package.objects.create(title="Langtang Valley", price=500)

        # Re-saving must not create a duplicate detail page.
        with self.captureOnCommitCallbacks(execute=True):
            first.summary = "Updated"
            first.save()

        self.assertEqual(PackageDetailPage.objects.filter(package=first).count(), 1)
        self.assertEqual(PackageDetailPage.objects.filter(package=second).count(), 1)
        index.refresh_from_db()
        self.assertEqual(index.get_children().type(PackageFolderPage).count(), 2)

    def test_package_saves_cleanly_without_a_packages_index(self):
        with self.captureOnCommitCallbacks(execute=True):
            package = Package.objects.create(title="Mustang Trek", price=900)

        self.assertFalse(PackageDetailPage.objects.filter(package=package).exists())

    def test_missing_page_self_heals_on_a_later_save(self):
        # Created before the packages index exists -> no page yet.
        with self.captureOnCommitCallbacks(execute=True):
            package = Package.objects.create(title="Manaslu Circuit", price=1100)
        self.assertFalse(PackageDetailPage.objects.filter(package=package).exists())

        # Once the index exists, any subsequent save creates the missing page.
        self._build_packages_index()
        with self.captureOnCommitCallbacks(execute=True):
            package.summary = "Now with an index page"
            package.save()

        self.assertTrue(PackageDetailPage.objects.filter(package=package).exists())
