"""Google ID-token verification kept behind a small, mockable boundary."""

from django.conf import settings


class GoogleCredentialError(Exception):
    """The supplied credential or its required identity claims are invalid."""


class GoogleAuthConfigurationError(Exception):
    """Google authentication is not configured on the server."""


def verify_google_credential(credential):
    """Verify a Google Identity Services credential and return its claims."""

    client_id = settings.GOOGLE_CLIENT_ID.strip()
    if not client_id:
        raise GoogleAuthConfigurationError("Google sign-in is not configured.")

    # Lazy imports keep management commands usable while dependencies are being
    # installed; production requirements always install google-auth.
    try:
        from google.auth.exceptions import GoogleAuthError
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token
    except ImportError as exc:  # pragma: no cover - deployment/configuration failure
        raise GoogleAuthConfigurationError("Google authentication support is unavailable.") from exc

    try:
        claims = id_token.verify_oauth2_token(
            credential,
            Request(),
            audience=client_id,
        )
    except (GoogleAuthError, ValueError) as exc:
        raise GoogleCredentialError("Invalid or expired Google credential.") from exc

    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise GoogleCredentialError("Invalid Google credential issuer.")
    if claims.get("aud") != client_id:
        raise GoogleCredentialError("Google credential was issued for another application.")
    if claims.get("email_verified") not in {True, "true"}:
        raise GoogleCredentialError("A verified Google email address is required.")
    if not str(claims.get("sub") or "").strip() or not str(claims.get("email") or "").strip():
        raise GoogleCredentialError("Google credential is missing required identity claims.")

    return claims
