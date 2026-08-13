from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.google import (
    GoogleAuthConfigurationError,
    GoogleCredentialError,
    verify_google_credential,
)
from apps.accounts.models import TravelerProfile
from apps.accounts.serializers import (
    GoogleCredentialSerializer,
    OnboardingSerializer,
    TravelerProfileSerializer,
)


def _profile_payload(profile):
    return TravelerProfileSerializer(profile).data


def _available_username(email, google_sub):
    """Choose a deterministic username without exposing a collision failure."""

    User = get_user_model()
    max_length = User._meta.get_field("username").max_length
    email_username = email[:max_length]
    if not User.objects.filter(username=email_username).exists():
        return email_username

    base = f"google_{google_sub}"[:max_length]
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        ending = f"_{suffix}"
        candidate = f"{base[:max_length - len(ending)]}{ending}"
        suffix += 1
    return candidate


@transaction.atomic
def _get_or_create_google_profile(claims):
    User = get_user_model()
    google_sub = str(claims["sub"]).strip()
    email = User.objects.normalize_email(str(claims["email"]).strip()).lower()
    google_name = str(claims.get("name") or "").strip()[:150]
    avatar_url = str(claims.get("picture") or "").strip()[:500]

    profile = (
        TravelerProfile.objects.select_for_update()
        .select_related("user")
        .filter(google_sub=google_sub)
        .first()
    )
    if profile is not None:
        if not profile.user.is_active:
            raise GoogleCredentialError("This account is disabled.")

        email_owner = (
            TravelerProfile.objects.select_for_update()
            .filter(user__email__iexact=email)
            .exclude(pk=profile.pk)
            .first()
        )
        if email_owner is not None:
            raise GoogleCredentialError("This email is already linked to another Google account.")

        user_changed = False
        if profile.user.email.lower() != email:
            profile.user.email = email
            user_changed = True
        if user_changed:
            profile.user.save(update_fields=["email"])

        profile_updates = []
        if not profile.full_name and google_name:
            profile.full_name = google_name
            profile_updates.append("full_name")
        if avatar_url and profile.avatar_url != avatar_url:
            profile.avatar_url = avatar_url
            profile_updates.append("avatar_url")
        if profile_updates:
            profile.save(update_fields=[*profile_updates, "updated_at"])
        return profile, False

    linked_profile = (
        TravelerProfile.objects.select_for_update()
        .filter(user__email__iexact=email)
        .first()
    )
    if linked_profile is not None:
        raise GoogleCredentialError("This email is already linked to another Google account.")

    # Never attach a social login to an existing password/staff account by
    # matching email alone. Django does not require User.email to be unique,
    # and Google's stable verified subject is the identity boundary here.
    user = User(
        username=_available_username(email, google_sub),
        email=email,
        first_name=str(claims.get("given_name") or "").strip()[:150],
        last_name=str(claims.get("family_name") or "").strip()[:150],
    )
    user.set_unusable_password()
    user.save()

    profile = TravelerProfile.objects.create(
        user=user,
        google_sub=google_sub,
        full_name=google_name,
        avatar_url=avatar_url,
    )
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

        token, _created = Token.objects.get_or_create(user=profile.user)
        return Response({"token": token.key, "user": _profile_payload(profile)})


class AuthenticatedProfileView(APIView):
    authentication_classes = [TokenAuthentication]
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
        profile = self.get_profile(request)
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Logged out."})
