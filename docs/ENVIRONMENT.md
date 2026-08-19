# Mind Link — Environment Variables Reference

This document explains every environment variable used by the application.

> [!IMPORTANT]
> **Never put real secret values in this file, in `.env.example`, or anywhere in the Git repository.**
> Real values belong in `.env` (local development) or `/etc/mindlink/mindlink.env` (VPS production).

---

## Quick Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ Required | random (insecure) | Flask session signing key |
| `FLASK_ENV` | Recommended | `development` | `development` or `production` |
| `FLASK_DEBUG` | Recommended | `0` | `0` = disabled, `1` = enabled |
| `SITE_URL` | Optional | `http://localhost:5000` | Base URL for first-boot admin message |
| `DATABASE_URL` | ✅ Required | — | Full PostgreSQL connection URI |
| `DATABASE_SSL_MODE` | Recommended | `prefer` | SSL mode for database connection |
| `SMTP_HOST` | Optional | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | Optional | `587` | SMTP server port |
| `SMTP_USER` | Optional | — | Email address (no email = notifications disabled) |
| `SMTP_PASSWORD` | Optional | — | Gmail App Password |
| `FROM_NAME` | Optional | `Mind Link Psychiatry Clinic` | Display name in emails |
| `FROM_EMAIL` | Optional | Same as `SMTP_USER` | Sender email address |
| `ADMIN_DEFAULT_USERNAME` | Optional | `admin` | First-boot admin username |
| `ADMIN_DEFAULT_PASSWORD` | Optional | `mindlink2026` | First-boot admin password |

---

## Detailed Reference

### `SECRET_KEY`

**Required:** Yes  
**Default:** A new random value generated each startup (sessions are invalidated on restart)

Flask uses this key to cryptographically sign session cookies. If this is not set, a new random value is generated on every application restart — this means all active admin sessions are invalidated on every restart.

**In production: always set an explicit, strong value.**

```bash
# Generate a secure key:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Example value (placeholder): `SECRET_KEY=a1b2c3d4e5f6...64hexchars`

---

### `FLASK_ENV`

**Required:** Recommended  
**Default:** `development`  
**Values:** `development` | `production`

Controls Flask's environment mode. Setting `production` enables:
- Secure session cookies (`SESSION_COOKIE_SECURE=True` — requires HTTPS)
- Disables debug error pages (no stack traces exposed to users)

```ini
FLASK_ENV=production   # VPS production
FLASK_ENV=development  # local development
```

---

### `FLASK_DEBUG`

**Required:** Recommended  
**Default:** `0`  
**Values:** `0` (disabled) | `1` (enabled)

Controls Flask debug mode when running `python app.py` directly.
**Never set to `1` in production.** Debug mode exposes an interactive debugger in the browser.

```ini
FLASK_DEBUG=0   # production
FLASK_DEBUG=1   # local development only
```

> Gunicorn ignores `FLASK_DEBUG` — debug mode only applies to `python app.py`.

---

### `SITE_URL`

**Required:** No  
**Default:** `http://localhost:5000`

Used in the first-boot console message that prints the admin login URL.
Has no effect on the running application after the admin user is created.

```ini
SITE_URL=https://yourdomain.com   # production
SITE_URL=http://localhost:5000    # local
```

---

### `DATABASE_URL`

**Required:** Yes  
**Format:** `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`

The full PostgreSQL connection URI.

```ini
# Supabase (cloud) — development:
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres

# Local PostgreSQL 16 on VPS — production:
DATABASE_URL=postgresql://mindlink_user:[PASSWORD]@127.0.0.1:5432/mindlink_db
```

> [!WARNING]
> Never commit a real `DATABASE_URL` containing a password to Git.

---

### `DATABASE_SSL_MODE`

**Required:** Recommended  
**Default:** `prefer`  
**Values:** `require` | `disable` | `prefer` | `allow` | `verify-ca` | `verify-full`

