#!/bin/sh
set -e

echo "Waiting for Postgres..."

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "Postgres is up!"

echo "Running makemigrations..."
python manage.py makemigrations --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collect static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn (production mode)..."
python manage.py runserver 0.0.0.0:8000
