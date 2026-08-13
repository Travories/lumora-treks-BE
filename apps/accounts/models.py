"""Profile data collected after a traveler signs in with Google."""

from django.conf import settings
from django.db import models


class TravelerProfile(models.Model):
    """Lumora-specific data attached to Django's built-in user model."""

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
    google_sub = models.CharField(
        max_length=255,
        unique=True,
        help_text="Stable subject identifier from Google's verified ID token.",
    )
    full_name = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
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
