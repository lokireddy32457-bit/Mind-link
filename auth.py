"""
Mind Link — Authentication Module
Handles admin login/logout, session management, and password hashing.
"""

from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_admin_user, create_admin_user, admin_user_exists

# Default admin credentials (printed to console on first run)
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'mindlink2026'


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
    Prints credentials to console for the doctor to note and change.
    """
    if not admin_user_exists():
        password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
        create_admin_user(DEFAULT_ADMIN_USERNAME, password_hash)
        print('\n' + '=' * 60)
        print('  MIND LINK — Default Admin Account Created')
        print('=' * 60)
        print(f'  Username: {DEFAULT_ADMIN_USERNAME}')
        print(f'  Password: {DEFAULT_ADMIN_PASSWORD}')
        print('  !!  Please change these credentials after first login!')
        print('  Dashboard: http://localhost:5000/admin/login')
        print('=' * 60 + '\n')
