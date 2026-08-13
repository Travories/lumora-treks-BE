from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.accounts.google import GoogleCredentialError
from apps.accounts.models import TravelerProfile


@override_settings(GOOGLE_CLIENT_ID="lumora-test.apps.googleusercontent.com")
class AccountApiTests(TestCase):
    google_claims = {
        "sub": "google-user-123",
        "email": "traveler@example.com",
        "email_verified": True,
        "name": "Asha Rai",
        "given_name": "Asha",
        "family_name": "Rai",
        "picture": "https://example.com/asha.jpg",
        "iss": "https://accounts.google.com",
        "aud": "lumora-test.apps.googleusercontent.com",
    }

    def setUp(self):
        self.client = APIClient()

    def google_login(self, claims=None):
        with patch(
            "apps.accounts.views.verify_google_credential",
            return_value=claims or self.google_claims,
        ) as verifier:
            response = self.client.post(
                reverse("accounts:google"),
                {"credential": "mock-google-credential"},
                format="json",
            )
        verifier.assert_called_once_with("mock-google-credential")
        return response

    def authenticate(self):
        response = self.google_login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        return response

    def test_google_login_creates_user_profile_and_token(self):
        response = self.google_login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"token", "user"})
        self.assertEqual(
            response.data["user"],
            {
                "id": get_user_model().objects.get().pk,
                "email": "traveler@example.com",
                "full_name": "Asha Rai",
                "avatar_url": "https://example.com/asha.jpg",
                "interests": [],
                "traveler_type": "",
                "onboarding_complete": False,
            },
        )
        user = get_user_model().objects.get()
        profile = user.traveler_profile
        self.assertFalse(user.has_usable_password())
        self.assertEqual(profile.google_sub, "google-user-123")
        self.assertTrue(Token.objects.filter(user=user, key=response.data["token"]).exists())

    def test_google_login_reuses_google_subject_and_preserves_onboarding_name(self):
        first_response = self.google_login()
        profile = TravelerProfile.objects.get()
        profile.full_name = "My chosen name"
        profile.save(update_fields=["full_name", "updated_at"])
        updated_claims = {
            **self.google_claims,
            "email": "new-address@example.com",
            "name": "Google Name",
            "picture": "https://example.com/new-avatar.jpg",
        }

        second_response = self.google_login(updated_claims)

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.data["token"], first_response.data["token"])
        self.assertEqual(get_user_model().objects.count(), 1)
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, "My chosen name")
        self.assertEqual(profile.user.email, "new-address@example.com")
        self.assertEqual(profile.avatar_url, "https://example.com/new-avatar.jpg")

    def test_google_login_never_links_an_existing_staff_account_by_email(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="cms-editor",
            email="traveler@example.com",
            password="not-a-real-production-password",
            is_staff=True,
        )

        response = self.google_login()

        self.assertEqual(response.status_code, 200)
        traveler = User.objects.get(pk=response.data["user"]["id"])
        self.assertNotEqual(traveler.pk, staff.pk)
        self.assertFalse(traveler.is_staff)
        self.assertFalse(traveler.has_usable_password())
        self.assertFalse(hasattr(staff, "traveler_profile"))

    def test_google_login_rejects_invalid_credential(self):
        with patch(
            "apps.accounts.views.verify_google_credential",
            side_effect=GoogleCredentialError("Invalid or expired Google credential."),
        ):
            response = self.client.post(
                reverse("accounts:google"),
                {"credential": "bad"},
                format="json",
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid or expired Google credential."})
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_me_requires_token_and_returns_profile_contract(self):
        unauthenticated = self.client.get(reverse("accounts:me"))
        login = self.authenticate()

        response = self.client.get(reverse("accounts:me"))

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"user": login.data["user"]})

    def test_onboarding_only_completes_after_all_valid_fields_are_saved(self):
        self.authenticate()

        partial_response = self.client.patch(
            reverse("accounts:onboarding"),
            {"full_name": "Asha Sherpa"},
            format="json",
        )
        self.assertEqual(partial_response.status_code, 200)
        self.assertFalse(partial_response.data["user"]["onboarding_complete"])

        complete_response = self.client.patch(
            reverse("accounts:onboarding"),
            {
                "interests": ["trekking", "culture"],
                "traveler_type": "solo",
            },
            format="json",
        )

        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(
            complete_response.data["user"],
            {
                **partial_response.data["user"],
                "interests": ["trekking", "culture"],
                "traveler_type": "solo",
                "onboarding_complete": True,
            },
        )
        profile = TravelerProfile.objects.get()
        self.assertIsNotNone(profile.onboarding_completed_at)

    def test_onboarding_rejects_values_outside_allowlists_without_mutating_profile(self):
        self.authenticate()
        profile = TravelerProfile.objects.get()

        response = self.client.patch(
            reverse("accounts:onboarding"),
            {
                "full_name": "Asha Sherpa",
                "interests": ["nightlife"],
                "traveler_type": "business",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, "Asha Rai")
        self.assertEqual(profile.interests, [])
        self.assertEqual(profile.traveler_type, "")
        self.assertIsNone(profile.onboarding_completed_at)

    def test_logout_revokes_token(self):
        login = self.authenticate()

        response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"detail": "Logged out."})
        self.assertFalse(Token.objects.filter(key=login.data["token"]).exists())
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 401)
