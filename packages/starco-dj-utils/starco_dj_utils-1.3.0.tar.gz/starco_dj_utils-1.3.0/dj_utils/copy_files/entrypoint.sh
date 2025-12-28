#!/bin/bash
set -e

echo "Database is ready! Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser if not exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
from  dotenv import load_dotenv;
load_dotenv();
import os;
username=os.environ.get('DJANGO_SUPERUSER_USERNAME');
print(username);
email=os.environ.get('DJANGO_SUPERUSER_EMAIL');
password=os.environ.get('DJANGO_SUPERUSER_PASSWORD');
if username and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username,email,password);
"

echo "Collecting static files..."
python manage.py collectstatic --noinput
exec "$@"
