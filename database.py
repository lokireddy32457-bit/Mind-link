"""
Mind Link — Database Module
PostgreSQL (Supabase) database setup and helper functions for appointments, inquiries, and admin users.

Connection is configured via the DATABASE_URL environment variable.
On Render, set DATABASE_URL in the Environment tab of the dashboard.
Locally, set it in your .env file.
"""

import os
import psycopg2
import psycopg2.extras
import psycopg2.errorcodes
from datetime import datetime


DATABASE_URL = os.environ.get('DATABASE_URL', '')


def get_db():
    """Get a PostgreSQL connection. SSL is required for Supabase."""
    url = DATABASE_URL
    # Supabase requires SSL — append sslmode if not already present
    if url and 'sslmode' not in url:
        sep = '&' if '?' in url else '?'
        url += sep + 'sslmode=require'
    return psycopg2.connect(url)


def init_db():
    """Initialize database tables if they don't exist."""
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

    conn.commit()
    cursor.close()
    conn.close()


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
