# Mind Link — HELIUM MIND CENTRE

> **Psychiatry & Mental Wellness Clinic Website**
> Flask-based clinic management system for Dr. Vikram Akavaram (MBBS, DPM (Osm), Neuro Psychiatrist) at Helium Mind Centre.

---

## Architecture

```
Internet
   ↓ HTTPS (443)
Nginx                  ← serves static files, SSL termination, HTTP→HTTPS redirect
   ↓ Unix socket
Gunicorn               ← WSGI application server (3 workers, gthread)
   ↓ WSGI
Flask (app.py)         ← application logic, routing, templates
   ↓ psycopg2
PostgreSQL 16          ← primary database (local on VPS)
```

### Key Components

| Component | File | Purpose |
|---|---|---|
| Flask App | `app.py` | Main entry point, all routes |
| WSGI Entry | `wsgi.py` | Gunicorn entry point |
| Database | `database.py` | PostgreSQL connection & all SQL helpers |
| Auth | `auth.py` | Admin session management, password hashing |
| Email | `email_utils.py` | SMTP email notifications to patients |
| VPS Gunicorn Config | `deploy/gunicorn.conf.py` | Production Gunicorn settings |

---

## Features

- **Public Pages**: Home, About (Dr. Akavaram), Services (8 detailed pages), Booking, Contact
- **Appointment Booking**: Server-side validated booking form saved to PostgreSQL
- **Admin Dashboard**: View, filter, approve, cancel appointments; bulk cancel by date
- **Patient Notifications**: Automated HTML emails on appointment approval/cancellation (Gmail SMTP)
- **Site Settings**: Admin can update clinic name and location live via dashboard
- **EmailJS Integration**: Client-side booking notification to clinic inbox
- **Health Endpoint**: `GET /health` → `{"status": "ok"}` for monitoring

---

## Local Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL (or Supabase account) with connection URL

### Installation

```bash
# Clone the repository
git clone https://github.com/lokireddy32457-bit/Mind-link.git
cd Mind-link

# Create a virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and fill in your DATABASE_URL, SMTP credentials, etc.
nano .env
```

### Running Locally

```bash
# Start the development server
python app.py

# The app will be available at http://localhost:5000
```

> **Note:** `app.py` reads `FLASK_DEBUG` from `.env`. Set `FLASK_DEBUG=1` for hot-reload during development.

### Running with Gunicorn (Local Test)

```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

---

## Environment Variables

See [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md) for a complete reference of all required environment variables.

The minimum required variables are:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session signing key |
| `DATABASE_URL` | PostgreSQL connection URI |
| `DATABASE_SSL_MODE` | `require` (Supabase) or `disable` (local Postgres) |
| `SMTP_USER` | Gmail address for patient emails |
| `SMTP_PASSWORD` | Gmail App Password |

---

## Deployment

Full VPS deployment guide: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

Backup strategy: [`docs/BACKUP.md`](docs/BACKUP.md)

Deployment config files: [`deploy/`](deploy/)

---

## Database Schema

Four tables in PostgreSQL:

| Table | Purpose |
|---|---|
| `appointments` | Patient appointment requests |
| `inquiries` | General contact form messages |
| `admin_users` | Admin login credentials (hashed) |
| `site_settings` | Clinic name and location (editable via admin) |

Tables are created automatically on first startup via `init_db()` in `database.py`.

---

## Tech Stack

- **Backend**: Python 3.12, Flask 3.x
- **Database**: PostgreSQL 16 (production), Supabase PostgreSQL (development)
- **Database Driver**: psycopg2-binary
- **WSGI Server**: Gunicorn 22.x (gthread worker)
- **Web Server**: Nginx (reverse proxy + static files)
- **Process Manager**: systemd
- **SSL**: Let's Encrypt / Certbot
- **Email**: Gmail SMTP (smtplib) + EmailJS (client-side)
- **Auth**: werkzeug scrypt password hashing

---

## Security Notes

- All secrets are stored in environment variables — never committed to Git
- Admin passwords are hashed with scrypt via werkzeug
- Session cookies are `HttpOnly`, `SameSite=Lax`, and `Secure` in production
- Database queries use parameterized statements throughout (no SQL injection risk)
- Nginx blocks access to hidden files (`.env`, `.git`, etc.)
