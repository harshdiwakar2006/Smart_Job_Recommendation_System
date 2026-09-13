#!/bin/bash

# Upgrade pip and install packages in Vercel's managed environment
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt --break-system-packages

# Collect static files
python3 manage.py collectstatic --noinput --clear