#!/usr/bin/env bash
# =========================================
# Mind Link — Render Build Script
# =========================================
# This script runs during every deploy on Render.
# It installs dependencies and initializes the database.

set -o errexit   # Exit on any error

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Initializing database..."
python -c "from database import init_db; from auth import create_default_admin; init_db(); create_default_admin()"

echo "==> Build complete!"
