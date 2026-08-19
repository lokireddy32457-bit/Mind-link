"""
Mind Link — Database Module
PostgreSQL database setup and helper functions for appointments, inquiries, and admin users.

Connection is configured via the DATABASE_URL environment variable.
Locally, set it in your .env file.
On the production VPS, set it in /etc/mindlink/mindlink.env (loaded by systemd).

SSL behaviour is controlled by DATABASE_SSL_MODE (default: 'prefer').
  - Set DATABASE_SSL_MODE=require  when connecting to Supabase (cloud PostgreSQL).
  - Set DATABASE_SSL_MODE=disable  when connecting to a local PostgreSQL instance.
  - Set DATABASE_SSL_MODE=prefer   (default) to attempt SSL but fall back gracefully.
If the DATABASE_URL already contains 'sslmode=', DATABASE_SSL_MODE is ignored.
"""

import os
import sys
import time
import psycopg2
import psycopg2.extras
import psycopg2.errorcodes
from datetime import datetime


DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Controls whether SSL is required for the database connection.
# 'prefer'  — attempt SSL, fall back to non-SSL (safe default for local Postgres)
# 'require' — always use SSL (use this for Supabase / cloud databases)
# 'disable' — never use SSL
DATABASE_SSL_MODE = os.environ.get('DATABASE_SSL_MODE', 'prefer')

# Track whether the database is reachable (set after successful init)
_db_available = False


def get_db():
    """Get a PostgreSQL connection.

    SSL mode is controlled by the DATABASE_SSL_MODE environment variable:
      - 'prefer'  (default) — attempts SSL, falls back gracefully (works for local Postgres)
      - 'require' — always SSL (set this for Supabase / cloud databases)
      - 'disable' — no SSL

    If the DATABASE_URL already contains 'sslmode=', DATABASE_SSL_MODE is ignored.
    """
    url = DATABASE_URL
    if not url:
        raise RuntimeError(
            'DATABASE_URL is not set. '
            'Set it in your .env file (local) or /etc/mindlink/mindlink.env (VPS production).'
        )
    # Only append sslmode if the URL does not already specify one
    if 'sslmode' not in url:
        sep = '&' if '?' in url else '?'
        url += sep + f'sslmode={DATABASE_SSL_MODE}'
    try:
        return psycopg2.connect(url, connect_timeout=10)
    except psycopg2.OperationalError as exc:
        error_msg = str(exc)
        print('\n' + '=' * 60, file=sys.stderr)
        print('  DATABASE CONNECTION ERROR', file=sys.stderr)
        print('=' * 60, file=sys.stderr)
        if 'ENOTFOUND' in error_msg or 'tenant' in error_msg:
            print('  The database host could not be found.', file=sys.stderr)
            print('  Possible causes:', file=sys.stderr)
            print('    1. If using Supabase: the project may be PAUSED (free-tier auto-pause).', file=sys.stderr)
            print('       → Go to https://supabase.com/dashboard and click "Restore".', file=sys.stderr)
            print('    2. The host in DATABASE_URL is incorrect.', file=sys.stderr)
            print('       → Check DATABASE_URL in your .env or environment config.', file=sys.stderr)
        elif 'password authentication' in error_msg.lower():
            print('  Authentication failed — the database password is incorrect.', file=sys.stderr)
            print('  → Update DATABASE_URL in your .env file with the correct password.', file=sys.stderr)
        elif 'ssl' in error_msg.lower():
            print('  SSL connection error.', file=sys.stderr)
            print('  → For local PostgreSQL, set DATABASE_SSL_MODE=disable in your .env.', file=sys.stderr)
            print('  → For Supabase / cloud databases, set DATABASE_SSL_MODE=require.', file=sys.stderr)
        else:
            print(f'  {error_msg}', file=sys.stderr)
        print('=' * 60 + '\n', file=sys.stderr)
        raise


