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
Lumora API tokens are provider-independent and expire server-side after
`AUTH_TOKEN_TTL_DAYS` (30 days by default); expired tokens are revoked, and a
successful Google re-login issues a fresh token.

## Lumora Admin (`/admin/`)

The Wagtail admin is branded **Lumora Admin** (`templates/wagtailadmin/`,
`static/lumora_admin/`). Sidebar:

| Menu | What editors do there | Defined in |
| --- | --- | --- |
| Pages | Page tree: home, listing pages, contact, legal | Wagtail |
| Blog | Flat list of every blog post | `apps/cms/wagtail_hooks.py` |
| Packages / Destinations / Testimonials | Catalog data | `apps/catalog/wagtail_hooks.py` |
| Leads | Enquiries and newsletter sign-ups | `apps/leads/wagtail_hooks.py` |
| Media | Images, videos, documents | `apps/core/wagtail_hooks.py` |
| Site settings | Brand, navigation, footer, theme, integrations | `apps/navigation/wagtail_hooks.py` |
| Administration | Users, groups, sites, redirects, workflows | Wagtail |

Each package and destination has two halves: the **snippet** holds the data
(price, itinerary, inclusions, region…) and an auto-created **detail page**
holds the screen layout and SEO. A "Related content" panel at the top of each
edit screen links the two, plus the destination's packages and a package's
leads and testimonials (`apps/catalog/editorial.py`).

The site is headless: page URLs ("View live", API `html_url`, SEO canonical
URLs, rich-text links) resolve to `FRONTEND_BASE_URL`, and old
`/cms-preview/…` links redirect there. **Set `FRONTEND_BASE_URL` in every
environment** (production defaults to `https://lumora.rivetsoft.com`).

## Seed data

`apps/seed` holds the site's starting content — 17 destinations, 5 packages
(itineraries, galleries, inclusions, group pricing), 7 blog posts, every page
under Home, site settings and the images they use (`apps/seed/media/`).

```bash
python manage.py seed_database            # wipe ALL data and seed (asks first)
python manage.py seed_database --force    # re-seed even if this seed is applied
```

With Docker, set `SEED_DATABASE` in `.env` and run `docker compose up --build -d`:

| `SEED_DATABASE` | On container start |
| --- | --- |
| `false` (default) | Existing data is left untouched. |
| `true` | Deletes all data, users and uploaded media, then seeds — **once per version of the seed content**. Restarts with the same content do nothing; changing anything in `apps/seed/data`, `apps/seed/media` or `apps/seed/pipeline.py` triggers one clean re-seed. |

After a seed, the admin account comes from `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD`. Set `SEED_DATABASE`
back to `false` once editors start working in production, or their changes
are lost the next time the seed content changes.

## Useful commands

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
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
