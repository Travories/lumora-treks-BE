"""Provider-neutral application profiles and external identities."""

from django.conf import settings
from django.db import models


class TravelerProfile(models.Model):
    """Lumora-specific data attached to Django's built-in user model."""

    ROLE_ADMIN = "ADMIN"
    ROLE_USER = "USER"
    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_USER, "User"),
    )

    INTEREST_CHOICES = (
        ("trekking", "Trekking"),
        ("sightseeing", "Sightseeing"),
        ("paragliding", "Paragliding"),
        ("culture", "Culture"),
        ("nature", "Nature"),
        ("wildlife", "Wildlife"),
        ("wellness", "Wellness"),
    )
    INTEREST_VALUES = frozenset(value for value, _label in INTEREST_CHOICES)
    MAX_INTERESTS = len(INTEREST_CHOICES)

    TRAVELER_TYPE_CHOICES = (
        ("solo", "Solo traveler"),
        ("couple", "Couple"),
        ("family", "Family"),
        ("friends", "Friends"),
        ("group", "Group"),
    )
    TRAVELER_TYPE_VALUES = frozenset(value for value, _label in TRAVELER_TYPE_CHOICES)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="traveler_profile",
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        help_text="Lumora application role; independent of Django CMS permissions.",
    )
    full_name = models.CharField(max_length=150, blank=True)
    interests = models.JSONField(default=list, blank=True)
    traveler_type = models.CharField(
        max_length=20,
        choices=TRAVELER_TYPE_CHOICES,
        blank=True,
    )
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "traveler profile"
        verbose_name_plural = "traveler profiles"

    def __str__(self):
        return self.full_name or self.user.email or self.user.get_username()

    def has_valid_onboarding_data(self):
        """Return whether every required onboarding field is valid."""

        interests = self.interests
        return bool(
            self.full_name.strip()
            and isinstance(interests, list)
            and 1 <= len(interests) <= self.MAX_INTERESTS
            and all(isinstance(interest, str) for interest in interests)
            and len(interests) == len(set(interests))
            and all(interest in self.INTEREST_VALUES for interest in interests)
            and self.traveler_type in self.TRAVELER_TYPE_VALUES
        )

    @property
    def onboarding_complete(self):
        return bool(self.onboarding_completed_at and self.has_valid_onboarding_data())


class SocialIdentity(models.Model):
    """A provider-owned identity linked to a Lumora user account."""

    PROVIDER_GOOGLE = "google"
    PROVIDER_CHOICES = ((PROVIDER_GOOGLE, "Google"),)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_identities",
    )
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES)
    subject = models.CharField(
        max_length=255,
        help_text="Stable user identifier issued by the provider.",
    )
    provider_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["provider", "subject"]
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "subject"),
                name="accounts_social_provider_subject_uniq",
            ),
            models.UniqueConstraint(
                fields=("user", "provider"),
                name="accounts_social_user_provider_uniq",
            ),
        ]
        verbose_name = "social identity"
        verbose_name_plural = "social identities"

    def __str__(self):
        return f"{self.provider}:{self.subject}"
