#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput

# Download OpenPGP.js into static files (avoid CDN dependency)
curl -fsSL "https://cdn.jsdelivr.net/npm/openpgp@5.11.2/dist/openpgp.min.js" -o static/js/openpgp.min.js
