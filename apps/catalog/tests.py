from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.accounts.models import TravelerProfile
from apps.catalog.models import Package, TravelerReview


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

    def test_review_requires_login_to_create(self):
        response = self.client.post(self.url, {"rating": 5, "body": "A wonderful and memorable trek."}, format="json")
        self.assertEqual(response.status_code, 401)

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
