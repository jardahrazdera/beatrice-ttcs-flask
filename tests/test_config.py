"""
Unit tests for configuration management.

Tests configuration loading, saving, validation, and error handling.
"""

import unittest
import tempfile
import os
import json

from config import SystemConfig


class TestSystemConfig(unittest.TestCase):
    """Test cases for SystemConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_fd, self.temp_config_path = tempfile.mkstemp(suffix='.json')
        # Temporarily override CONFIG_FILE class attribute
        self.original_config_file = SystemConfig.CONFIG_FILE
        SystemConfig.CONFIG_FILE = self.temp_config_path
        self.config = SystemConfig()

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original CONFIG_FILE
        SystemConfig.CONFIG_FILE = self.original_config_file
        os.close(self.temp_fd)
        if os.path.exists(self.temp_config_path):
            os.unlink(self.temp_config_path)

    def test_default_values(self):
        """Test default configuration values."""
        self.assertEqual(self.config.get('setpoint'), 60.0)
        self.assertEqual(self.config.get('hysteresis'), 2.0)
        self.assertEqual(self.config.get('pump_delay'), 60)
        self.assertEqual(self.config.get('max_temperature'), 85.0)
        self.assertEqual(self.config.get('update_interval'), 5)
        self.assertFalse(self.config.get('manual_override'))
        self.assertTrue(self.config.get('heating_system_enabled'))

    def test_set_and_get(self):
        """Test setting and getting configuration values."""
        self.config.set('setpoint', 70.0)
        self.assertEqual(self.config.get('setpoint'), 70.0)

        self.config.set('manual_override', True)
        self.assertTrue(self.config.get('manual_override'))

    def test_get_with_default(self):
        """Test getting non-existent key with default value."""
        value = self.config.get('non_existent_key', 'default_value')
        self.assertEqual(value, 'default_value')

    def test_save_and_load(self):
        """Test saving and loading configuration from file."""
        # Set some values
        self.config.set('setpoint', 75.0)
        self.config.set('hysteresis', 3.0)

        # Create new config instance and load
        new_config = SystemConfig()

        self.assertEqual(new_config.get('setpoint'), 75.0)
        self.assertEqual(new_config.get('hysteresis'), 3.0)

    def test_load_corrupted_file(self):
        """Test loading corrupted JSON file."""
        # Write invalid JSON
        with open(self.temp_config_path, 'w') as f:
            f.write("{ invalid json }")

        # Should not crash, should use defaults
        config = SystemConfig()
        self.assertEqual(config.get('setpoint'), 60.0)  # Should use default

    def test_load_missing_file(self):
        """Test loading non-existent config file."""
        os.unlink(self.temp_config_path)

        # Should not crash, should use defaults
        config = SystemConfig()
        self.assertEqual(config.get('setpoint'), 60.0)

    def test_save_creates_file(self):
        """Test save creates file if it doesn't exist."""
        os.unlink(self.temp_config_path)

        self.config.set('setpoint', 65.0)

        self.assertTrue(os.path.exists(self.temp_config_path))

    def test_get_all_settings(self):
        """Test getting all settings."""
        self.config.set('setpoint', 70.0)
        self.config.set('custom_key', 'custom_value')

        all_settings = self.config.settings

        self.assertIn('setpoint', all_settings)
        self.assertIn('custom_key', all_settings)
        self.assertEqual(all_settings['setpoint'], 70.0)

    def test_numeric_value_types(self):
        """Test handling of different numeric types."""
        # Float
        self.config.set('setpoint', 65.5)
        self.assertEqual(self.config.get('setpoint'), 65.5)

        # Integer
        self.config.set('pump_delay', 120)
        self.assertEqual(self.config.get('pump_delay'), 120)

    def test_boolean_values(self):
        """Test handling of boolean values."""
        self.config.set('manual_override', True)
        self.assertTrue(self.config.get('manual_override'))

        self.config.set('manual_override', False)
        self.assertFalse(self.config.get('manual_override'))

        self.config.set('heating_system_enabled', False)
        self.assertFalse(self.config.get('heating_system_enabled'))

        self.config.set('heating_system_enabled', True)
        self.assertTrue(self.config.get('heating_system_enabled'))

    def test_string_values(self):
        """Test handling of string values."""
        self.config.set('relay_heating', '1_01')
        self.assertEqual(self.config.get('relay_heating'), '1_01')


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_fd, self.temp_config_path = tempfile.mkstemp(suffix='.json')
        self.original_config_file = SystemConfig.CONFIG_FILE
        SystemConfig.CONFIG_FILE = self.temp_config_path
        self.config = SystemConfig()

    def tearDown(self):
        """Clean up test fixtures."""
        SystemConfig.CONFIG_FILE = self.original_config_file
        os.close(self.temp_fd)
        if os.path.exists(self.temp_config_path):
            os.unlink(self.temp_config_path)

    def test_temperature_bounds(self):
        """Test temperature values are within reasonable bounds."""
        # Valid values
        self.config.set('setpoint', 60.0)
        self.assertEqual(self.config.get('setpoint'), 60.0)

        # Edge cases
        self.config.set('setpoint', 5.0)  # Minimum reasonable
        self.assertEqual(self.config.get('setpoint'), 5.0)

        self.config.set('setpoint', 85.0)  # Maximum reasonable
        self.assertEqual(self.config.get('setpoint'), 85.0)

    def test_hysteresis_positive(self):
        """Test hysteresis is positive."""
        self.config.set('hysteresis', 2.5)
        self.assertEqual(self.config.get('hysteresis'), 2.5)

        # Test zero (edge case)
        self.config.set('hysteresis', 0.0)
        self.assertEqual(self.config.get('hysteresis'), 0.0)

    def test_pump_delay_non_negative(self):
        """Test pump delay is non-negative."""
        self.config.set('pump_delay', 60)
        self.assertEqual(self.config.get('pump_delay'), 60)

        # Test zero (immediate shutdown)
        self.config.set('pump_delay', 0)
        self.assertEqual(self.config.get('pump_delay'), 0)

    def test_persistence_after_multiple_saves(self):
        """Test configuration persists correctly after multiple saves."""
        # First save
        self.config.set('setpoint', 65.0)

        # Second save with different value
        self.config.set('setpoint', 70.0)
        self.config.set('hysteresis', 3.0)

        # Load and verify
        new_config = SystemConfig()

        self.assertEqual(new_config.get('setpoint'), 70.0)
        self.assertEqual(new_config.get('hysteresis'), 3.0)


class TestConfigEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_fd, self.temp_config_path = tempfile.mkstemp(suffix='.json')
        self.original_config_file = SystemConfig.CONFIG_FILE
        SystemConfig.CONFIG_FILE = self.temp_config_path
        self.config = SystemConfig()

    def tearDown(self):
        """Clean up test fixtures."""
        SystemConfig.CONFIG_FILE = self.original_config_file
        os.close(self.temp_fd)
        if os.path.exists(self.temp_config_path):
            os.unlink(self.temp_config_path)

    def test_empty_config_file(self):
        """Test loading empty config file."""
        # Write empty file
        with open(self.temp_config_path, 'w') as f:
            f.write('')

        config = SystemConfig()

        # Should use defaults
        self.assertEqual(config.get('setpoint'), 60.0)

    def test_config_with_extra_fields(self):
        """Test loading config with extra unknown fields."""
        # Write config with extra fields
        config_data = {
            'setpoint': 65.0,
            'unknown_field': 'value',
            'another_unknown': 123
        }
        with open(self.temp_config_path, 'w') as f:
            json.dump(config_data, f)

        config = SystemConfig()

        # Should load known fields
        self.assertEqual(config.get('setpoint'), 65.0)
        # Extra fields should be preserved
        self.assertEqual(config.get('unknown_field'), 'value')

    def test_read_only_file_save(self):
        """Test saving to read-only file."""
        # Make file read-only
        os.chmod(self.temp_config_path, 0o444)

        result = self.config.set('setpoint', 70.0)

        # Save should handle error gracefully and return False
        self.assertFalse(result)

        # Restore permissions for cleanup
        os.chmod(self.temp_config_path, 0o644)

    def test_concurrent_modifications(self):
        """Test handling concurrent modifications."""
        # Simulate external modification
        self.config.set('setpoint', 65.0)

        # External modification
        with open(self.temp_config_path, 'w') as f:
            json.dump({'setpoint': 70.0}, f)

        # Load should get external changes
        self.config.settings = self.config.load_settings()
        self.assertEqual(self.config.get('setpoint'), 70.0)

    def test_none_values(self):
        """Test handling of None values."""
        self.config.set('test_key', None)
        self.assertIsNone(self.config.get('test_key'))

    def test_special_characters_in_strings(self):
        """Test handling of special characters."""
        test_strings = [
            'relay_1-01',
            'sensor@bus#1',
            'config/path/value',
            'unicode_čěš'
        ]

        for test_str in test_strings:
            self.config.set('test_string', test_str)
            self.assertEqual(self.config.get('test_string'), test_str)

            # Verify persistence
            new_config = SystemConfig()
            self.assertEqual(new_config.get('test_string'), test_str)


if __name__ == '__main__':
    unittest.main()
