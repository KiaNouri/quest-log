#!/bin/sh
set -e

export DJANGO_SETTINGS_MODULE=django_project.settings.production

python manage.py migrate --noinput

# Replace this shell process with the production web server
exec gunicorn django_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class gthread \
    --threads 2 \
    --timeout 30 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile -