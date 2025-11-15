FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    build-essential pkg-config \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Bu port faqat image ichida "expose" bo‘ladi, Railway baribir $PORT beradi
EXPOSE 8000

# Muhim qism: collectstatic + migrate + superuser + gunicorn
CMD sh -c "
  python manage.py collectstatic --noinput && \
  python manage.py makemigrations --noinput && \
  python manage.py migrate --noinput && \
  python manage.py shell -c \"from django.contrib.auth import get_user_model; User=get_user_model(); email='admin@admin.com'; password='admin'; u=User.objects.filter(email=email).first(); print('Superuser already exists' if u else 'Creating superuser'); u or User.objects.create_superuser(email=email, password=password)\" && \
  gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
"
