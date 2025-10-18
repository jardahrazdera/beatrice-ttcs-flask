"""
Authentication handler for web interface.

This module provides basic authentication functionality including
password hashing, session management, and login decorators.
"""

import os
from functools import wraps
from flask import session, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash


# Default credentials (should be changed in production)
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD_HASH = generate_password_hash('admin123')

# Super admin password for sensitive operations
# Set via environment variable: SUPER_ADMIN_PASSWORD or SUPER_ADMIN_PASSWORD_HASH
# Default: 'superadmin123' (CHANGE IN PRODUCTION!)
SUPER_ADMIN_PASSWORD_HASH = os.environ.get(
    'SUPER_ADMIN_PASSWORD_HASH',
    generate_password_hash(os.environ.get('SUPER_ADMIN_PASSWORD', 'superadmin123'))
)

# In production, store credentials in environment variables or secure config
CREDENTIALS = {
    DEFAULT_USERNAME: DEFAULT_PASSWORD_HASH
}


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt via werkzeug.security.

    Args:
        password: Plain text password

    Returns:
        Bcrypt password hash
    """
    return generate_password_hash(password)


def check_auth(username: str, password: str) -> bool:
    """
    Verify username and password using secure bcrypt comparison.

    Args:
        username: Username to check
        password: Plain text password

    Returns:
        True if credentials are valid, False otherwise
    """
    if username not in CREDENTIALS:
        return False

    return check_password_hash(CREDENTIALS[username], password)


def requires_auth(f):
    """
    Decorator for routes that require authentication.

    Usage:
        @app.route('/protected')
        @requires_auth
        def protected_route():
            return 'Protected content'
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated


def add_user(username: str, password: str) -> bool:
    """
    Add new user credentials.

    Args:
        username: New username
        password: Plain text password

    Returns:
        True if user added successfully
    """
    if username in CREDENTIALS:
        return False

    CREDENTIALS[username] = hash_password(password)
    return True


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """
    Change user password.

    Args:
        username: Username
        old_password: Current password (plain text)
        new_password: New password (plain text)

    Returns:
        True if password changed successfully
    """
    if not check_auth(username, old_password):
        return False

    CREDENTIALS[username] = hash_password(new_password)
    return True


def check_super_admin_auth(password: str) -> bool:
    """
    Verify super admin password for sensitive operations using secure bcrypt comparison.

    Args:
        password: Plain text super admin password

    Returns:
        True if password is valid, False otherwise
    """
    if not password:
        return False

    return check_password_hash(SUPER_ADMIN_PASSWORD_HASH, password)


def requires_super_admin(f):
    """
    Decorator for routes that require super admin authentication.
    Expects 'super_admin_password' in request JSON body.

    Usage:
        @app.route('/protected')
        @requires_auth
        @requires_super_admin
        def protected_route():
            return 'Protected content'
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is authenticated first
        if not session.get('authenticated'):
            return {'error': 'Authentication required'}, 401

        # Check super admin password
        data = request.get_json()
        if not data or not data.get('super_admin_password'):
            return {'error': 'Super admin password required'}, 403

        if not check_super_admin_auth(data.get('super_admin_password')):
            return {'error': 'Invalid super admin password'}, 403

        return f(*args, **kwargs)
    return decorated
