"""
Mind Link — Database Module
SQLite database setup and helper functions for appointments, inquiries, and admin users.
"""

import sqlite3
import os
from datetime import datetime

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mind_link.db')


def get_db():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            preferred_time TEXT NOT NULL,
            service_type TEXT NOT NULL,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
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
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name'],
        data['email'],
        data['phone'],
        data['preferred_date'],
        data['preferred_time'],
        data['service_type'],
        data.get('message', '')
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_appointments(status=None, service_type=None, date_from=None, date_to=None):
    """Retrieve appointments with optional filtering."""
    conn = get_db()
    query = 'SELECT * FROM appointments WHERE 1=1'
    params = []

    if status and status != 'all':
        query += ' AND status = ?'
        params.append(status)

    if service_type and service_type != 'all':
        query += ' AND service_type = ?'
        params.append(service_type)

    if date_from:
        query += ' AND preferred_date >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND preferred_date <= ?'
        params.append(date_to)

    query += ' ORDER BY created_at DESC'

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_appointment_by_id(appointment_id):
    """Retrieve a single appointment by ID."""
    conn = get_db()
    row = conn.execute('SELECT * FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_appointment_status(appointment_id, status):
    """Update the status of an appointment (pending, approved, cancelled)."""
    conn = get_db()
    conn.execute('''
        UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?
    ''', (status, datetime.now().isoformat(), appointment_id))
    conn.commit()
    conn.close()


def get_dashboard_stats():
    """Get aggregate stats for the admin dashboard."""
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'pending'").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'approved'").fetchone()[0]
    cancelled = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'cancelled'").fetchone()[0]
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
    rows = conn.execute(
        "SELECT preferred_time FROM appointments WHERE preferred_date = ? AND status = 'approved'",
        (date,)
    ).fetchall()
    conn.close()
    return [row['preferred_time'] for row in rows]


# ---------------------
# Inquiry Helpers
# ---------------------

def save_inquiry(data):
    """Save a general inquiry. Returns the new row ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inquiries (name, email, subject, message)
        VALUES (?, ?, ?, ?)
    ''', (
        data['name'],
        data['email'],
        data['subject'],
        data['message']
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


# ---------------------
# Admin User Helpers
# ---------------------

def get_admin_user(username):
    """Retrieve an admin user by username."""
    conn = get_db()
    row = conn.execute('SELECT * FROM admin_users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_admin_user(username, password_hash):
    """Create a new admin user."""
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO admin_users (username, password_hash)
            VALUES (?, ?)
        ''', (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()


def admin_user_exists():
    """Check if any admin user exists."""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM admin_users').fetchone()[0]
    conn.close()
    return count > 0
