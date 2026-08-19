# Mind Link — Deployment Quick Reference

This directory contains production deployment configuration files for the
**Hostinger KVM 1 VPS** running **Ubuntu 24.04 LTS**.

> See `docs/DEPLOYMENT.md` in the project root for the **complete step-by-step
> VPS setup guide**, including PostgreSQL setup, UFW, Certbot, and systemd.

---

## Files in This Directory

| File | Purpose |
|---|---|
| `gunicorn.conf.py` | Gunicorn settings for production (Unix socket, 3 workers) |
| `gunicorn.service.example` | systemd unit file template — copy to `/etc/systemd/system/mindlink.service` |
| `nginx.conf.example` | Nginx server block template — copy to `/etc/nginx/sites-available/mindlink` |

---

## Quick Deployment Steps (Summary)

Replace `YOUR_DOMAIN` with your actual domain throughout.

### 1. Copy systemd service file

```bash
sudo cp /var/www/mindlink/deploy/gunicorn.service.example \
        /etc/systemd/system/mindlink.service
sudo systemctl daemon-reload
sudo systemctl enable mindlink
sudo systemctl start mindlink
sudo systemctl status mindlink
```

### 2. Copy Nginx config

```bash
sudo cp /var/www/mindlink/deploy/nginx.conf.example \
        /etc/nginx/sites-available/mindlink

# Edit the file and replace YOUR_DOMAIN with your real domain
sudo nano /etc/nginx/sites-available/mindlink

# Enable the site
sudo ln -s /etc/nginx/sites-available/mindlink \
           /etc/nginx/sites-enabled/mindlink

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Issue SSL certificate

```bash
sudo certbot --nginx -d YOUR_DOMAIN -d www.YOUR_DOMAIN
sudo systemctl reload nginx
```

### 4. Create the environment file (secrets)

```bash
sudo mkdir -p /etc/mindlink
sudo nano /etc/mindlink/mindlink.env
# Paste contents from .env.example and fill in real values

sudo chmod 640 /etc/mindlink/mindlink.env
sudo chown root:deploy /etc/mindlink/mindlink.env
```

### 5. Restart the application

```bash
sudo systemctl restart mindlink
sudo systemctl status mindlink
journalctl -u mindlink -f
```

---

## Verifying the Deployment

```bash
# Check Gunicorn is running
systemctl is-active mindlink

# Check the health endpoint
curl -s http://127.0.0.1/health
# Expected: {"service":"mindlink","status":"ok"}

# Check Nginx
systemctl is-active nginx

# Check PostgreSQL
systemctl is-active postgresql

# View recent application logs
journalctl -u mindlink -n 50 --no-pager

# View Nginx access logs
sudo tail -f /var/log/nginx/mindlink_access.log
```

---

## Important Notes

- **Never put real passwords in these files.** They are in version control.
- All secrets must be in `/etc/mindlink/mindlink.env` on the VPS.
- The `deploy/gunicorn.conf.py` file (NOT the root `gunicorn.conf.py`) is used in production.
- The root `gunicorn.conf.py` is kept for Render.com compatibility.
