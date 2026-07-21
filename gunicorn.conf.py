"""
Mind Link — Gunicorn Configuration
Production server settings for Render deployment.
"""

import os

# Bind to the port Render provides via $PORT, default 10000
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Worker configuration
# PostgreSQL handles concurrent writes safely, so we can use multiple workers.
workers = 2
threads = 4          # Handle concurrent requests within each worker
worker_class = "gthread"

# Timeouts
timeout = 120        # Allow longer requests (e.g. email sending)
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

# Use /dev/shm for worker heartbeat files on Linux (better performance)
worker_tmp_dir = "/dev/shm"
