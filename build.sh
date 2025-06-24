#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

python manage.py migrate
python manage.py makemigrations core
python manage.py migrate
# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
# Create superuser if it doesn't exist
python manage.py shell <<EOF
from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "lautaroaray57@gmail.com", "admin1234")
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")
EOF