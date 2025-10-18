"""
Unit tests for temperature control logic.

Tests the core temperature control functionality including hysteresis,
safety limits, pump control, and error handling.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import pytz

from control import TemperatureController
from config import SystemConfig


class TestTemperatureController(unittest.TestCase):
    """Test cases for TemperatureController class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock Evok client
        self.mock_evok = Mock()
        self.mock_evok.get_all_sensors.return_value = [
            {'circuit': 'sensor1', 'dev': 'temp', 'type': 'DS18B20'},
            {'circuit': 'sensor2', 'dev': 'temp', 'type': 'DS18B20'},
            {'circuit': 'sensor3', 'dev': 'temp', 'type': 'DS18B20'}
        ]
        self.mock_evok.get_temperature.return_value = 50.0
        self.mock_evok.set_relay.return_value = True

        # Create test configuration
        self.config = SystemConfig()
        self.config.set('setpoint', 60.0)
        self.config.set('hysteresis', 2.0)
        self.config.set('pump_delay', 60)
        self.config.set('max_temperature', 85.0)
        self.config.set('relay_heating', '1_01')
        self.config.set('relay_pump', '1_02')
        self.config.set('manual_override', False)  # Ensure manual mode is off

        # Create controller
        self.controller = TemperatureController(self.mock_evok, self.config)

    def test_discover_sensors_success(self):
        """Test successful sensor discovery."""
        result = self.controller.discover_sensors()
        self.assertTrue(result)
        self.assertEqual(len(self.controller.sensor_ids), 3)
        self.assertEqual(self.controller.sensor_ids, ['sensor1', 'sensor2', 'sensor3'])

    def test_discover_sensors_warning_on_fewer_sensors(self):
        """Test warning when fewer than 3 sensors found."""
        self.mock_evok.get_all_sensors.return_value = [
            {'circuit': 'sensor1', 'dev': 'temp', 'type': 'DS18B20'}
        ]
        result = self.controller.discover_sensors()
        self.assertTrue(result)
        self.assertEqual(len(self.controller.sensor_ids), 1)

    def test_discover_sensors_failure(self):
        """Test sensor discovery failure."""
        self.mock_evok.get_all_sensors.return_value = None
        result = self.controller.discover_sensors()
        self.assertFalse(result)

    def test_read_temperatures(self):
        """Test reading temperatures from all sensors."""
        self.controller.sensor_ids = ['sensor1', 'sensor2', 'sensor3']
        self.mock_evok.get_temperature.side_effect = [50.0, 51.0, 49.0]

        temps = self.controller.read_temperatures()
        self.assertEqual(len(temps), 3)
        self.assertEqual(temps['sensor1'], 50.0)
        self.assertEqual(temps['sensor2'], 51.0)
        self.assertEqual(temps['sensor3'], 49.0)

    def test_calculate_average_temperature(self):
        """Test average temperature calculation."""
        self.controller.temperatures = {
            'sensor1': 50.0,
            'sensor2': 60.0,
            'sensor3': 70.0
        }
        avg = self.controller.calculate_average_temperature()
        self.assertEqual(avg, 60.0)

    def test_calculate_average_with_none_values(self):
        """Test average calculation ignores None values."""
        self.controller.temperatures = {
            'sensor1': 50.0,
            'sensor2': None,
            'sensor3': 70.0
        }
        avg = self.controller.calculate_average_temperature()
        self.assertEqual(avg, 60.0)

    def test_calculate_average_all_none(self):
        """Test average calculation when all sensors fail."""
        self.controller.temperatures = {
            'sensor1': None,
            'sensor2': None,
            'sensor3': None
        }
        avg = self.controller.calculate_average_temperature()
        self.assertIsNone(avg)

    def test_hysteresis_heating_on(self):
        """Test heating turns on when temperature below setpoint - hysteresis."""
        self.controller.average_temperature = 57.0  # Below 60 - 2 = 58
        self.controller.heating_active = False

        self.controller.update_heating_control()

        self.mock_evok.set_relay.assert_any_call('1_01', True)  # Heating
        self.mock_evok.set_relay.assert_any_call('1_02', True)  # Pump
        self.assertTrue(self.controller.heating_active)
        self.assertTrue(self.controller.pump_active)

    def test_hysteresis_heating_off(self):
        """Test heating turns off when temperature above setpoint + hysteresis."""
        self.controller.average_temperature = 63.0  # Above 60 + 2 = 62
        self.controller.heating_active = True
        self.controller.pump_active = True  # Need pump active too

        self.controller.update_heating_control()

        self.mock_evok.set_relay.assert_any_call('1_01', False)  # Heating off
        self.assertFalse(self.controller.heating_active)
        self.assertIsNotNone(self.controller.pump_shutdown_time)

    def test_hysteresis_no_change_in_deadband(self):
        """Test heating state doesn't change within hysteresis deadband."""
        # Temperature in deadband (58-62), heating currently on
        self.controller.average_temperature = 60.0
        self.controller.heating_active = True

        self.controller.update_heating_control()

        # Should not toggle state
        self.assertTrue(self.controller.heating_active)

    def test_safety_max_temperature(self):
        """Test heating disabled when max temperature exceeded."""
        self.controller.average_temperature = 86.0  # Above max 85
        self.controller.heating_active = True
        self.controller.pump_active = True

        self.controller.update_heating_control()

        self.mock_evok.set_relay.assert_any_call('1_01', False)
        self.assertFalse(self.controller.heating_active)

    def test_heating_disabled_on_no_temperature(self):
        """Test heating disabled when no valid temperature reading."""
        self.controller.average_temperature = None
        self.controller.heating_active = True
        self.controller.pump_active = True

        self.controller.update_heating_control()

        self.mock_evok.set_relay.assert_any_call('1_01', False)
        self.assertFalse(self.controller.heating_active)

    def test_pump_delay_scheduling(self):
        """Test pump shutdown is scheduled with correct delay."""
        self.controller.average_temperature = 63.0
        self.controller.heating_active = True
        self.controller.pump_active = True

        before_time = datetime.now(pytz.timezone('Europe/Prague'))
        self.controller.update_heating_control()
        after_time = datetime.now(pytz.timezone('Europe/Prague'))

        # Pump shutdown should be scheduled ~60 seconds from now
        self.assertIsNotNone(self.controller.pump_shutdown_time)
        expected_shutdown = before_time + timedelta(seconds=60)
        # Allow 2 second tolerance for test execution time
        self.assertLess(abs((self.controller.pump_shutdown_time - expected_shutdown).total_seconds()), 2)

    def test_pump_delayed_shutdown(self):
        """Test pump shuts down after delay expires."""
        # Set pump shutdown time in the past
        past_time = datetime.now(pytz.timezone('Europe/Prague')) - timedelta(seconds=1)
        self.controller.pump_shutdown_time = past_time
        self.controller.pump_active = True

        self.controller.update_pump_control()

        self.mock_evok.set_relay.assert_called_with('1_02', False)
        self.assertFalse(self.controller.pump_active)
        self.assertIsNone(self.controller.pump_shutdown_time)

    def test_pump_no_shutdown_before_delay(self):
        """Test pump doesn't shut down before delay expires."""
        # Set pump shutdown time in the future
        future_time = datetime.now(pytz.timezone('Europe/Prague')) + timedelta(seconds=30)
        self.controller.pump_shutdown_time = future_time
        self.controller.pump_active = True

        self.controller.update_pump_control()

        # Pump should still be active
        self.assertTrue(self.controller.pump_active)

    def test_manual_override_heating(self):
        """Test manual override for heating control."""
        self.config.set('manual_override', True)
        self.config.set('manual_heating', True)
        self.controller.heating_active = False

        self.controller.update_heating_control()

        self.assertTrue(self.controller.heating_active)

    def test_manual_override_pump(self):
        """Test manual override for pump control."""
        self.config.set('manual_override', True)
        self.config.set('manual_pump', True)
        self.controller.pump_active = False

        self.controller.update_pump_control()

        self.assertTrue(self.controller.pump_active)

    def test_get_status(self):
        """Test status reporting."""
        self.controller.temperatures = {'sensor1': 50.0}
        self.controller.average_temperature = 50.0
        self.controller.heating_active = True
        self.controller.pump_active = True

        status = self.controller.get_status()

        self.assertEqual(status['average_temperature'], 50.0)
        self.assertTrue(status['heating'])
        self.assertTrue(status['pump'])
        self.assertEqual(status['setpoint'], 60.0)


class TestTemperatureControlEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_evok = Mock()
        self.config = SystemConfig()
        self.config.set('setpoint', 60.0)
        self.config.set('hysteresis', 2.0)
        self.config.set('relay_heating', '1_01')
        self.config.set('relay_pump', '1_02')
        self.config.set('manual_override', False)  # Ensure manual mode is off
        self.controller = TemperatureController(self.mock_evok, self.config)

    def test_sensor_failure_during_read(self):
        """Test handling of sensor failures during reading."""
        self.controller.sensor_ids = ['sensor1', 'sensor2', 'sensor3']
        self.mock_evok.get_temperature.side_effect = [50.0, None, 52.0]

        temps = self.controller.read_temperatures()

        self.assertEqual(temps['sensor1'], 50.0)
        self.assertIsNone(temps['sensor2'])
        self.assertEqual(temps['sensor3'], 52.0)

    def test_relay_control_failure(self):
        """Test handling of relay control failures."""
        self.mock_evok.set_relay.return_value = False
        self.controller.average_temperature = 57.0

        # Should not crash on relay failure
        self.controller.update_heating_control()

    def test_extreme_temperatures(self):
        """Test handling of extreme temperature values."""
        test_cases = [
            (-10.0, False),  # Below freezing - should disable heating
            (0.0, True),     # Freezing point
            (100.0, False),  # Boiling point - should disable (above max)
        ]

        for temp, should_heat in test_cases:
            self.controller.average_temperature = temp
            self.controller.heating_active = not should_heat
            self.controller.update_heating_control()

    def test_zero_hysteresis(self):
        """Test control with zero hysteresis (edge case)."""
        self.config.set('hysteresis', 0.0)
        self.controller.average_temperature = 59.9
        self.controller.heating_active = False

        self.controller.update_heating_control()

        # Should turn on heating at any temp below setpoint
        self.assertTrue(self.controller.heating_active)

    def test_large_hysteresis(self):
        """Test control with large hysteresis value."""
        self.config.set('hysteresis', 10.0)
        self.controller.average_temperature = 55.0  # Within 60 +/- 10
        self.controller.heating_active = True

        self.controller.update_heating_control()

        # Should maintain current state in wide deadband
        self.assertTrue(self.controller.heating_active)


if __name__ == '__main__':
    unittest.main()
