#!/usr/bin/env bash
# Render (or any host) build command: ./build.sh
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_site
python manage.py apply_watermarks
