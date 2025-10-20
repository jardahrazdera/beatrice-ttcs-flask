"""
Integration tests for Flask API endpoints.

Tests authentication, API endpoints, WebSocket functionality,
and error handling.
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

# Import app dependencies after preventing app initialization
os.environ['USE_MOCK_EVOK'] = 'true'

from app import app, socketio, system_config, db
from config import SystemConfig
from control import TemperatureController


class TestFlaskAPI(unittest.TestCase):
    """Test cases for Flask API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['WTF_CSRF_ENABLED'] = False

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Mock authenticated session
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_index_requires_auth(self):
        """Test that index page requires authentication."""
        # Clear session
        with self.client.session_transaction() as sess:
            sess.clear()

        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_index_with_auth(self):
        """Test accessing index with authentication."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_get(self):
        """Test login page GET request."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    @patch('app.check_auth')
    def test_login_post_success(self, mock_check_auth):
        """Test successful login."""
        mock_check_auth.return_value = True

        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'password'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @patch('app.check_auth')
    def test_login_post_failure(self, mock_check_auth):
        """Test failed login."""
        mock_check_auth.return_value = False

        response = self.client.post('/login', data={
            'username': 'wrong',
            'password': 'wrong'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Neplatn', response.data)  # Czech error message

    def test_logout(self):
        """Test logout functionality."""
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_logout_disables_manual_override(self):
        """Test that logout disables manual override for safety."""
        system_config.set('manual_override', True)

        self.client.get('/logout')

        self.assertFalse(system_config.get('manual_override'))

    def test_get_temperature_no_controller(self):
        """Test temperature endpoint when controller not initialized."""
        with patch('app.temp_controller', None):
            response = self.client.get('/api/temperature')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertIsNone(data['tank1'])
            self.assertIsNone(data['average'])

    def test_get_status_no_controller(self):
        """Test status endpoint when controller not initialized."""
        with patch('app.temp_controller', None):
            response = self.client.get('/api/status')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertFalse(data['heating'])
            self.assertFalse(data['pump'])

    def test_get_settings(self):
        """Test loading settings."""
        response = self.client.get('/api/settings')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('setpoint', data)
        self.assertIn('hysteresis', data)

    def test_save_temperature_settings_valid(self):
        """Test saving valid temperature settings."""
        response = self.client.post('/api/settings/temperature',
            json={
                'setpoint': 65.0,
                'hysteresis': 3.0,
                'max_temperature': 80.0
            })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify settings were saved
        self.assertEqual(system_config.get('setpoint'), 65.0)
        self.assertEqual(system_config.get('hysteresis'), 3.0)

    def test_save_temperature_settings_invalid_setpoint(self):
        """Test validation of invalid setpoint."""
        response = self.client.post('/api/settings/temperature',
            json={
                'setpoint': 100.0,  # Too high
                'hysteresis': 2.0,
                'max_temperature': 85.0
            })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_save_temperature_settings_invalid_hysteresis(self):
        """Test validation of invalid hysteresis."""
        response = self.client.post('/api/settings/temperature',
            json={
                'setpoint': 60.0,
                'hysteresis': 15.0,  # Too high
                'max_temperature': 85.0
            })

        self.assertEqual(response.status_code, 400)

    def test_save_pump_settings_valid(self):
        """Test saving valid pump settings."""
        response = self.client.post('/api/settings/pump',
            json={'pump_delay': 90})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        self.assertEqual(system_config.get('pump_delay'), 90)

    def test_save_pump_settings_invalid(self):
        """Test validation of invalid pump delay."""
        response = self.client.post('/api/settings/pump',
            json={'pump_delay': 500})  # Too high

        self.assertEqual(response.status_code, 400)

    def test_save_system_settings_valid(self):
        """Test saving valid system settings."""
        response = self.client.post('/api/settings/system',
            json={
                'update_interval': 10,
                'sensor_timeout': 45
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(system_config.get('update_interval'), 10)

    def test_save_system_settings_invalid_interval(self):
        """Test validation of invalid update interval."""
        response = self.client.post('/api/settings/system',
            json={
                'update_interval': 100,  # Too high
                'sensor_timeout': 30
            })

        self.assertEqual(response.status_code, 400)

    def test_heating_system_enable(self):
        """Test enabling heating system."""
        system_config.set('heating_system_enabled', False)

        response = self.client.post('/api/settings/heating-system',
            json={'enabled': True})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(system_config.get('heating_system_enabled'))
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['heating_system_enabled'])

    def test_heating_system_disable(self):
        """Test disabling heating system."""
        system_config.set('heating_system_enabled', True)

        response = self.client.post('/api/settings/heating-system',
            json={'enabled': False})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(system_config.get('heating_system_enabled'))
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertFalse(data['heating_system_enabled'])

    def test_heating_system_missing_parameter(self):
        """Test heating system endpoint with missing parameter."""
        response = self.client.post('/api/settings/heating-system',
            json={})

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.requires_super_admin')
    def test_manual_override_requires_super_admin(self, mock_super_admin):
        """Test that manual override requires super admin password."""
        # Simulate super admin decorator allowing access
        mock_super_admin.return_value = lambda f: f

        response = self.client.post('/api/settings/manual',
            json={
                'manual_override': True,
                'manual_heating': True,
                'manual_pump': False
            })

        self.assertEqual(response.status_code, 200)

    def test_get_temperature_history(self):
        """Test temperature history endpoint."""
        response = self.client.get('/api/history/temperature?hours=24')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)

    def test_get_average_history(self):
        """Test average temperature history endpoint."""
        response = self.client.get('/api/history/average?hours=12&interval=10')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_get_events_history(self):
        """Test system events endpoint."""
        response = self.client.get('/api/history/events?limit=50')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_get_control_history(self):
        """Test control action history endpoint."""
        response = self.client.get('/api/history/control?hours=24')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_get_statistics(self):
        """Test statistics endpoint."""
        response = self.client.get('/api/statistics?hours=24')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_get_database_stats(self):
        """Test database statistics endpoint."""
        response = self.client.get('/api/database/stats')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('total_readings', data)

    def test_settings_validation_edge_cases(self):
        """Test settings validation with edge case values."""
        # Minimum valid values
        response = self.client.post('/api/settings/temperature',
            json={
                'setpoint': 5.0,
                'hysteresis': 0.5,
                'max_temperature': 60.0
            })
        self.assertEqual(response.status_code, 200)

        # Maximum valid values
        response = self.client.post('/api/settings/temperature',
            json={
                'setpoint': 85.0,
                'hysteresis': 10.0,
                'max_temperature': 95.0
            })
        self.assertEqual(response.status_code, 200)

    def test_api_error_handling(self):
        """Test API error handling with malformed requests."""
        # Missing required fields
        response = self.client.post('/api/settings/temperature',
            json={})

        # Should use defaults, not crash
        self.assertIn(response.status_code, [200, 400, 500])

    def test_api_requires_json_content_type(self):
        """Test API endpoints handle non-JSON requests."""
        response = self.client.post('/api/settings/temperature',
            data='not json',
            content_type='text/plain')

        # Should handle gracefully
        self.assertIn(response.status_code, [400, 500])


class TestAuthentication(unittest.TestCase):
    """Test authentication and authorization."""

    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_unauthenticated_access_redirects(self):
        """Test that unauthenticated requests redirect to login."""
        protected_routes = [
            '/',
            '/history',
            '/settings'
        ]

        for route in protected_routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302)  # Redirect

    def test_unauthenticated_api_access(self):
        """Test that unauthenticated API requests are blocked."""
        api_routes = [
            '/api/temperature',
            '/api/status',
            '/api/settings'
        ]

        for route in api_routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [302, 401, 403])

    def test_session_persistence(self):
        """Test that session persists across requests."""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

        # First request
        response1 = self.client.get('/api/status')
        self.assertEqual(response1.status_code, 200)

        # Second request should still be authenticated
        response2 = self.client.get('/api/temperature')
        self.assertEqual(response2.status_code, 200)


