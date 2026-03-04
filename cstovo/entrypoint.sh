#!/bin/sh
set -e

echo "Waiting for database..."
sleep 20

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput



echo "Starting Gunicorn..."
exec "$@"