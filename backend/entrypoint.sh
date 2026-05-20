#!/bin/sh

set -e

echo "Waiting for database..."
python -c "
import time
import psycopg2
import os

while True:
    try:
        conn = psycopg2.connect(
            dbname=os.environ['POSTGRES_DB'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['POSTGRES_HOST'],
            port=os.environ.get('POSTGRES_PORT', '5432')
        )
        conn.close()
        print('Database is ready!')
        break
    except psycopg2.OperationalError:
        print('Database not ready, waiting 2 seconds...')
        time.sleep(2)
"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating default superuser..."
python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@mahalla.uz')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created successfully.")
else:
    print(f"Superuser '{username}' already exists.")
PYEOF

echo "Entrypoint completed successfully."
