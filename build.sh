#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Download OpenPGP.js into static files (avoid CDN dependency)
curl -fsSL "https://cdn.jsdelivr.net/npm/openpgp@5.11.2/dist/openpgp.min.js" -o static/js/openpgp.min.js

# Remove source map reference to prevent whitenoise staticfiles error
sed -i '/^\/\/ # sourceMappingURL=/d' static/js/openpgp.min.js

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py migrate --noinput
