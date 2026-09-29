#!/bin/sh
# Container start: static files → schema → optional clean seed → app server.
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# No-op unless SEED_DATABASE=true. When true, wipes the database and seeds it
# from apps/seed/data — once per version of the seed content, so restarts
# don't re-seed. See `python manage.py seed_database --help`.
python manage.py seed_database --if-enabled --noinput

exec gunicorn --bind 0.0.0.0:7319 --workers 3 --timeout 120 lumora.wsgi:application