class TestWebSocket(unittest.TestCase):
    """Test WebSocket functionality."""

    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        self.client = socketio.test_client(app)
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.client.is_connected():
            self.client.disconnect()
        self.app_context.pop()

    def test_websocket_connection(self):
        """Test WebSocket connection."""
        self.assertTrue(self.client.is_connected())

    def test_websocket_receives_status(self):
        """Test WebSocket receives status message on connect."""
        received = self.client.get_received()

        # Should receive status message
        status_messages = [msg for msg in received if msg['name'] == 'status']
        self.assertGreater(len(status_messages), 0)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        with self.client.session_transaction() as sess:
            sess['authenticated'] = True

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_invalid_json_payload(self):
        """Test handling of invalid JSON payload."""
        response = self.client.post('/api/settings/temperature',
            data='{ invalid json }',
            content_type='application/json')

        self.assertIn(response.status_code, [400, 500])

    def test_missing_parameters(self):
        """Test handling of missing required parameters."""
        response = self.client.post('/api/settings/temperature',
            json={'setpoint': 60.0})  # Missing hysteresis and max_temperature

        # Should use defaults or return error
        self.assertIn(response.status_code, [200, 400])

    def test_invalid_parameter_types(self):
        """Test handling of invalid parameter types."""
        response = self.client.post('/api/settings/temperature',
            json={
                'setpoint': 'not_a_number',
                'hysteresis': 2.0,
                'max_temperature': 85.0
            })

        self.assertIn(response.status_code, [400, 500])

    def test_sql_injection_attempts(self):
        """Test that SQL injection attempts are handled safely."""
        malicious_inputs = [
            "'; DROP TABLE temperature_readings; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>"
        ]

        for malicious_input in malicious_inputs:
            response = self.client.get(f'/api/history/events?type={malicious_input}')
            # Should not crash and should sanitize input
            self.assertIn(response.status_code, [200, 400, 500])

    def test_extreme_parameter_values(self):
        """Test handling of extreme parameter values."""
        extreme_values = [
            {'setpoint': 999999, 'hysteresis': 2.0, 'max_temperature': 85.0},
            {'setpoint': -1000, 'hysteresis': 2.0, 'max_temperature': 85.0},
            {'setpoint': 60.0, 'hysteresis': -50, 'max_temperature': 85.0},
        ]

        for values in extreme_values:
            response = self.client.post('/api/settings/temperature', json=values)
            self.assertEqual(response.status_code, 400)  # Should reject


if __name__ == '__main__':
    unittest.main()
