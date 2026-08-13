# Lumora Treks CMS/API

Django/Wagtail backend for the Lumora Treks frontend. It exposes the Wagtail API and custom catalog, site-settings, block-registry, and lead endpoints under `/api/v2/`.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

The default development settings use SQLite only when `DATABASE_URL` is absent. Use a local PostgreSQL/Redis/S3-compatible setup when testing production behavior.

For traveler sign-in, create a Google Web OAuth client and set
`GOOGLE_CLIENT_ID` to the same client ID used by the frontend's
`NEXT_PUBLIC_GOOGLE_CLIENT_ID`. Then run `python manage.py migrate` to create
the application profile, social-identity, and API-token tables. Google subjects
are stored in `SocialIdentity`; the profile itself is provider-neutral.

Account API responses expose the application role as `USER` or `ADMIN`.
Google-created accounts are always `USER`. This role is read-only through the
API and is independent of Django's `is_staff` and `is_superuser` CMS access;
only trusted database/admin workflows may promote an application account.

## Useful commands

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py seed_lumora
```

## API surface

- `/api/v2/pages/`, `/api/v2/images/`, `/api/v2/documents/` — Wagtail API
- `/api/v2/page-by-path/` — page payload for a frontend route
- `/api/v2/packages/` and `/api/v2/destinations/` — catalog
- `/api/v2/site/` — brand, navigation, footer, theme, integrations
- `/api/v2/block-registry/` — CMS/frontend component contract
- `/api/v2/leads/` — enquiry and newsletter submissions
- `/api/v2/auth/google/` — verify a Google ID token and start a traveler session
- `/api/v2/auth/me/`, `/api/v2/auth/onboarding/`, `/api/v2/auth/logout/` — traveler profile/session endpoints

Payment/booking endpoints are not implemented yet; the frontend must not claim payment success until a provider and server-side verification flow are added.
