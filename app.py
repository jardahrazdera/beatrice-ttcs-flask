"""
Main Flask application for Hot Water Tank Temperature Control System.

This module initializes the Flask web application and handles routing
for the temperature control system interface.
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
import os
import atexit
from threading import Thread
import time

from config import Config, SystemConfig
from control import TemperatureController
from evok_mock import create_evok_client
from auth import check_auth, requires_auth, requires_super_admin
from database import Database

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize SocketIO for real-time updates (exempt from CSRF)
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Hot Water Tank Control System startup')

# Initialize system configuration
system_config = SystemConfig()

# Initialize database
db = Database('data.db')

# Initialize controllers
evok_client = None
temp_controller = None
broadcast_thread = None
broadcast_running = False


@app.route('/')
@requires_auth
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication handler."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_auth(username, password):
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Neplatné přihlašovací údaje')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout handler - also disables manual override for safety."""
    # Disable manual override when user logs out (safety feature)
    if system_config.get('manual_override', False):
        system_config.update({
            'manual_override': False,
            'manual_heating': False,
            'manual_pump': False
        })
        app.logger.warning('Manual override disabled on logout (safety)')

    session.pop('authenticated', None)
    return redirect(url_for('login'))


@app.route('/history')
@requires_auth
def history():
    """History and statistics page."""
    return render_template('history.html')


@app.route('/settings', methods=['GET', 'POST'])
@requires_auth
def settings():
    """Settings page for configuration."""
    if request.method == 'POST':
        # Handle settings update
        pass

    return render_template('settings.html')


@app.route('/api/temperature')
@requires_auth
def get_temperature():
    """API endpoint for current temperature readings."""
    if temp_controller:
        temps = temp_controller.temperatures
        # Convert sensor IDs to tank numbers
        sensor_ids = list(temps.keys())
        return jsonify({
            'tank1': temps.get(sensor_ids[0]) if len(sensor_ids) > 0 else None,
            'tank2': temps.get(sensor_ids[1]) if len(sensor_ids) > 1 else None,
            'tank3': temps.get(sensor_ids[2]) if len(sensor_ids) > 2 else None,
            'average': temp_controller.average_temperature
        })
    return jsonify({
        'tank1': None,
        'tank2': None,
        'tank3': None,
        'average': None
    })


@app.route('/api/status')
@requires_auth
def get_status():
    """API endpoint for system status."""
    if temp_controller:
        status = temp_controller.get_status()
        status.update({
            'setpoint': system_config.get('setpoint'),
            'hysteresis': system_config.get('hysteresis')
        })
        return jsonify(status)

    return jsonify({
        'heating': False,
        'pump': False,
        'setpoint': system_config.get('setpoint', 60.0),
        'hysteresis': system_config.get('hysteresis', 2.0),
        'manual_override': system_config.get('manual_override', False)
    })


@app.route('/api/settings', methods=['GET'])
@requires_auth
def get_settings():
    """API endpoint to load current settings."""
    sensor_count = len(temp_controller.sensor_ids) if temp_controller else 0

    settings = system_config.settings.copy()
    settings['sensor_count'] = sensor_count

    return jsonify(settings)


@app.route('/api/settings/temperature', methods=['POST'])
@requires_auth
def save_temperature_settings():
    """API endpoint to save temperature settings."""
    try:
        data = request.get_json()

        # Validate input
        setpoint = float(data.get('setpoint', 60.0))
        hysteresis = float(data.get('hysteresis', 2.0))
        max_temperature = float(data.get('max_temperature', 85.0))

        if not (30 <= setpoint <= 85):
            return jsonify({'error': 'Setpoint must be between 30-85°C'}), 400

        if not (0.5 <= hysteresis <= 10):
            return jsonify({'error': 'Hysteresis must be between 0.5-10°C'}), 400

        if not (60 <= max_temperature <= 95):
            return jsonify({'error': 'Max temperature must be between 60-95°C'}), 400

        # Update settings
        system_config.update({
            'setpoint': setpoint,
            'hysteresis': hysteresis,
            'max_temperature': max_temperature
        })

        app.logger.info(f'Temperature settings updated: setpoint={setpoint}, hysteresis={hysteresis}')
        return jsonify({'success': True, 'message': 'Settings saved'})

    except Exception as e:
        app.logger.error(f'Error saving temperature settings: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/pump', methods=['POST'])
