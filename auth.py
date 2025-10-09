"""
Authentication handler for web interface.

This module provides basic authentication functionality including
password hashing, session management, and login decorators.
"""

import hashlib
import os
from functools import wraps
from flask import session, redirect, url_for, request


# Default credentials (should be changed in production)
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD_HASH = hashlib.sha256('admin123'.encode()).hexdigest()

# In production, store credentials in environment variables or secure config
CREDENTIALS = {
    DEFAULT_USERNAME: DEFAULT_PASSWORD_HASH
}


def hash_password(password: str) -> str:
    """
    Hash password using SHA-256.

    Args:
        password: Plain text password

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(password.encode()).hexdigest()


def check_auth(username: str, password: str) -> bool:
    """
    Verify username and password.

    Args:
        username: Username to check
        password: Plain text password

    Returns:
        True if credentials are valid, False otherwise
    """
    if username not in CREDENTIALS:
        return False

    password_hash = hash_password(password)
    return CREDENTIALS[username] == password_hash


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
