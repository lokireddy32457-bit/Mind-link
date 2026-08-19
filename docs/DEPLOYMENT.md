# Mind Link — VPS Deployment Guide

**Target:** Hostinger KVM 1 VPS — Ubuntu 24.04 LTS — Mumbai, India  
**Stack:** Nginx → Gunicorn → Flask → PostgreSQL 16  
**Domain:** Managed via GoDaddy DNS (DNS changes are a separate manual step)

> [!IMPORTANT]
> This document does NOT assume you have already connected to the VPS.
> All commands in this guide run **on the VPS** via SSH unless stated otherwise.
> Do NOT run these commands on your local Windows machine.

---

## Table of Contents

1. [Initial Server Access](#1-initial-server-access)
2. [System Updates & Core Tools](#2-system-updates--core-tools)
3. [UFW Firewall](#3-ufw-firewall)
4. [Create Deployment User](#4-create-deployment-user)
5. [Python Setup](#5-python-setup)
6. [PostgreSQL 16 Setup](#6-postgresql-16-setup)
7. [Application Deployment](#7-application-deployment)
8. [Environment Configuration (Secrets)](#8-environment-configuration-secrets)
9. [Gunicorn Setup (systemd)](#9-gunicorn-setup-systemd)
10. [Nginx Setup](#10-nginx-setup)
11. [HTTPS with Let's Encrypt](#11-https-with-lets-encrypt)
12. [Database Migration from Supabase](#12-database-migration-from-supabase)
13. [Verification](#13-verification)
14. [Rollback Plan](#14-rollback-plan)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Initial Server Access

SSH into your VPS as root using the credentials from Hostinger:

```bash
ssh root@YOUR_SERVER_IP
```

Immediately change the root password if you haven't:

```bash
passwd
```

---

## 2. System Updates & Core Tools

```bash
apt update && apt upgrade -y
apt install -y git curl wget unzip nano ufw fail2ban build-essential \
               libpq-dev python3-dev python3-pip python3-venv
```

---

## 3. UFW Firewall

```bash
# Set default policy: deny incoming, allow outgoing
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (critical — do this FIRST before enabling UFW)
ufw allow OpenSSH

# Allow HTTP and HTTPS for Nginx
ufw allow 'Nginx Full'

# Enable UFW
ufw enable

# Verify
ufw status verbose
```

> [!CAUTION]
> Always allow SSH **before** enabling UFW. Locking yourself out requires Hostinger console access.

---

## 4. Create Deployment User

```bash
# Create a non-root user for running the application
adduser deploy

# Add to sudo group (for maintenance operations)
usermod -aG sudo deploy

# Add to www-data group (so Nginx can read the Unix socket)
usermod -aG www-data deploy

# Copy SSH keys so you can log in as deploy directly
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

From now on, prefer SSH as `deploy` rather than root:

```bash
ssh deploy@YOUR_SERVER_IP
```

---

## 5. Python Setup

Ubuntu 24.04 ships with Python 3.12. Verify:

```bash
python3 --version
# Expected: Python 3.12.x
```

---

## 6. PostgreSQL 16 Setup

```bash
# Install PostgreSQL 16
apt install -y postgresql postgresql-contrib

# Start and enable
systemctl start postgresql
systemctl enable postgresql

# Verify
systemctl status postgresql
```

### Create Database and User

```bash
# Connect as the postgres superuser
sudo -u postgres psql

-- Inside psql:
CREATE DATABASE mindlink_db;
CREATE USER mindlink_user WITH ENCRYPTED PASSWORD 'CHOOSE_A_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE mindlink_db TO mindlink_user;

-- For PostgreSQL 15+ also grant schema privileges:
\c mindlink_db
GRANT ALL ON SCHEMA public TO mindlink_user;

\q
```

> [!CAUTION]
> Replace `CHOOSE_A_STRONG_PASSWORD` with a real, random password (minimum 20 characters).
> Generate one with: `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`
> Save this password — you'll need it in the environment file.

### Configure PostgreSQL for Local Connections Only

Edit `/etc/postgresql/16/main/pg_hba.conf` to ensure local connections use password auth:

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Ensure these lines exist (they usually do by default):

```
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

Test the connection:

```bash
psql -U mindlink_user -h 127.0.0.1 -d mindlink_db
# Enter password when prompted
\q
```

---

## 7. Application Deployment

### Create Web Directory

```bash
sudo mkdir -p /var/www/mindlink
sudo chown deploy:www-data /var/www/mindlink
sudo chmod 750 /var/www/mindlink
```

### Clone the Repository

```bash
cd /var/www
sudo -u deploy git clone https://github.com/lokireddy32457-bit/Mind-link.git mindlink
cd mindlink
```

### Create Python Virtual Environment

```bash
sudo -u deploy python3 -m venv /var/www/mindlink/venv
sudo -u deploy /var/www/mindlink/venv/bin/pip install --upgrade pip
sudo -u deploy /var/www/mindlink/venv/bin/pip install -r requirements.txt
```

---

## 8. Environment Configuration (Secrets)

Create the secrets file on the VPS. **This file must never be in Git.**

```bash
sudo mkdir -p /etc/mindlink
sudo nano /etc/mindlink/mindlink.env
```

Paste and fill in the following (no quotes around values):

```ini
SECRET_KEY=paste-a-64-char-random-hex-here
FLASK_ENV=production
FLASK_DEBUG=0
SITE_URL=https://YOUR_DOMAIN

DATABASE_URL=postgresql://mindlink_user:YOUR_DB_PASSWORD@127.0.0.1:5432/mindlink_db
DATABASE_SSL_MODE=disable

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-clinic-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
FROM_NAME=Mind Link Psychiatry Clinic
FROM_EMAIL=your-clinic-email@gmail.com

ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=choose-a-strong-first-login-password
```

Secure the file:

```bash
sudo chmod 640 /etc/mindlink/mindlink.env
sudo chown root:deploy /etc/mindlink/mindlink.env
```

Generate a strong SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 9. Gunicorn Setup (systemd)

### Install the systemd Service

```bash
sudo cp /var/www/mindlink/deploy/gunicorn.service.example \
        /etc/systemd/system/mindlink.service

sudo systemctl daemon-reload
sudo systemctl enable mindlink
sudo systemctl start mindlink
sudo systemctl status mindlink
```

### Verify Gunicorn is Running

```bash
# Check the Unix socket was created
ls -la /run/gunicorn/mindlink.sock

# Check logs
journalctl -u mindlink -n 50 --no-pager
```

You should see `[Database] Connected to PostgreSQL successfully.` in the logs on first start. The database tables will be created automatically by `init_db()`.

---

## 10. Nginx Setup

### Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
```

### Configure the Site

```bash
sudo cp /var/www/mindlink/deploy/nginx.conf.example \
        /etc/nginx/sites-available/mindlink

# Edit the file — replace YOUR_DOMAIN with your real domain
sudo nano /etc/nginx/sites-available/mindlink

# Enable the site
sudo ln -s /etc/nginx/sites-available/mindlink \
           /etc/nginx/sites-enabled/mindlink

# Remove the default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## 11. HTTPS with Let's Encrypt

### Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Issue Certificate

> [!IMPORTANT]
> Your DNS must be pointing to the VPS IP **before** running certbot.
> DNS propagation can take up to 48 hours. Verify with: `nslookup YOUR_DOMAIN`

```bash
sudo certbot --nginx -d YOUR_DOMAIN -d www.YOUR_DOMAIN
```

Follow the prompts. Certbot will:
1. Obtain the certificate from Let's Encrypt
2. Automatically modify your Nginx config with the correct cert paths
3. Set up auto-renewal

### Verify Auto-Renewal

```bash
sudo certbot renew --dry-run
```

---

## 12. Database Migration from Supabase

> [!CAUTION]
> **Do NOT delete Supabase data until the migration is fully verified.**
> Keep Supabase as a backup until you are confident the VPS database is correct.

### Step 1 — Export from Supabase (Run Locally on Windows)

Open Command Prompt or PowerShell:

```powershell
# Install pg_dump if needed — part of PostgreSQL client tools
# Download from https://www.postgresql.org/download/windows/ and install

# Export full schema + data from Supabase
pg_dump "postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres?sslmode=require" `
    --no-owner `
    --no-acl `
    --format=plain `
    --file=mindlink_supabase_backup.sql

# Verify the file was created
Get-Item mindlink_supabase_backup.sql
```

> Replace the connection string with the real Supabase URI from your `.env` file.

### Step 2 — Review the Export

Open `mindlink_supabase_backup.sql` and verify it contains:
- `CREATE TABLE appointments`
- `CREATE TABLE inquiries`
- `CREATE TABLE admin_users`
- `CREATE TABLE site_settings`
- `INSERT` statements with your actual data

### Step 3 — Transfer to VPS

```powershell
# From Windows PowerShell / Command Prompt
scp mindlink_supabase_backup.sql deploy@YOUR_SERVER_IP:/tmp/mindlink_supabase_backup.sql
```

### Step 4 — Import on VPS

```bash
# SSH into VPS
ssh deploy@YOUR_SERVER_IP

# Import into the new PostgreSQL 16 database
psql -U mindlink_user -h 127.0.0.1 -d mindlink_db \
     -f /tmp/mindlink_supabase_backup.sql

# Clean up the temp file after import
rm /tmp/mindlink_supabase_backup.sql
```

### Step 5 — Schema Verification

```bash
psql -U mindlink_user -h 127.0.0.1 -d mindlink_db
```

Inside psql:

```sql
-- List all tables
\dt

-- Verify expected tables exist:
-- appointments, inquiries, admin_users, site_settings

-- Check row counts
SELECT 'appointments' AS table_name, COUNT(*) FROM appointments
UNION ALL
SELECT 'inquiries', COUNT(*) FROM inquiries
UNION ALL
SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL
SELECT 'site_settings', COUNT(*) FROM site_settings;

-- Check sequences are correct (avoid duplicate ID conflicts)
SELECT last_value FROM appointments_id_seq;
SELECT last_value FROM inquiries_id_seq;
SELECT last_value FROM admin_users_id_seq;

\q
```

### Step 6 — Data Verification

Compare with Supabase:
- Row counts in each table should match
- Admin users should exist with correct usernames
- Site settings should show clinic name and location

### Step 7 — Application Testing

```bash
# Restart the application
sudo systemctl restart mindlink

# Check it connects to the local database
journalctl -u mindlink -n 30 --no-pager
# Look for: [Database] Connected to PostgreSQL successfully.

# Test the health endpoint
curl -s http://127.0.0.1/health
# Expected: {"service":"mindlink","status":"ok"}
```

Then test via browser:
- Visit `https://YOUR_DOMAIN/` — home page loads
- Visit `https://YOUR_DOMAIN/booking` — booking form works
- Visit `https://YOUR_DOMAIN/admin/login` — admin login works
- Submit a test booking — verify it appears in the admin dashboard

### Step 8 — Rollback Plan

If something goes wrong during or after migration:

**Option A — Revert to Supabase:**
```bash
# SSH into VPS
sudo nano /etc/mindlink/mindlink.env

# Change DATABASE_URL back to Supabase URI
# Change DATABASE_SSL_MODE=require

# Restart the application
sudo systemctl restart mindlink
```

**Option B — Restore from dump:**
```bash
# Drop and recreate the local database
sudo -u postgres psql -c "DROP DATABASE mindlink_db;"
sudo -u postgres psql -c "CREATE DATABASE mindlink_db OWNER mindlink_user;"
sudo -u postgres psql -c "GRANT ALL ON DATABASE mindlink_db TO mindlink_user;"

# Re-import
psql -U mindlink_user -h 127.0.0.1 -d mindlink_db -f /tmp/mindlink_supabase_backup.sql
```

---

## 13. Verification

Final checklist after complete deployment:

```bash
# All services running
systemctl is-active postgresql   # active
systemctl is-active mindlink     # active
systemctl is-active nginx        # active

# Health check
curl -s https://YOUR_DOMAIN/health
# {"service":"mindlink","status":"ok"}

# SSL certificate valid
curl -sI https://YOUR_DOMAIN | grep -i strict
# Strict-Transport-Security: max-age=63072000; includeSubDomains; preload

# Application logs clean (no errors)
journalctl -u mindlink -n 100 --no-pager | grep -i error

# Nginx logs
sudo tail -20 /var/log/nginx/mindlink_access.log
sudo tail -20 /var/log/nginx/mindlink_error.log
```

---

## 14. Rollback Plan

If the deployment fails at any point:

1. **Application not starting**: Check `journalctl -u mindlink -n 50` for errors.
2. **Database connection failure**: Verify `DATABASE_URL` and `DATABASE_SSL_MODE` in `/etc/mindlink/mindlink.env`.
3. **Nginx 502 Bad Gateway**: Gunicorn socket may not exist — check `ls /run/gunicorn/`.
4. **Full rollback to Render/Supabase**: Update DNS to point back to Render, update `DATABASE_URL` in env file.

---

## 15. Troubleshooting

### Application won't start

```bash
journalctl -u mindlink -f
# Look for: ImportError, ModuleNotFoundError, DATABASE_URL not set
```

### 502 Bad Gateway

```bash
# Is Gunicorn running?
systemctl status mindlink

# Does the socket exist?
ls -la /run/gunicorn/mindlink.sock

# Restart Gunicorn
sudo systemctl restart mindlink

# Check Nginx error log
sudo tail -50 /var/log/nginx/mindlink_error.log
```

### Database connection refused

```bash
# Is PostgreSQL running?
systemctl status postgresql

# Can you connect manually?
psql -U mindlink_user -h 127.0.0.1 -d mindlink_db

# Check pg_hba.conf allows local connections
sudo cat /etc/postgresql/16/main/pg_hba.conf | grep -v "^#" | grep -v "^$"
```

### SSL certificate errors

```bash
# Check certificate status
sudo certbot certificates

# Renew if needed
sudo certbot renew

# Check expiry
openssl s_client -connect YOUR_DOMAIN:443 -servername YOUR_DOMAIN 2>/dev/null | openssl x509 -noout -dates
```

### Static files not loading

```bash
# Check Nginx config static path matches actual path
sudo nginx -t
ls -la /var/www/mindlink/static/
```
