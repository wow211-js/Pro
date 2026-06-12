#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput

# Download cloudflared binary
CLOUDFLARED_VERSION="2025.4.0"
curl -fsSL "https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-linux-amd64" -o cloudflared
chmod +x cloudflared
mv cloudflared /opt/render/project/bin/cloudflared