def init_db():
    """Initialize database tables if they don't exist.

    Retries once after a short delay, then allows the app to start
    without a database so that public (non-DB) pages still work.
    """
    global _db_available

    for attempt in range(1, 3):  # two attempts
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id        BIGSERIAL PRIMARY KEY,
                    name      TEXT NOT NULL,
                    email     TEXT NOT NULL,
                    phone     TEXT NOT NULL,
                    preferred_date TEXT NOT NULL,
                    preferred_time TEXT NOT NULL,
                    service_type   TEXT NOT NULL,
                    message   TEXT,
                    status    TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inquiries (
                    id         BIGSERIAL PRIMARY KEY,
                    name       TEXT NOT NULL,
                    email      TEXT NOT NULL,
                    subject    TEXT NOT NULL,
                    message    TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id            BIGSERIAL PRIMARY KEY,
                    username      TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_settings (
                    key        TEXT PRIMARY KEY,
                    value      TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Seed default settings on first boot
            cursor.execute('''
                INSERT INTO site_settings (key, value)
                VALUES
                    ('site_name',     'HELIUM MIND CENTRE'),
                    ('site_location', '123 Wellness Avenue, Suite 200, Springfield, IL 62701')
                ON CONFLICT (key) DO NOTHING
            ''')

            conn.commit()
            cursor.close()
            conn.close()
            _db_available = True
            print('[Database] Connected to PostgreSQL successfully.', file=sys.stderr)
            return  # success
        except Exception as exc:
            if attempt < 2:
                print(f'[Database] Connection attempt {attempt} failed, retrying in 3s…',
                      file=sys.stderr)
                time.sleep(3)
            else:
                print(
                    '\n⚠️  Could not connect to the database after 2 attempts.\n'
                    '   The app will start, but features requiring the database\n'
                    '   (booking, admin, contact form) will not work until the\n'
                    '   database is reachable.\n',
                    file=sys.stderr,
                )


# ---------------------
# Appointment Helpers
# ---------------------

def save_appointment(data):
    """Save a new appointment request. Returns the new row ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (name, email, phone, preferred_date, preferred_time, service_type, message)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (
        data['name'],
        data['email'],
        data['phone'],
        data['preferred_date'],
        data['preferred_time'],
        data['service_type'],
        data.get('message', '')
    ))
    row_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return row_id


def get_appointments(status=None, service_type=None, date_from=None, date_to=None):
    """Retrieve appointments with optional filtering."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = 'SELECT * FROM appointments WHERE 1=1'
    params = []

    if status and status != 'all':
        query += ' AND status = %s'
        params.append(status)

    if service_type and service_type != 'all':
        query += ' AND service_type = %s'
        params.append(service_type)

    if date_from:
        query += ' AND preferred_date >= %s'
        params.append(date_from)

    if date_to:
        query += ' AND preferred_date <= %s'
        params.append(date_to)

    query += ' ORDER BY created_at DESC'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]


def get_appointment_by_id(appointment_id):
    """Retrieve a single appointment by ID."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM appointments WHERE id = %s', (appointment_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def update_appointment_status(appointment_id, status):
    """Update the status of an appointment (pending, approved, cancelled)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE appointments SET status = %s, updated_at = %s WHERE id = %s
    ''', (status, datetime.now().isoformat(), appointment_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_dashboard_stats():
    """Get aggregate stats for the admin dashboard."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM appointments')
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'approved'")
    approved = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'cancelled'")
    cancelled = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return {
        'total': total,
        'pending': pending,
        'approved': approved,
        'cancelled': cancelled
    }


def cancel_appointments_by_date(date):
    """Cancel all pending and approved appointments on a given date.

    Returns a list of dicts with {id, name, email} for each cancelled appointment
    so the caller can optionally send notification emails.
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        """
        UPDATE appointments
        SET status = 'cancelled', updated_at = %s
        WHERE preferred_date = %s
          AND status IN ('pending', 'approved')
        RETURNING id, name, email
        """,
        (datetime.now().isoformat(), date)
    )
    affected = [dict(row) for row in cursor.fetchall()]
    conn.commit()
    cursor.close()
    conn.close()
    return affected


def get_booked_slots(date):
    """Return a list of time strings that are already approved for a given date."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT preferred_time FROM appointments WHERE preferred_date = %s AND status = 'approved'",
        (date,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]


# ---------------------
# Inquiry Helpers
# ---------------------

def save_inquiry(data):
    """Save a general inquiry. Returns the new row ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inquiries (name, email, subject, message)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (
        data['name'],
        data['email'],
        data['subject'],
        data['message']
    ))
    row_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return row_id


# ---------------------
# Admin User Helpers
# ---------------------

def get_admin_user(username):
    """Retrieve an admin user by username."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM admin_users WHERE username = %s', (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def create_admin_user(username, password_hash):
    """Create a new admin user."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO admin_users (username, password_hash)
            VALUES (%s, %s)
        ''', (username, password_hash))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False  # Username already exists
    finally:
        cursor.close()
        conn.close()


def admin_user_exists():
    """Check if any admin user exists."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM admin_users')
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0


# ---------------------
# Site Settings Helpers
# ---------------------

_SETTING_DEFAULTS = {
    'site_name':     'HELIUM MIND CENTRE',
    'site_location': '123 Wellness Avenue, Suite 200, Springfield, IL 62701',
}


def get_site_settings():
    """Return all site settings as a dict.  Falls back to hardcoded defaults
    if the database is unavailable so templates never break."""
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT key, value FROM site_settings')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        settings = dict(_SETTING_DEFAULTS)  # start with defaults
        for row in rows:
            settings[row['key']] = row['value']
        return settings
    except Exception:
        return dict(_SETTING_DEFAULTS)


def update_site_setting(key, value):
    """Upsert a single site setting. Returns True on success."""
    if key not in _SETTING_DEFAULTS:
        raise ValueError(f'Unknown setting key: {key!r}')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO site_settings (key, value, updated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value,
                updated_at = EXCLUDED.updated_at
        ''',
        (key, value, datetime.now().isoformat())
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True
