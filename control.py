"""
Temperature control logic for Hot Water Tank System.

This module implements the main control loop including temperature monitoring,
hysteresis-based heating control, and circulation pump management.
"""

import logging
import time
import pytz
from typing import List, Optional, Dict
from threading import Thread, Event
from datetime import datetime, timedelta

from evok_client import EvokClient
from config import SystemConfig


class TemperatureController:
    """Main temperature control logic handler."""

    # CET timezone for time operations
    CET = pytz.timezone('Europe/Prague')

    def __init__(self, evok_client: EvokClient, config: SystemConfig, database=None):
        """
        Initialize temperature controller.

        Args:
            evok_client: Evok API client instance
            config: System configuration instance
            database: Database instance for logging (optional)
        """
        self.evok = evok_client
        self.config = config
        self.db = database
        self.logger = logging.getLogger(__name__)

        # Sensor IDs (to be discovered)
        self.sensor_ids: List[str] = []

        # Current state
        self.temperatures: Dict[str, Optional[float]] = {}
        self.average_temperature: Optional[float] = None
        self.heating_active = False
        self.pump_active = False
        self.pump_shutdown_time: Optional[datetime] = None

        # Control thread
        self.control_thread: Optional[Thread] = None
        self.stop_event = Event()

        # Database cleanup tracking
        self.last_cleanup: Optional[datetime] = None

    @staticmethod
    def _get_cet_now() -> datetime:
        """Get current time in CET/CEST timezone with automatic DST."""
        return datetime.now(TemperatureController.CET)

    def discover_sensors(self) -> bool:
        """
        Discover 1-wire temperature sensors on the bus.

        Returns:
            True if sensors found, False otherwise
        """
        sensors = self.evok.get_all_sensors()
        if sensors and len(sensors) > 0:
            # Extract sensor circuit IDs (already filtered for DS18B20 by evok_client)
            self.sensor_ids = [s['circuit'] for s in sensors]
            self.logger.info(f"Discovered {len(self.sensor_ids)} temperature sensors: {self.sensor_ids}")

            # Warn if fewer than 3 sensors
            if len(self.sensor_ids) < 3:
                self.logger.warning(f"Only {len(self.sensor_ids)} of 3 expected sensors found")

            return len(self.sensor_ids) > 0

        self.logger.error("No temperature sensors found")
        return False

    def read_temperatures(self) -> Dict[str, Optional[float]]:
        """
        Read temperatures from all sensors.

        Returns:
            Dictionary of sensor ID to temperature readings
        """
        temps = {}
        for sensor_id in self.sensor_ids:
            temp = self.evok.get_temperature(sensor_id)
            temps[sensor_id] = temp
        return temps

    def calculate_average_temperature(self) -> Optional[float]:
        """
        Calculate average temperature from all working sensors.

        Returns:
            Average temperature or None if no valid readings
        """
        valid_temps = [t for t in self.temperatures.values() if t is not None]
        if valid_temps:
            return sum(valid_temps) / len(valid_temps)
        return None

    def update_heating_control(self):
        """Apply hysteresis control logic for heating."""
        if self.config.get('manual_override'):
            # Manual mode - use manual settings
            target_heating = self.config.get('manual_heating', False)
            if target_heating != self.heating_active:
                self.set_heating(target_heating)
            return

        if self.average_temperature is None:
            self.logger.warning("No valid temperature reading, heating disabled")
            self.set_heating(False)
            return

        setpoint = self.config.get('setpoint', 60.0)
        hysteresis = self.config.get('hysteresis', 2.0)
        max_temp = self.config.get('max_temperature', 85.0)

        # Safety check - disable heating if temperature too high
        if self.average_temperature >= max_temp:
            self.logger.warning(f"Temperature {self.average_temperature}°C exceeds maximum {max_temp}°C")
            self.set_heating(False)
            return

        # Hysteresis control logic
        if self.average_temperature < (setpoint - hysteresis):
            # Temperature too low - turn on heating
            if not self.heating_active:
                self.set_heating(True)
        elif self.average_temperature > (setpoint + hysteresis):
            # Temperature too high - turn off heating
            if self.heating_active:
                self.set_heating(False)

    def set_heating(self, state: bool):
        """
        Control heating unit and circulation pump.

        Args:
            state: True to enable heating, False to disable
        """
        relay_heating = self.config.get('relay_heating', '1_01')
        relay_pump = self.config.get('relay_pump', '1_02')

        if state:
            # Turn on heating and pump
            self.evok.set_relay(relay_heating, True)
            self.evok.set_relay(relay_pump, True)
            self.heating_active = True
            self.pump_active = True
            self.pump_shutdown_time = None
            self.logger.info("Heating and pump activated")

            # Log control action
            if self.db:
                self.db.insert_control_action(
                    'heating_on',
                    True,
                    True,
                    self.average_temperature,
                    self.config.get('setpoint')
                )
        else:
            # Turn off heating, schedule pump shutdown
            self.evok.set_relay(relay_heating, False)
            self.heating_active = False

            # Schedule pump shutdown with delay
            pump_delay = self.config.get('pump_delay', 60)
            self.pump_shutdown_time = self._get_cet_now() + timedelta(seconds=pump_delay)
            self.logger.info(f"Heating deactivated, pump will stop in {pump_delay} seconds")

            # Log control action
            if self.db:
                self.db.insert_control_action(
                    'heating_off',
                    False,
                    True,  # Pump still on (delayed shutdown)
                    self.average_temperature,
                    self.config.get('setpoint')
                )

    def update_pump_control(self):
        """Handle pump control (manual or automatic delayed shutdown)."""
        if self.config.get('manual_override'):
            # Manual mode - use manual pump setting
            target_pump = self.config.get('manual_pump', False)
            if target_pump != self.pump_active:
                relay_pump = self.config.get('relay_pump', '1_02')
                self.evok.set_relay(relay_pump, target_pump)
                self.pump_active = target_pump
                self.pump_shutdown_time = None
                self.logger.info(f"Pump manually {'activated' if target_pump else 'deactivated'}")
            return

        # Automatic mode - handle delayed shutdown
        if self.pump_shutdown_time and self._get_cet_now() >= self.pump_shutdown_time:
            relay_pump = self.config.get('relay_pump', '1_02')
            self.evok.set_relay(relay_pump, False)
            self.pump_active = False
            self.pump_shutdown_time = None
            self.logger.info("Circulation pump deactivated")

    def control_loop(self):
        """Main control loop running in separate thread."""
        self.logger.info("Control loop started")

        # Log startup event
        if self.db:
            self.db.insert_event('startup', 'Temperature controller started')

        while not self.stop_event.is_set():
            try:
                # Perform daily database cleanup (once per day)
                if self.db:
                    now = self._get_cet_now()
                    if self.last_cleanup is None or (now - self.last_cleanup).days >= 1:
                        retention_days = self.config.get('data_retention_days', 365)
                        self.logger.info(f"Performing daily database cleanup (keeping {retention_days} days)...")
                        try:
                            self.db.cleanup_old_data(days_to_keep=retention_days)
                            self.last_cleanup = now
                            self.logger.info("Database cleanup completed successfully")
                        except Exception as cleanup_error:
                            self.logger.error(f"Database cleanup error: {cleanup_error}")

                # Read temperatures
                self.temperatures = self.read_temperatures()
                self.average_temperature = self.calculate_average_temperature()

                # Log temperature readings to database
                if self.db:
                    readings = []
                    for idx, (sensor_id, temp) in enumerate(self.temperatures.items()):
                        if temp is not None:
                            readings.append((sensor_id, temp, idx + 1))  # Tank number 1-3

                    if readings:
                        self.db.insert_multiple_readings(readings)

                # Update control logic
                self.update_heating_control()
                self.update_pump_control()

                # Wait for next update
                update_interval = self.config.get('update_interval', 5)
                self.stop_event.wait(timeout=update_interval)

            except Exception as e:
                self.logger.error(f"Error in control loop: {e}")
                if self.db:
                    self.db.insert_event('error', f'Control loop error: {str(e)}')
                time.sleep(5)

        # Log shutdown event
        if self.db:
            self.db.insert_event('shutdown', 'Temperature controller stopped')

        self.logger.info("Control loop stopped")

    def start(self):
        """Start the control loop."""
        if self.control_thread and self.control_thread.is_alive():
            self.logger.warning("Control loop already running")
            return

        # Discover sensors first
        if not self.discover_sensors():
            self.logger.error("No temperature sensors found")
            return

        self.stop_event.clear()
        self.control_thread = Thread(target=self.control_loop, daemon=True)
        self.control_thread.start()
        self.logger.info("Temperature controller started")

    def stop(self):
        """Stop the control loop."""
        self.stop_event.set()
        if self.control_thread:
            self.control_thread.join(timeout=10)
        self.logger.info("Temperature controller stopped")

    def get_status(self) -> Dict:
        """
        Get current system status.

        Returns:
            Dictionary containing current system state
        """
        return {
            'temperatures': self.temperatures,
            'average_temperature': self.average_temperature,
            'heating': self.heating_active,
            'pump': self.pump_active,
            'setpoint': self.config.get('setpoint'),
            'hysteresis': self.config.get('hysteresis'),
            'manual_override': self.config.get('manual_override'),
        }
