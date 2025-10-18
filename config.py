"""
Configuration management for Hot Water Tank Temperature Control System.

This module handles application configuration including default values,
user settings persistence, and environment-specific settings.
"""

import os
import json
from typing import Dict, Any


class Config:
    """Flask application configuration."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Session settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Application settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Evok API settings
    EVOK_HOST = os.environ.get('EVOK_HOST', '127.0.0.1')
    EVOK_PORT = int(os.environ.get('EVOK_PORT', '8080'))
    EVOK_WS_URL = f"ws://{EVOK_HOST}:{EVOK_PORT}/ws"
    EVOK_API_URL = f"http://{EVOK_HOST}:{EVOK_PORT}"


class SystemConfig:
    """System configuration for temperature control with in-memory caching."""

    CONFIG_FILE = 'config.json'

    # Default settings
    DEFAULT_SETTINGS = {
        'setpoint': 60.0,           # Target temperature in °C
        'hysteresis': 2.0,          # Temperature hysteresis in °C
        'pump_delay': 60,           # Pump shutdown delay in seconds
        'sensor_timeout': 30,       # Sensor read timeout in seconds
        'update_interval': 5,       # Temperature update interval in seconds
        'max_temperature': 85.0,    # Maximum safe temperature in °C
        'relay_heating': '1_01',    # Relay circuit for heating unit (Unipi format: "1_01")
        'relay_pump': '1_02',       # Relay circuit for circulation pump (Unipi format: "1_02")
        'manual_override': False,   # Manual control mode
        'manual_heating': False,    # Manual heating state
        'data_retention_days': 365, # Database data retention period in days
    }

    def __init__(self):
        """Initialize configuration with in-memory cache."""
        self.settings = self.load_settings()
        self._cache_mtime = None  # Track file modification time
        self._update_cache_mtime()

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from configuration file."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.DEFAULT_SETTINGS.copy()
                    settings.update(loaded)
                    return settings
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()

    def _update_cache_mtime(self):
        """Update the cached modification time of config file."""
        if os.path.exists(self.CONFIG_FILE):
            self._cache_mtime = os.path.getmtime(self.CONFIG_FILE)

    def _is_cache_valid(self) -> bool:
        """Check if cached settings are still valid (file hasn't been modified)."""
        if not os.path.exists(self.CONFIG_FILE):
            return True  # No file = cache is valid (using defaults)
        current_mtime = os.path.getmtime(self.CONFIG_FILE)
        return current_mtime == self._cache_mtime

    def save_settings(self) -> bool:
        """Save current settings to configuration file."""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            self._update_cache_mtime()  # Update cache timestamp after save
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default=None):
        """Get configuration value from cache (with automatic refresh if file changed)."""
        # Reload if file was modified externally
        if not self._is_cache_valid():
            self.settings = self.load_settings()
            self._update_cache_mtime()
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save."""
        self.settings[key] = value
        return self.save_settings()

    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values."""
        self.settings.update(updates)
        return self.save_settings()
