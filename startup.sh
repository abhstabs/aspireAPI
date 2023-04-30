#!/bin/bash

# Apply database migrations
python manage.py migrate

echo "Creating Admin"

python manage.py createsuperuser --email=$DJANGO_EMAIL --noinput

# Start the application server
python manage.py runserver 0.0.0.0:8000
