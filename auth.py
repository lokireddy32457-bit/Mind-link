"""
Mind Link — Authentication Module
Handles admin login/logout, session management, and password hashing.
"""

import os
import sys
from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_admin_user, create_admin_user, admin_user_exists

# Default admin credentials — used only on first boot if no admin user exists.
# Override via the ADMIN_DEFAULT_PASSWORD environment variable.
# IMPORTANT: Change the admin password immediately after first login.
DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_DEFAULT_USERNAME', 'admin')
DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_DEFAULT_PASSWORD', 'mindlink2026')


def hash_password(password):
    """Hash a password using werkzeug's secure hashing."""
    return generate_password_hash(password, method='scrypt')


def verify_password(password, password_hash):
    """Verify a password against its hash."""
    return check_password_hash(password_hash, password)


def login_required(f):
    """Decorator to protect admin routes — redirects to login if not authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access the dashboard.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate_admin(username, password):
    """
    Authenticate an admin user.
    Returns True if credentials are valid, False otherwise.
    """
    user = get_admin_user(username)
    if user and verify_password(password, user['password_hash']):
        return True
    return False


def create_default_admin():
    """
    Create the default admin account if no admin users exist.
    Credentials are printed to stderr on first boot only.

    If the database is unreachable, a warning is logged and the app
    continues to start (public pages will still work).
    """
    try:
        if not admin_user_exists():
            password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
            create_admin_user(DEFAULT_ADMIN_USERNAME, password_hash)

            site_url = os.environ.get('SITE_URL', 'http://localhost:5000')
            print('\n' + '=' * 60, file=sys.stderr)
            print('  MIND LINK — Default Admin Account Created', file=sys.stderr)
            print('=' * 60, file=sys.stderr)
            print(f'  Username : {DEFAULT_ADMIN_USERNAME}', file=sys.stderr)
            print(f'  Password : {DEFAULT_ADMIN_PASSWORD}', file=sys.stderr)
            print('  !! Change these credentials after first login!', file=sys.stderr)
            print(f'  Dashboard: {site_url}/admin/login', file=sys.stderr)
            print('=' * 60 + '\n', file=sys.stderr)
    except Exception:
        print(
            '\n⚠️  Could not create default admin — database is unavailable.\n'
            '   Admin login will not work until the database is reachable.\n',
            file=sys.stderr,
        )
