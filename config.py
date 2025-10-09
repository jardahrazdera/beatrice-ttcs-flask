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
    """System configuration for temperature control."""

    CONFIG_FILE = 'config.json'

    # Default settings
    DEFAULT_SETTINGS = {
        'setpoint': 60.0,           # Target temperature in °C
        'hysteresis': 2.0,          # Temperature hysteresis in °C
        'pump_delay': 60,           # Pump shutdown delay in seconds
        'sensor_timeout': 30,       # Sensor read timeout in seconds
        'update_interval': 5,       # Temperature update interval in seconds
        'max_temperature': 85.0,    # Maximum safe temperature in °C
        'relay_heating': 1,         # Relay circuit for heating unit
        'relay_pump': 2,            # Relay circuit for circulation pump
        'manual_override': False,   # Manual control mode
        'manual_heating': False,    # Manual heating state
    }

    def __init__(self):
        """Initialize configuration."""
        self.settings = self.load_settings()

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

    def save_settings(self) -> bool:
        """Save current settings to configuration file."""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save."""
        self.settings[key] = value
        return self.save_settings()

    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values."""
        self.settings.update(updates)
        return self.save_settings()
