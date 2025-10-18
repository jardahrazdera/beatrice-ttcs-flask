"""
Unit tests for Evok client.

Tests Evok API communication, sensor reading, relay control,
and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests

from evok_client import EvokClient


class TestEvokClient(unittest.TestCase):
    """Test cases for EvokClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = EvokClient(host='127.0.0.1', port=8080)

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.host, '127.0.0.1')
        self.assertEqual(self.client.port, 8080)
        self.assertEqual(self.client.base_url, 'http://127.0.0.1:8080')
        self.assertEqual(self.client.ws_url, 'ws://127.0.0.1:8080/ws')

    @patch('evok_client.requests.get')
    def test_get_all_sensors_success(self, mock_get):
        """Test successful sensor discovery."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'dev': 'temp', 'type': 'DS18B20', 'circuit': 'sensor1', 'value': 50.0},
            {'dev': 'temp', 'type': 'DS18B20', 'circuit': 'sensor2', 'value': 51.0},
            {'dev': 'relay', 'circuit': 'relay1', 'value': 0}  # Should be filtered out
        ]
        mock_get.return_value = mock_response

        sensors = self.client.get_all_sensors()

        self.assertEqual(len(sensors), 2)
        self.assertEqual(sensors[0]['circuit'], 'sensor1')
        self.assertEqual(sensors[1]['circuit'], 'sensor2')
        mock_get.assert_called_once_with('http://127.0.0.1:8080/json/all', timeout=5)

    @patch('evok_client.requests.get')
    def test_get_all_sensors_network_error(self, mock_get):
        """Test sensor discovery with network error."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        sensors = self.client.get_all_sensors()

        self.assertIsNone(sensors)

    @patch('evok_client.requests.get')
    def test_get_all_sensors_timeout(self, mock_get):
        """Test sensor discovery with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()

        sensors = self.client.get_all_sensors()

        self.assertIsNone(sensors)

    @patch('evok_client.requests.get')
    def test_get_temperature_success(self, mock_get):
        """Test successful temperature reading."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'value': 55.5}
        mock_get.return_value = mock_response

        temp = self.client.get_temperature('sensor1')

        self.assertEqual(temp, 55.5)
        mock_get.assert_called_once_with('http://127.0.0.1:8080/json/temp/sensor1', timeout=5)

    @patch('evok_client.requests.get')
    def test_get_temperature_error(self, mock_get):
        """Test temperature reading with error."""
        mock_get.side_effect = requests.exceptions.RequestException()

        temp = self.client.get_temperature('sensor1')

        self.assertIsNone(temp)

    @patch('evok_client.requests.get')
    def test_get_temperature_invalid_response(self, mock_get):
        """Test temperature reading with invalid response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing 'value' key
        mock_get.return_value = mock_response

        temp = self.client.get_temperature('sensor1')

        self.assertEqual(temp, 0.0)  # Default value

    @patch('evok_client.requests.post')
    def test_set_relay_on_success(self, mock_post):
        """Test successful relay control (ON)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.client.set_relay('1_01', True)

        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://127.0.0.1:8080/json/ro/1_01',
            json={'value': 1},
            timeout=5
        )

    @patch('evok_client.requests.post')
    def test_set_relay_off_success(self, mock_post):
        """Test successful relay control (OFF)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.client.set_relay('1_02', False)

        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://127.0.0.1:8080/json/ro/1_02',
            json={'value': 0},
            timeout=5
        )

    @patch('evok_client.requests.post')
    def test_set_relay_network_error(self, mock_post):
        """Test relay control with network error."""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        result = self.client.set_relay('1_01', True)

        self.assertFalse(result)

    @patch('evok_client.requests.post')
    def test_set_relay_timeout(self, mock_post):
        """Test relay control with timeout."""
        mock_post.side_effect = requests.exceptions.Timeout()

        result = self.client.set_relay('1_01', True)

        self.assertFalse(result)

    @patch('evok_client.requests.get')
    def test_get_relay_state_on(self, mock_get):
        """Test reading relay state (ON)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'value': 1}
        mock_get.return_value = mock_response

        state = self.client.get_relay_state('1_01')

        self.assertTrue(state)

    @patch('evok_client.requests.get')
    def test_get_relay_state_off(self, mock_get):
        """Test reading relay state (OFF)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'value': 0}
        mock_get.return_value = mock_response

        state = self.client.get_relay_state('1_01')

        self.assertFalse(state)

    @patch('evok_client.requests.get')
    def test_get_relay_state_error(self, mock_get):
        """Test reading relay state with error."""
        mock_get.side_effect = requests.exceptions.RequestException()

        state = self.client.get_relay_state('1_01')

        self.assertIsNone(state)


class TestEvokClientEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = EvokClient(host='192.168.1.100', port=8080)

    @patch('evok_client.requests.get')
    def test_empty_sensor_list(self, mock_get):
        """Test handling of empty sensor list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        sensors = self.client.get_all_sensors()

        self.assertEqual(sensors, [])

    @patch('evok_client.requests.get')
    def test_malformed_json_response(self, mock_get):
        """Test handling of malformed JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_get.return_value = mock_response

        sensors = self.client.get_all_sensors()

        self.assertIsNone(sensors)

    @patch('evok_client.requests.get')
    def test_http_error_codes(self, mock_get):
        """Test handling of HTTP error codes."""
        error_codes = [400, 401, 403, 404, 500, 503]

        for code in error_codes:
            mock_response = Mock()
            mock_response.status_code = code
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_get.return_value = mock_response

            sensors = self.client.get_all_sensors()
            self.assertIsNone(sensors)

    @patch('evok_client.requests.get')
    def test_extreme_temperature_values(self, mock_get):
        """Test handling of extreme temperature values."""
        test_temps = [-55.0, 0.0, 125.0, 999.9]

        for temp_value in test_temps:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'value': temp_value}
            mock_get.return_value = mock_response

            temp = self.client.get_temperature('sensor1')
            self.assertEqual(temp, temp_value)

    def test_custom_host_and_port(self):
        """Test initialization with custom host and port."""
        client = EvokClient(host='192.168.2.100', port=9090)

        self.assertEqual(client.base_url, 'http://192.168.2.100:9090')
        self.assertEqual(client.ws_url, 'ws://192.168.2.100:9090/ws')

    @patch('evok_client.requests.post')
    def test_rapid_relay_switching(self, mock_post):
        """Test rapid relay on/off switching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Rapid switching
        for i in range(10):
            state = i % 2 == 0
            result = self.client.set_relay('1_01', state)
            self.assertTrue(result)

        self.assertEqual(mock_post.call_count, 10)

    @patch('evok_client.requests.get')
    def test_multiple_sensor_types(self, mock_get):
        """Test filtering of different sensor types."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'dev': 'temp', 'type': 'DS18B20', 'circuit': 'sensor1'},
            {'dev': 'temp', 'type': 'DHT22', 'circuit': 'sensor2'},  # Different type
            {'dev': 'temp', 'type': 'DS18B20', 'circuit': 'sensor3'},
            {'dev': 'input', 'circuit': 'input1'},  # Not a temp sensor
        ]
        mock_get.return_value = mock_response

        sensors = self.client.get_all_sensors()

        # Should only return DS18B20 sensors
        self.assertEqual(len(sensors), 2)
        self.assertTrue(all(s['type'] == 'DS18B20' for s in sensors))


class TestEvokWebSocket(unittest.TestCase):
    """Test WebSocket functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = EvokClient()

    @patch('evok_client.websocket.WebSocketApp')
    @patch('evok_client.Thread')
    def test_websocket_start(self, mock_thread, mock_ws_app):
        """Test WebSocket connection initialization."""
        callback = Mock()

        self.client.start_websocket(on_message_callback=callback)

        # Verify WebSocketApp was created
        mock_ws_app.assert_called_once()

        # Verify thread was started
        mock_thread.assert_called_once()

    def test_websocket_stop(self):
        """Test WebSocket connection closing."""
        self.client.ws = Mock()
        mock_ws = self.client.ws

        self.client.stop_websocket()

        mock_ws.close.assert_called_once()
        self.assertIsNone(self.client.ws)

    def test_websocket_stop_when_not_connected(self):
        """Test stopping WebSocket when not connected."""
        self.client.ws = None

        # Should not crash
        self.client.stop_websocket()


if __name__ == '__main__':
    unittest.main()
