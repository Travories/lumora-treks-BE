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

Payment/booking endpoints are not implemented yet; the frontend must not claim payment success until a provider and server-side verification flow are added.
