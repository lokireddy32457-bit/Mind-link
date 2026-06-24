"""
Mind Link — Gunicorn Configuration
Production server settings for Render deployment.
"""

import os

# Bind to the port Render provides via $PORT, default 10000
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Worker configuration
workers = 2          # Keep low for SQLite (avoids write contention)
threads = 4          # Handle concurrent requests per worker
worker_class = "gthread"

# Timeouts
timeout = 120        # Allow longer requests
graceful_timeout = 30

# Logging
accesslog = "-"      # Log to stdout (Render captures this)
errorlog = "-"       # Log to stderr
loglevel = "info"

# Security
forwarded_allow_ips = "*"   # Trust Render's reverse proxy
secure_scheme_headers = {
    "X-Forwarded-Proto": "https"
}

# Preload app for faster worker startup
preload_app = True
