from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.authentication import ExpiringTokenAuthentication, get_or_rotate_token
from apps.accounts.google import (
    GoogleAuthConfigurationError,
    GoogleCredentialError,
    verify_google_credential,
)
from apps.accounts.models import SocialIdentity, TravelerProfile
from apps.accounts.serializers import (
    GoogleCredentialSerializer,
    OnboardingSerializer,
    TravelerProfileSerializer,
)


def _profile_payload(profile):
    return TravelerProfileSerializer(profile).data


def _available_username(email, identity_hint):
    """Choose a deterministic username without exposing a collision failure."""

    User = get_user_model()
    max_length = User._meta.get_field("username").max_length
    email_username = email[:max_length]
    if not User.objects.filter(username=email_username).exists():
        return email_username

    base = f"google_{identity_hint}"[:max_length]
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        ending = f"_{suffix}"
        candidate = f"{base[:max_length - len(ending)]}{ending}"
        suffix += 1
    return candidate


def _find_google_identity(subject):
    return (
        SocialIdentity.objects.select_for_update()
        .select_related("user")
        .filter(provider=SocialIdentity.PROVIDER_GOOGLE, subject=subject)
        .first()
    )


def _sync_google_identity_profile(identity, email, google_name):
    """Update verified provider metadata without changing application role."""

    user = identity.user
    if not user.is_active:
        raise GoogleCredentialError("This account is disabled.")

    if user.email.lower() != email:
        user.email = email
        user.save(update_fields=["email"])

    if identity.provider_email.lower() != email:
        identity.provider_email = email
        identity.save(update_fields=["provider_email", "updated_at"])

    profile, profile_created = TravelerProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": TravelerProfile.ROLE_USER,
            "full_name": google_name,
        },
    )

    profile_updates = []
    if not profile_created and not profile.full_name and google_name:
        profile.full_name = google_name
        profile_updates.append("full_name")
    if profile_updates:
        profile.save(update_fields=[*profile_updates, "updated_at"])
    return profile


@transaction.atomic
def _get_or_create_google_profile(claims):
    User = get_user_model()
    subject = str(claims["sub"]).strip()
    email = User.objects.normalize_email(str(claims["email"]).strip()).lower()
    google_name = str(claims.get("name") or "").strip()[:150]

    identity = _find_google_identity(subject)
    if identity is not None:
        return _sync_google_identity_profile(
            identity,
            email,
            google_name,
        ), False

    # Email is provider metadata, not an account-linking key. In particular,
    # never attach Google to an existing staff or password-backed user merely
    # because the verified email matches. The provider subject is the identity
    # boundary and a new subject gets a new, unprivileged application account.
    try:
        # The savepoint rolls back the speculative user and profile if another
        # request wins the unique provider/subject race before this insert.
        with transaction.atomic():
            user = User(
                username=_available_username(email, subject),
                email=email,
                first_name=str(claims.get("given_name") or "").strip()[:150],
                last_name=str(claims.get("family_name") or "").strip()[:150],
            )
            user.set_unusable_password()
            user.save()

            profile = TravelerProfile.objects.create(
                user=user,
                role=TravelerProfile.ROLE_USER,
                full_name=google_name,
            )
            SocialIdentity.objects.create(
                user=user,
                provider=SocialIdentity.PROVIDER_GOOGLE,
                subject=subject,
                provider_email=email,
            )
    except IntegrityError:
        # The inner atomic block has restored this transaction to a usable
        # state, so refetch the winning identity under the outer transaction.
        identity = (
            SocialIdentity.objects.select_for_update()
            .select_related("user")
            .filter(provider=SocialIdentity.PROVIDER_GOOGLE, subject=subject)
            .first()
        )
        if identity is None:
            raise
        return _sync_google_identity_profile(
            identity,
            email,
            google_name,
        ), False
    return profile, True


class GoogleLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = GoogleCredentialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            claims = verify_google_credential(serializer.validated_data["credential"])
            profile, _created = _get_or_create_google_profile(claims)
        except GoogleAuthConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except GoogleCredentialError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        token = get_or_rotate_token(profile.user)
        return Response({"token": token.key, "user": _profile_payload(profile)})


class AuthenticatedProfileView(APIView):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_profile(request):
        try:
            return request.user.traveler_profile
        except TravelerProfile.DoesNotExist:
            return None


class MeView(AuthenticatedProfileView):
    def get(self, request):
        profile = self.get_profile(request)
        if profile is None:
            return Response(
                {"detail": "Traveler profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"user": _profile_payload(profile)})


class OnboardingView(AuthenticatedProfileView):
    @transaction.atomic
    def patch(self, request):
        profile = (
            TravelerProfile.objects.select_for_update()
            .filter(user=request.user)
            .first()
        )
        if profile is None:
            return Response(
                {"detail": "Traveler profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(profile, field, value)

        update_fields = [*serializer.validated_data.keys(), "updated_at"]
        if profile.has_valid_onboarding_data() and profile.onboarding_completed_at is None:
            profile.onboarding_completed_at = timezone.now()
            update_fields.append("onboarding_completed_at")
        profile.save(update_fields=update_fields)
        return Response({"user": _profile_payload(profile)})


class LogoutView(APIView):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response({"detail": "Logged out."})
