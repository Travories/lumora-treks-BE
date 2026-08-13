from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.accounts.authentication import token_is_expired
from apps.accounts.google import GoogleCredentialError
from apps.accounts.models import SocialIdentity, TravelerProfile


@override_settings(
    GOOGLE_CLIENT_ID="lumora-test.apps.googleusercontent.com",
    AUTH_TOKEN_TTL_DAYS=30,
)
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
                "role": "USER",
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
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(profile.role, TravelerProfile.ROLE_USER)
        identity = SocialIdentity.objects.get()
        self.assertEqual(identity.user, user)
        self.assertEqual(identity.provider, SocialIdentity.PROVIDER_GOOGLE)
        self.assertEqual(identity.subject, "google-user-123")
        self.assertEqual(identity.provider_email, "traveler@example.com")
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
        self.assertEqual(SocialIdentity.objects.count(), 1)
        profile.refresh_from_db()
        identity = SocialIdentity.objects.get()
        self.assertEqual(profile.full_name, "My chosen name")
        self.assertEqual(profile.user.email, "new-address@example.com")
        self.assertEqual(profile.avatar_url, "https://example.com/new-avatar.jpg")
        self.assertEqual(identity.provider_email, "new-address@example.com")

    def test_google_relogin_rotates_expired_token(self):
        first_response = self.google_login()
        old_key = first_response.data["token"]
        Token.objects.filter(key=old_key).update(
            created=timezone.now() - timedelta(days=31),
        )

        second_response = self.google_login()

        self.assertEqual(second_response.status_code, 200)
        self.assertNotEqual(second_response.data["token"], old_key)
        self.assertFalse(Token.objects.filter(key=old_key).exists())
        new_token = Token.objects.get(user__email="traveler@example.com")
        self.assertEqual(new_token.key, second_response.data["token"])
        self.assertFalse(token_is_expired(new_token))

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
        self.assertEqual(SocialIdentity.objects.get().user, traveler)

    def test_google_login_never_links_an_existing_password_user_by_email(self):
        User = get_user_model()
        password_user = User.objects.create_user(
            username="existing-traveler",
            email="traveler@example.com",
            password="not-a-real-production-password",
        )
        existing_profile = TravelerProfile.objects.create(
            user=password_user,
            full_name="Existing Traveler",
        )

        response = self.google_login()

        self.assertEqual(response.status_code, 200)
        google_user = User.objects.get(pk=response.data["user"]["id"])
        self.assertNotEqual(google_user, password_user)
        self.assertEqual(SocialIdentity.objects.get().user, google_user)
        self.assertFalse(password_user.social_identities.exists())
        existing_profile.refresh_from_db()
        self.assertEqual(existing_profile.role, TravelerProfile.ROLE_USER)

    def test_google_login_request_cannot_choose_application_role(self):
        with patch("apps.accounts.views.verify_google_credential") as verifier:
            response = self.client.post(
                reverse("accounts:google"),
                {
                    "credential": "mock-google-credential",
                    "role": "ADMIN",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("role", response.data)
        verifier.assert_not_called()
        self.assertFalse(get_user_model().objects.exists())

    def test_google_login_recovers_when_provider_identity_race_is_lost(self):
        winner = get_user_model().objects.create_user(
            username="race-winner",
            email="traveler@example.com",
        )
        winner.set_unusable_password()
        winner.save(update_fields=["password"])
        TravelerProfile.objects.create(
            user=winner,
            role=TravelerProfile.ROLE_USER,
            full_name="Race Winner",
        )
        SocialIdentity.objects.create(
            user=winner,
            provider=SocialIdentity.PROVIDER_GOOGLE,
            subject=self.google_claims["sub"],
            provider_email=self.google_claims["email"],
        )

        # Force the initial lookup to model a stale concurrent miss. The
        # speculative insert then hits the real unique constraint, rolls back
        # to its savepoint, and refetches the winner through the real manager.
        with patch("apps.accounts.views._find_google_identity", return_value=None):
            response = self.google_login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], winner.pk)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(TravelerProfile.objects.count(), 1)
        self.assertEqual(SocialIdentity.objects.count(), 1)
        self.assertEqual(Token.objects.get().user, winner)

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

    def test_expired_token_is_deleted_and_rejected_by_me(self):
        login = self.authenticate()
        token_key = login.data["token"]
        Token.objects.filter(key=token_key).update(
            created=timezone.now() - timedelta(days=31),
        )

        response = self.client.get(reverse("accounts:me"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(str(response.data["detail"]), "Token has expired.")
        self.assertFalse(Token.objects.filter(key=token_key).exists())

    def test_lumora_token_authenticates_profile_without_social_identity(self):
        user = get_user_model().objects.create_user(
            username="local-admin",
            email="admin@example.com",
            password="not-a-real-production-password",
        )
        profile = TravelerProfile.objects.create(
            user=user,
            role=TravelerProfile.ROLE_ADMIN,
            full_name="Lumora Admin",
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get(reverse("accounts:me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], user.pk)
        self.assertEqual(response.data["user"]["role"], "ADMIN")
        self.assertEqual(response.data["user"]["full_name"], profile.full_name)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(SocialIdentity.objects.exists())

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

    def test_onboarding_cannot_elevate_application_role(self):
        self.authenticate()
        profile = TravelerProfile.objects.get()

        response = self.client.patch(
            reverse("accounts:onboarding"),
            {"role": "ADMIN"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("role", response.data)
        profile.refresh_from_db()
        self.assertEqual(profile.role, TravelerProfile.ROLE_USER)

    def test_logout_revokes_token(self):
        login = self.authenticate()

        response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"detail": "Logged out."})
        self.assertFalse(Token.objects.filter(key=login.data["token"]).exists())
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 401)
