"""
Mock Evok API client for local testing without Unipi hardware.

This module provides a simulated Evok client that generates realistic
temperature data and relay states for development and testing purposes.
"""

import logging
import random
import time
from typing import Optional, List, Dict, Any


class MockEvokClient:
    """Mock Evok client for testing without hardware."""

    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        """
        Initialize mock Evok client.

        Args:
            host: Ignored (for compatibility)
            port: Ignored (for compatibility)
        """
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)

        # Simulate 3 temperature sensors
        self.mock_sensors = [
            {'circuit': '28-00000a1b2c3d', 'typ': 'DS18B20'},
            {'circuit': '28-00000a1b2c4e', 'typ': 'DS18B20'},
            {'circuit': '28-00000a1b2c5f', 'typ': 'DS18B20'}
        ]

        # Simulate temperatures (will fluctuate realistically)
        self.mock_temperatures = {
            '28-00000a1b2c3d': 58.5,
            '28-00000a1b2c4e': 59.0,
            '28-00000a1b2c5f': 58.8
        }

        # Simulate relay states
        self.relay_states = {
            1: False,  # Heating relay
            2: False   # Pump relay
        }

        # Heating simulation
        self.heating_active = False
        self.last_update = time.time()

        self.logger.info('Mock Evok client initialized (development mode)')

    def get_all_sensors(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all 1-wire temperature sensors (mocked).

        Returns:
            List of mock sensor information
        """
        self.logger.debug('Mock: Getting all sensors')
        return self.mock_sensors

    def get_temperature(self, sensor_id: str) -> Optional[float]:
        """
        Read temperature from specific sensor (mocked with simulation).

        Args:
            sensor_id: 1-wire sensor ID

        Returns:
            Simulated temperature in Celsius
        """
        # Update simulation
        self._update_simulation()

        temp = self.mock_temperatures.get(sensor_id)
        if temp is not None:
            # Add small random fluctuation
            temp += random.uniform(-0.2, 0.2)
            self.mock_temperatures[sensor_id] = temp
            self.logger.debug(f'Mock: Temperature {sensor_id} = {temp:.2f}°C')
            return temp

        self.logger.warning(f'Mock: Unknown sensor {sensor_id}')
        return None

    def set_relay(self, circuit: int, state: bool) -> bool:
        """
        Set relay state (mocked).

        Args:
            circuit: Relay circuit number
            state: True for ON, False for OFF

        Returns:
            True (always succeeds in mock)
        """
        self.relay_states[circuit] = state

        # Update heating simulation state
        if circuit == 1:  # Heating relay
            self.heating_active = state

        self.logger.info(f'Mock: Relay {circuit} set to {"ON" if state else "OFF"}')
        return True

    def get_relay_state(self, circuit: int) -> Optional[bool]:
        """
        Get current relay state (mocked).

        Args:
            circuit: Relay circuit number

        Returns:
            Mocked relay state
        """
        state = self.relay_states.get(circuit, False)
        self.logger.debug(f'Mock: Relay {circuit} state = {"ON" if state else "OFF"}')
        return state

    def _update_simulation(self):
        """Update temperature simulation based on heating state."""
        now = time.time()
        delta_time = now - self.last_update
        self.last_update = now

        # Simulate temperature changes based on heating
        for sensor_id in self.mock_temperatures:
            current_temp = self.mock_temperatures[sensor_id]

            if self.heating_active:
                # Temperature rises when heating is on (approx 0.5°C per minute)
                temp_increase = 0.5 * (delta_time / 60)
                new_temp = min(current_temp + temp_increase, 85.0)
            else:
                # Temperature falls slowly when heating is off (approx 0.1°C per minute)
                temp_decrease = 0.1 * (delta_time / 60)
                new_temp = max(current_temp - temp_decrease, 20.0)

            self.mock_temperatures[sensor_id] = new_temp

    def start_websocket(self, on_message_callback=None):
        """
        Mock WebSocket connection (does nothing).

        Args:
            on_message_callback: Ignored in mock
        """
        self.logger.info('Mock: WebSocket connection simulated (no-op)')

    def stop_websocket(self):
        """Mock WebSocket stop (does nothing)."""
        self.logger.info('Mock: WebSocket disconnection simulated (no-op)')


# Factory function to choose between real and mock client
def create_evok_client(host: str = '127.0.0.1', port: int = 8080, mock: bool = False):
    """
    Create Evok client (real or mock).

    Args:
        host: Evok API host
        port: Evok API port
        mock: If True, create mock client for testing

    Returns:
        EvokClient or MockEvokClient instance
    """
    if mock:
        return MockEvokClient(host, port)
    else:
        from evok_client import EvokClient
        return EvokClient(host, port)
