#!/usr/bin/env bash
# =========================================
# Mind Link — Render Build Script
# =========================================

set -o errexit

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Build complete!"
