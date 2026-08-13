"""Provider-independent authentication for Lumora API tokens."""

from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


def token_is_expired(token, *, now=None):
    """Return whether a token has reached the configured server-side TTL."""

    now = now or timezone.now()
    expires_at = token.created + timedelta(days=settings.AUTH_TOKEN_TTL_DAYS)
    return expires_at <= now


@transaction.atomic
def get_or_rotate_token(user):
    """Return the user's current token, replacing it when its TTL has elapsed."""

    try:
        # A savepoint keeps the outer transaction usable if two first logins
        # attempt to create the user's one-to-one token simultaneously.
        with transaction.atomic():
            token, created = Token.objects.select_for_update().get_or_create(user=user)
    except IntegrityError:
        token = Token.objects.select_for_update().get(user=user)
        created = False
    if not created and token_is_expired(token):
        token.delete()
        token = Token.objects.create(user=user)
    return token


class ExpiringTokenAuthentication(TokenAuthentication):
    """DRF token authentication with deletion on server-side expiration."""

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")

        if not token.user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        if token_is_expired(token):
            token.delete()
            raise AuthenticationFailed("Token has expired.")

        return token.user, token