Controls whether SSL is used for the database connection.

| Value | When to Use |
|---|---|
| `require` | Supabase / cloud databases (always require SSL) |
| `disable` | Local PostgreSQL on the same VPS (no SSL needed) |
| `prefer` | Default — tries SSL, falls back gracefully |

> If `DATABASE_URL` already contains `sslmode=`, this variable is ignored.

```ini
DATABASE_SSL_MODE=require   # for Supabase
DATABASE_SSL_MODE=disable   # for local VPS PostgreSQL
```

---

### `SMTP_HOST`

**Required:** No (email is optional)  
**Default:** `smtp.gmail.com`

SMTP server hostname. Gmail is the recommended provider.

```ini
SMTP_HOST=smtp.gmail.com
```

---

### `SMTP_PORT`

**Required:** No  
**Default:** `587`

SMTP server port.

| Port | Protocol |
|---|---|
| `587` | STARTTLS (recommended) |
| `465` | SSL/TLS |

```ini
SMTP_PORT=587
```

---

### `SMTP_USER`

**Required:** No (email disabled if missing)  
**Example:** `your-clinic-email@gmail.com`

The Gmail address used to send appointment notifications.  
If this is empty, email notifications are silently skipped — appointments still save to the database.

---

### `SMTP_PASSWORD`

**Required:** No (email disabled if missing)  
**Example:** Gmail App Password (16 characters)

**This must be a Gmail App Password, not your regular Gmail password.**

To create an App Password:
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. 2-Step Verification must be enabled
3. Select "Mail" and "Other (Custom name)" → enter "Mind Link"
4. Copy the 16-character password

> [!CAUTION]
> Never commit this value to Git. Store it only in `.env` or `/etc/mindlink/mindlink.env`.

---

### `FROM_NAME`

**Required:** No  
**Default:** `Mind Link Psychiatry Clinic`

The display name shown in the "From" field of patient notification emails.

```ini
FROM_NAME=Helium Mind Centre
```

---

### `FROM_EMAIL`

**Required:** No  
**Default:** Same as `SMTP_USER`

The email address shown in the "From" field. For Gmail, this must match `SMTP_USER`.

---

### `ADMIN_DEFAULT_USERNAME`

**Required:** No  
**Default:** `admin`

The username for the default admin account created on first boot (only if no admin exists).

> Change the password immediately after first login. This variable has no effect once an admin exists.

---

### `ADMIN_DEFAULT_PASSWORD`

**Required:** No  
**Default:** `mindlink2026`

The password for the default admin account created on first boot.

> [!WARNING]
> Set this to a strong value in production. Even though it is only used once (first boot), a weak default password is a security risk if the admin user hasn't been changed yet.
> After the admin password has been changed via the dashboard, this variable has no further effect.

---

## Example Configurations

### Local Development (Supabase)

```ini
SECRET_KEY=dev-secret-not-for-production
FLASK_ENV=development
FLASK_DEBUG=1
SITE_URL=http://localhost:5000
DATABASE_URL=postgresql://postgres:[SUPABASE-PASSWORD]@db.xxxx.supabase.co:5432/postgres
DATABASE_SSL_MODE=require
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourname@gmail.com
SMTP_PASSWORD=your-app-password
FROM_NAME=Mind Link Clinic (Dev)
FROM_EMAIL=yourname@gmail.com
```

### VPS Production (Local PostgreSQL)

```ini
SECRET_KEY=64-char-random-hex-value
FLASK_ENV=production
FLASK_DEBUG=0
SITE_URL=https://yourdomain.com
DATABASE_URL=postgresql://mindlink_user:[STRONG-PASSWORD]@127.0.0.1:5432/mindlink_db
DATABASE_SSL_MODE=disable
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=clinic@gmail.com
SMTP_PASSWORD=gmail-app-password
FROM_NAME=Helium Mind Centre
FROM_EMAIL=clinic@gmail.com
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=strong-first-login-password
```