@requires_auth
def save_pump_settings():
    """API endpoint to save pump settings."""
    try:
        data = request.get_json()

        pump_delay = int(data.get('pump_delay', 60))

        if not (0 <= pump_delay <= 300):
            return jsonify({'error': 'Pump delay must be between 0-300 seconds'}), 400

        system_config.set('pump_delay', pump_delay)

        app.logger.info(f'Pump settings updated: delay={pump_delay}s')
        return jsonify({'success': True, 'message': 'Settings saved'})

    except Exception as e:
        app.logger.error(f'Error saving pump settings: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/system', methods=['POST'])
@requires_auth
def save_system_settings():
    """API endpoint to save system settings."""
    try:
        data = request.get_json()

        update_interval = int(data.get('update_interval', 5))
        sensor_timeout = int(data.get('sensor_timeout', 30))

        if not (1 <= update_interval <= 60):
            return jsonify({'error': 'Update interval must be between 1-60 seconds'}), 400

        if not (5 <= sensor_timeout <= 120):
            return jsonify({'error': 'Sensor timeout must be between 5-120 seconds'}), 400

        system_config.update({
            'update_interval': update_interval,
            'sensor_timeout': sensor_timeout
        })

        app.logger.info(f'System settings updated: interval={update_interval}s, timeout={sensor_timeout}s')
        return jsonify({'success': True, 'message': 'Settings saved'})

    except Exception as e:
        app.logger.error(f'Error saving system settings: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/manual', methods=['POST'])
@requires_auth
@requires_super_admin
def save_manual_override():
    """API endpoint to save manual override settings. Requires super admin password."""
    try:
        data = request.get_json()

        manual_override = bool(data.get('manual_override', False))
        manual_heating = bool(data.get('manual_heating', False))
        manual_pump = bool(data.get('manual_pump', False))

        system_config.update({
            'manual_override': manual_override,
            'manual_heating': manual_heating,
            'manual_pump': manual_pump
        })

        app.logger.warning(f'Manual override {"enabled" if manual_override else "disabled"} by super admin')
        if manual_override:
            app.logger.info(f'Manual controls: heating={manual_heating}, pump={manual_pump}')
        return jsonify({'success': True, 'message': 'Manual override updated'})

    except Exception as e:
        app.logger.error(f'Error saving manual override: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/temperature', methods=['GET'])
@requires_auth
def get_temperature_history():
    """API endpoint for temperature history."""
    try:
        hours = int(request.args.get('hours', 24))
        tank_number = request.args.get('tank')

        if tank_number:
            tank_number = int(tank_number)

        history = db.get_temperature_history(hours=hours, tank_number=tank_number)
        return jsonify({'success': True, 'data': history})

    except Exception as e:
        app.logger.error(f'Error getting temperature history: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/average', methods=['GET'])
@requires_auth
def get_average_history():
    """API endpoint for averaged temperature history."""
    try:
        hours = int(request.args.get('hours', 24))
        interval = int(request.args.get('interval', 5))

        history = db.get_average_temperature_history(hours=hours, interval_minutes=interval)
        return jsonify({'success': True, 'data': history})

    except Exception as e:
        app.logger.error(f'Error getting average history: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/average/range', methods=['GET'])
