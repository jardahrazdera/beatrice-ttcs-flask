# Development Guide

This guide explains how to set up and run the Hot Water Tank Control System locally for development and testing.

## Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of Flask and Python

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jardahrazdera/beatrice-ttcs-flask.git
cd beatrice-ttcs-flask
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)

```bash
cp .env.example .env
# Edit .env file as needed
```

### 5. Run in Development Mode

#### Quick Start (Using Mock Hardware)

```bash
./run_dev.sh
```

This script automatically:
- Creates virtual environment if needed
- Installs dependencies
- Sets `USE_MOCK_EVOK=true` for simulated hardware
- Starts Flask in debug mode

#### Manual Start

```bash
export USE_MOCK_EVOK=true
export FLASK_DEBUG=true
python app.py
```

### 6. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

**Default credentials:**
- Username: `admin`
- Password: `admin123`

> **Important:** Change these credentials in production!

## Mock Mode vs. Production Mode

### Mock Mode (Development)

When `USE_MOCK_EVOK=true`:
- Uses simulated Evok client
- Generates realistic temperature data
- Temperatures change based on heating state
- No actual hardware required
- Perfect for UI development and testing

### Production Mode

When `USE_MOCK_EVOK=false` or not set:
- Connects to real Evok API
- Requires Unipi 1.1 hardware
- Reads actual DS18B20 sensors
- Controls real relays

## Project Structure

```
beatrice-ttcs-flask/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── control.py             # Temperature control logic
├── evok_client.py         # Real Evok API client
├── evok_mock.py           # Mock Evok client for testing
├── auth.py                # Authentication
├── requirements.txt       # Python dependencies
├── run_dev.sh            # Development run script
├── .env.example          # Environment variables template
├── static/               # Frontend assets
│   ├── css/
│   ├── js/
│   └── img/
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── settings.html
└── logs/                 # Application logs
```

## Development Workflow

### 1. Backend Development

Edit Python files:
- `app.py` - Add new routes or API endpoints
- `control.py` - Modify control logic
- `config.py` - Update configuration options
- `evok_client.py` - Extend hardware communication

Flask auto-reloads on file changes when `FLASK_DEBUG=true`.

### 2. Frontend Development

Edit templates and assets:
- `templates/*.html` - Modify UI
- `static/css/style.css` - Update styles
- `static/js/*.js` - Add JavaScript functionality

Refresh browser to see changes.

### 3. Testing Changes

- Test in mock mode first
- Verify all features work without hardware
- Test API endpoints using browser dev tools
- Check WebSocket communication
- Review logs in `logs/app.log`

## API Endpoints

### Temperature & Status

```bash
# Get current temperatures
GET /api/temperature

# Get system status
GET /api/status
```

### Settings

```bash
# Load all settings
GET /api/settings

# Save temperature settings
POST /api/settings/temperature
{
  "setpoint": 60.0,
  "hysteresis": 2.0,
  "max_temperature": 85.0
}

# Save pump settings
POST /api/settings/pump
{
  "pump_delay": 60
}

# Save system settings
POST /api/settings/system
{
  "update_interval": 5,
  "sensor_timeout": 30
}

# Manual override
POST /api/settings/manual
{
  "manual_override": true,
  "manual_heating": false
}
```

## WebSocket Events

### Client → Server

```javascript
// Connect to server
socket = io();
```

### Server → Client

```javascript
// Temperature update
socket.on('temperature_update', (data) => {
  // data: {tank1, tank2, tank3, average}
});

// Status update
socket.on('status_update', (data) => {
  // data: {heating, pump, setpoint, hysteresis, ...}
});
```

## Configuration

### System Configuration (config.json)

Settings are persisted in `config.json`:

```json
{
  "setpoint": 60.0,
  "hysteresis": 2.0,
  "pump_delay": 60,
  "sensor_timeout": 30,
  "update_interval": 5,
  "max_temperature": 85.0,
  "relay_heating": 1,
  "relay_pump": 2,
  "manual_override": false,
  "manual_heating": false
}
```

### Flask Configuration

Edit `config.py` to modify:
- Secret key
- Session settings
- Evok API endpoints

## Logging

Logs are written to `logs/app.log`:

```bash
# View logs
tail -f logs/app.log

# View last 50 lines
tail -n 50 logs/app.log
```

Log rotation:
- Max file size: 10KB
- Backup count: 10 files

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

### Dependencies Not Installing

```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -v -r requirements.txt
```

### WebSocket Not Connecting

- Check browser console for errors
- Verify Flask-SocketIO is installed
- Check firewall settings
- Ensure correct port (5000)

### Mock Temperatures Not Changing

- Verify `USE_MOCK_EVOK=true` is set
- Check logs for errors
- Ensure control loop is running

## Adding New Features

### 1. Add API Endpoint

Edit `app.py`:

```python
@app.route('/api/new-endpoint')
@requires_auth
def new_endpoint():
    # Your code here
    return jsonify({'result': 'data'})
```

### 2. Add Frontend Page

1. Create template in `templates/`
2. Add route in `app.py`
3. Add navigation link in `templates/base.html`
4. Create JavaScript file in `static/js/`

### 3. Add Configuration Option

1. Add to `DEFAULT_SETTINGS` in `config.py`
2. Add UI control in `templates/settings.html`
3. Add API endpoint to save setting
4. Update frontend JavaScript to handle setting

## Deployment

See separate deployment documentation for:
- Raspberry Pi deployment
- Systemd service setup
- Production configuration
- Security hardening

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly in mock mode
4. Test on actual hardware if possible
5. Update documentation
6. Create pull request

## License

MIT License - See LICENSE file
