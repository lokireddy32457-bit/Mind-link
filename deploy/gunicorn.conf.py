"""
Mind Link — Gunicorn Configuration (VPS Production)
=====================================================
This file is for the Hostinger KVM 1 VPS running Ubuntu 24.04 LTS.
It is used by the systemd service via:

    gunicorn --config /var/www/mindlink/deploy/gunicorn.conf.py wsgi:app

Architecture:
    Internet → Nginx (port 443/80) → Unix Socket → Gunicorn → Flask → PostgreSQL
"""

import multiprocessing
import os

# ─── Bind ─────────────────────────────────────────────────────────────────────
# Use a Unix socket — Nginx will proxy to it.
# The socket directory must exist and be writable by the deploy user.
# Created by: sudo mkdir -p /run/gunicorn && sudo chown deploy:www-data /run/gunicorn
bind = "unix:/run/gunicorn/mindlink.sock"

# ─── Workers ──────────────────────────────────────────────────────────────────
# Recommended formula: (2 × CPU cores) + 1
# Hostinger KVM 1 has 1 vCPU → 3 workers is a safe default.
# Each worker is an independent Python process.
workers = int(os.environ.get("GUNICORN_WORKERS", 3))

# Threads per worker (gthread worker class).
# Allows handling concurrent requests within a single worker process.
threads = int(os.environ.get("GUNICORN_THREADS", 2))

# Worker class — gthread supports both sync and async-style requests.
worker_class = "gthread"

# ─── Timeouts ─────────────────────────────────────────────────────────────────
# Allow up to 120 seconds per request (accommodates email sending on approve/cancel).
timeout = 120
graceful_timeout = 30
keepalive = 5

# ─── Logging ──────────────────────────────────────────────────────────────────
# Log to stdout/stderr — systemd captures both to the journal.
# View with: journalctl -u mindlink -f
accesslog = "-"
errorlog  = "-"
loglevel  = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# ─── Security ─────────────────────────────────────────────────────────────────
# Trust only the local Nginx reverse proxy.
forwarded_allow_ips = "127.0.0.1"

# Recognise HTTPS from Nginx's X-Forwarded-Proto header.
secure_scheme_headers = {
    "X-Forwarded-Proto": "https"
}

# ─── Performance ──────────────────────────────────────────────────────────────
# Pre-load the Flask application before forking workers.
# Saves memory via copy-on-write; also catches import errors at startup.
preload_app = True

# Use /dev/shm for worker heartbeat temp files (faster than /tmp on Linux).
worker_tmp_dir = "/dev/shm"

# Maximum requests per worker before it is gracefully restarted.
# Prevents memory leaks from accumulating indefinitely.
max_requests = 1000
max_requests_jitter = 100