@requires_auth
def get_average_history_range():
    """API endpoint for averaged temperature history with custom date range."""
    try:
        from datetime import datetime

        date_from_str = request.args.get('from')
        date_to_str = request.args.get('to')
        interval = int(request.args.get('interval', 5))

        if not date_from_str or not date_to_str:
            return jsonify({'error': 'Missing from or to parameter'}), 400

        # Parse datetime-local format (YYYY-MM-DDTHH:MM)
        date_from = datetime.fromisoformat(date_from_str)
        date_to = datetime.fromisoformat(date_to_str)

        # Validate date range
        if date_from >= date_to:
            return jsonify({'error': 'Start date must be before end date'}), 400

        history = db.get_average_temperature_history_range(
            date_from=date_from,
            date_to=date_to,
            interval_minutes=interval
        )
        return jsonify({'success': True, 'data': history})

    except ValueError as ve:
        app.logger.error(f'Invalid date format: {ve}')
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DDTHH:MM'}), 400
    except Exception as e:
        app.logger.error(f'Error getting average history by range: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/events', methods=['GET'])
@requires_auth
def get_events_history():
    """API endpoint for system events."""
    try:
        limit = int(request.args.get('limit', 100))
        event_type = request.args.get('type')

        events = db.get_recent_events(limit=limit, event_type=event_type)
        return jsonify({'success': True, 'data': events})

    except Exception as e:
        app.logger.error(f'Error getting events: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/events/range', methods=['GET'])
@requires_auth
def get_events_history_range():
    """API endpoint for system events with custom date range."""
    try:
        from datetime import datetime

        date_from_str = request.args.get('from')
        date_to_str = request.args.get('to')
        event_type = request.args.get('type')

        if not date_from_str or not date_to_str:
            return jsonify({'error': 'Missing from or to parameter'}), 400

        # Parse datetime-local format (YYYY-MM-DDTHH:MM)
        date_from = datetime.fromisoformat(date_from_str)
        date_to = datetime.fromisoformat(date_to_str)

        # Validate date range
        if date_from >= date_to:
            return jsonify({'error': 'Start date must be before end date'}), 400

        events = db.get_events_range(
            date_from=date_from,
            date_to=date_to,
            event_type=event_type if event_type else None
        )
        return jsonify({'success': True, 'data': events})

    except ValueError as ve:
        app.logger.error(f'Invalid date format: {ve}')
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DDTHH:MM'}), 400
    except Exception as e:
        app.logger.error(f'Error getting events by range: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/control', methods=['GET'])
@requires_auth
def get_control_history():
    """API endpoint for control action history."""
    try:
        hours = int(request.args.get('hours', 24))

        history = db.get_control_history(hours=hours)
        return jsonify({'success': True, 'data': history})

    except Exception as e:
        app.logger.error(f'Error getting control history: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/control/range', methods=['GET'])
