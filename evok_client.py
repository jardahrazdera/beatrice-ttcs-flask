"""
Evok API client for Unipi 1.1 hardware communication.

This module provides an interface to the Evok API for controlling relays,
reading 1-wire temperature sensors, and monitoring hardware state changes.
"""

import requests
import websocket
import json
import logging
from typing import Optional, List, Dict, Any
from threading import Thread


class EvokClient:
    """Client for communicating with Evok API."""

    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        """
        Initialize Evok client.

        Args:
            host: Evok API host address
            port: Evok API port number
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}/ws"
        self.ws = None
        self.ws_thread = None
        self.logger = logging.getLogger(__name__)

    def get_all_sensors(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all 1-wire temperature sensors.

        Returns:
            List of sensor information dictionaries or None on error
        """
        try:
            # Get all devices and filter for temperature sensors
            response = requests.get(f"{self.base_url}/json/all", timeout=5)
            response.raise_for_status()
            all_devices = response.json()

            # Filter for temperature sensors (DS18B20)
            sensors = [device for device in all_devices
                      if device.get('dev') == 'temp' and device.get('type') == 'DS18B20']

            self.logger.info(f"Found {len(sensors)} DS18B20 temperature sensors")
            return sensors
        except Exception as e:
            self.logger.error(f"Error getting sensors: {e}")
            return None

    def get_temperature(self, sensor_id: str) -> Optional[float]:
        """
        Read temperature from specific sensor.

        Args:
            sensor_id: 1-wire sensor ID

        Returns:
            Temperature in Celsius or None on error
        """
        try:
            response = requests.get(f"{self.base_url}/json/temp/{sensor_id}", timeout=5)
            response.raise_for_status()
            data = response.json()
            return float(data.get('value', 0.0))
        except Exception as e:
            self.logger.error(f"Error reading temperature from {sensor_id}: {e}")
            return None

    def set_relay(self, circuit: str, state: bool) -> bool:
        """
        Set relay state.

        Args:
            circuit: Relay circuit identifier (e.g., "1_01", "1_02")
            state: True for ON, False for OFF

        Returns:
            True if successful, False otherwise
        """
        try:
            value = 1 if state else 0
            response = requests.post(
                f"{self.base_url}/json/ro/{circuit}",
                json={"value": value},
                timeout=5
            )
            response.raise_for_status()
            self.logger.info(f"Relay {circuit} set to {'ON' if state else 'OFF'}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting relay {circuit}: {e}")
            return False

    def get_relay_state(self, circuit: str) -> Optional[bool]:
        """
        Get current relay state.

        Args:
            circuit: Relay circuit identifier (e.g., "1_01", "1_02")

        Returns:
            True if ON, False if OFF, None on error
        """
        try:
            response = requests.get(f"{self.base_url}/json/ro/{circuit}", timeout=5)
            response.raise_for_status()
            data = response.json()
            return bool(data.get('value', 0))
        except Exception as e:
            self.logger.error(f"Error getting relay {circuit} state: {e}")
            return None

    def start_websocket(self, on_message_callback=None):
        """
        Start WebSocket connection for real-time updates.

        Args:
            on_message_callback: Callback function for incoming messages
        """
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if on_message_callback:
                    on_message_callback(data)
            except Exception as e:
                self.logger.error(f"WebSocket message error: {e}")

        def on_error(ws, error):
            self.logger.error(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            self.logger.info("WebSocket connection closed")

        def on_open(ws):
            self.logger.info("WebSocket connection opened")

        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        self.ws_thread = Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def stop_websocket(self):
        """Stop WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.ws = None
