"""
Main Flask application for Hot Water Tank Temperature Control System.

This module initializes the Flask web application and handles routing
for the temperature control system interface.
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import logging
from logging.handlers import RotatingFileHandler
import os

from config import Config
from control import TemperatureController
from evok_client import EvokClient
from auth import check_auth, requires_auth

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SocketIO for real-time updates
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

# Initialize controllers
evok_client = None
temp_controller = None


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
    """Logout handler."""
    session.pop('authenticated', None)
    return redirect(url_for('login'))


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
    # TODO: Implement temperature reading
    return jsonify({
        'tank1': 0.0,
        'tank2': 0.0,
        'tank3': 0.0,
        'average': 0.0
    })


@app.route('/api/status')
@requires_auth
def get_status():
    """API endpoint for system status."""
    # TODO: Implement status retrieval
    return jsonify({
        'heating': False,
        'pump': False,
        'setpoint': 60.0,
        'hysteresis': 2.0
    })


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    app.logger.info('Client connected')
    emit('status', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    app.logger.info('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