@requires_auth
def get_control_history_range():
    """API endpoint for control action history with custom date range."""
    try:
        from datetime import datetime

        date_from_str = request.args.get('from')
        date_to_str = request.args.get('to')

        if not date_from_str or not date_to_str:
            return jsonify({'error': 'Missing from or to parameter'}), 400

        # Parse datetime-local format (YYYY-MM-DDTHH:MM)
        date_from = datetime.fromisoformat(date_from_str)
        date_to = datetime.fromisoformat(date_to_str)

        # Validate date range
        if date_from >= date_to:
            return jsonify({'error': 'Start date must be before end date'}), 400

        history = db.get_control_history_range(
            date_from=date_from,
            date_to=date_to
        )
        return jsonify({'success': True, 'data': history})

    except ValueError as ve:
        app.logger.error(f'Invalid date format: {ve}')
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DDTHH:MM'}), 400
    except Exception as e:
        app.logger.error(f'Error getting control history by range: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
@requires_auth
def get_statistics():
    """API endpoint for statistical summary."""
    try:
        hours = int(request.args.get('hours', 24))

        stats = db.get_statistics(hours=hours)
        return jsonify({'success': True, 'data': stats})

    except Exception as e:
        app.logger.error(f'Error getting statistics: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/stats', methods=['GET'])
@requires_auth
def get_database_stats():
    """API endpoint for database statistics."""
    try:
        stats = db.get_database_info()
        return jsonify(stats)

    except Exception as e:
        app.logger.error(f'Error getting database stats: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/delete', methods=['POST'])
@requires_auth
@requires_super_admin
def delete_database():
    """API endpoint to delete all database data. Requires super admin password."""
    try:
        deleted = db.delete_all_data()

        app.logger.warning('Database cleared via API request by super admin')
        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': 'All database data has been deleted'
        })

    except Exception as e:
        app.logger.error(f'Error deleting database: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    app.logger.info('Client connected')
    emit('status', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    app.logger.info('Client disconnected')


def broadcast_updates():
    """Background thread to broadcast temperature and status updates via WebSocket."""
    global broadcast_running

    while broadcast_running:
        try:
            if temp_controller:
                # Get current temperature data
                temps = temp_controller.temperatures
                sensor_ids = list(temps.keys())

                temp_data = {
                    'tank1': temps.get(sensor_ids[0]) if len(sensor_ids) > 0 else None,
                    'tank2': temps.get(sensor_ids[1]) if len(sensor_ids) > 1 else None,
                    'tank3': temps.get(sensor_ids[2]) if len(sensor_ids) > 2 else None,
                    'average': temp_controller.average_temperature
                }

                # Get current status
                status_data = temp_controller.get_status()
                status_data.update({
                    'setpoint': system_config.get('setpoint'),
                    'hysteresis': system_config.get('hysteresis')
                })

                # Broadcast to all connected clients
                socketio.emit('temperature_update', temp_data)
                socketio.emit('status_update', status_data)

            # Wait before next update
            time.sleep(system_config.get('update_interval', 5))

        except Exception as e:
            app.logger.error(f'Error in broadcast thread: {e}')
            time.sleep(5)

    app.logger.info('Broadcast thread stopped')


def initialize_system():
    """Initialize Evok client and temperature controller."""
    global evok_client, temp_controller, broadcast_thread, broadcast_running

    try:
        app.logger.info('Initializing system...')

        # Initialize Evok client (mock or real based on environment)
        evok_host = app.config.get('EVOK_HOST', '127.0.0.1')
        evok_port = app.config.get('EVOK_PORT', 8080)
        use_mock = os.environ.get('USE_MOCK_EVOK', 'false').lower() == 'true'

        evok_client = create_evok_client(host=evok_host, port=evok_port, mock=use_mock)

        if use_mock:
            app.logger.warning('Using MOCK Evok client (development mode)')
        else:
            app.logger.info(f'Evok client initialized: {evok_host}:{evok_port}')

        # Initialize temperature controller with database
        temp_controller = TemperatureController(evok_client, system_config, db)

        # Start control loop
        temp_controller.start()
        app.logger.info('Temperature controller started')

        # Start broadcast thread
        broadcast_running = True
        broadcast_thread = Thread(target=broadcast_updates, daemon=True)
        broadcast_thread.start()
        app.logger.info('Broadcast thread started')

        app.logger.info('System initialization complete')

    except Exception as e:
        app.logger.error(f'Error initializing system: {e}')


def shutdown_system():
    """Shutdown system cleanly."""
    global temp_controller, broadcast_running

    app.logger.info('Shutting down system...')

    # Stop broadcast thread
    broadcast_running = False

    # Stop temperature controller
    if temp_controller:
        temp_controller.stop()
        app.logger.info('Temperature controller stopped')

    app.logger.info('System shutdown complete')


# Register shutdown handler
atexit.register(shutdown_system)

# Initialize system at module level (works with both gunicorn and direct run)
# Only initialize if in Flask reloader child process or in production (gunicorn)
# WERKZEUG_RUN_MAIN is set by Flask reloader in the child process
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    # This is either the reloader child process or production - initialize
    initialize_system()


if __name__ == '__main__':
    # Run Flask-SocketIO server for development
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
