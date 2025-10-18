# Hot Water Tank Temperature Control System

A temperature control system for three 1000-liter hot water storage tanks using Unipi 1.1 controller with Raspberry Pi 4.

## Overview

This system monitors and controls water temperature in three interconnected storage tanks using DS18B20 temperature sensors and manages heating through a bivalent heating unit with automatic circulation pump control.

## Features

- **Real-time Temperature Monitoring**: Individual monitoring of three tanks via DS18B20 1-wire sensors
- **Intelligent Control**: Hysteresis-based temperature control with average temperature calculation
- **Web Interface**: Responsive web UI for monitoring and configuration (Czech language)
- **Safety Features**: Over-temperature protection, sensor failure detection, and manual override
- **Historical Data**: Temperature graphs, statistics, and event logging for system analysis
- **Automatic Circulation**: Smart pump control to prevent heating unit overheating
- **Secure Authentication**: Multi-level access control with super admin protection for sensitive operations
- **Database Management**: Temperature history, events, and control action logging

## Hardware Requirements

- Unipi 1.1 controller with Raspberry Pi 4
- 3x DS18B20 1-wire temperature sensors
- Bivalent heating unit
- Circulation pump
- 3x 1000L hot water tanks with heat exchangers

## Technology Stack

- **Backend**: Python 3, Flask
- **Frontend**: HTML5/CSS3/JavaScript, Chart.js
- **Communication**: Evok API (REST/JSON + WebSocket)
- **System**: systemd service, logging

## Quick Start

### Production Installation (Raspberry Pi with Unipi 1.1)

The easiest way to install on a Raspberry Pi:

```bash
wget https://raw.githubusercontent.com/jardahrazdera/beatrice-ttcs-flask/master/deployment/install.sh
chmod +x install.sh
./install.sh
```

The installation script will:
- Install all dependencies
- Clone the repository to `/opt/water-tank-control`
- Set up Python virtual environment
- Configure systemd service
- Optionally configure nginx reverse proxy

**Prerequisites:** Ensure Evok is installed and running before installation.

For detailed installation instructions and configuration, see [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md).

### Development Setup

For development on your local machine:

1. Clone the repository:
```bash
git clone https://github.com/jardahrazdera/beatrice-ttcs-flask.git
cd beatrice-ttcs-flask
```

2. Create and activate Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env to set USE_MOCK_EVOK=true for development
```

5. Run the application:
```bash
python app.py
```

Access at `http://localhost:5000`

### Running Tests

The project includes a comprehensive test suite with 68 tests covering all critical functionality:

```bash
# Run all tests
./run_tests.py

# Run with pytest
venv/bin/python -m pytest

# Run specific test file
venv/bin/python -m pytest tests/test_control.py -v
```

For detailed testing documentation, see [TESTING.md](TESTING.md).

## Configuration

Access the web interface at `http://<raspberry-pi-ip>:5000` to configure:
- Target temperature setpoint
- Temperature hysteresis (upper/lower bounds)
- Pump delay settings
- System update intervals
- Manual override controls (requires super admin password)
- View real-time monitoring data
- Access historical temperature graphs and statistics

### Authentication

**Default credentials:**
- Username: `admin`
- Password: `admin123`

**Super admin password** (for sensitive operations):
- Default: `superadmin123`
- Configure via `SUPER_ADMIN_PASSWORD` environment variable
- Required for: Manual override, Database deletion

**⚠️ IMPORTANT**: Change all default passwords in production!

## Deployment

The system is designed for production deployment on Raspberry Pi with automatic startup and monitoring.

### Quick Deployment

After installation, the system runs as a systemd service:

```bash
# Service management
sudo systemctl start water-tank-control    # Start service
sudo systemctl stop water-tank-control     # Stop service
sudo systemctl restart water-tank-control  # Restart service
sudo systemctl status water-tank-control   # Check status

# View logs
sudo journalctl -u water-tank-control -f   # Follow logs in real-time
```

### Updating

The installation uses git for easy updates:

```bash
cd /opt/water-tank-control
git pull origin master
source venv/bin/activate
pip install -r requirements.txt  # If dependencies changed
sudo systemctl restart water-tank-control
```

Your local configuration (`.env`, `config.json`, `data.db`, logs) is automatically preserved during updates.

### Production Features

- **Systemd Integration**: Auto-start on boot, automatic restart on failure
- **Nginx Support**: Optional reverse proxy for professional deployment
- **Logging**: Rotating file logs + systemd journal integration
- **Security**: Process isolation, read-only system files
- **Git-Based Deployment**: Easy updates and rollback capability

For complete deployment instructions, nginx configuration, SSL setup, and troubleshooting, see [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md).

## Project Structure

```
/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── control.py             # Temperature control logic
├── evok_client.py         # Real Evok API client
├── evok_mock.py           # Mock client for development
├── auth.py                # Authentication (basic + super admin)
├── database.py            # SQLite database management
├── run_tests.py           # Test runner
├── static/                # CSS, JS, images
├── templates/             # HTML templates (Czech language)
├── tests/                 # Test suite (68 tests)
├── logs/                  # Application logs
├── deployment/            # Deployment scripts and configs
└── doc/                   # Additional documentation
```

## Safety

- **Protected Manual Override**: Manual control of heating and pump requires super admin authentication to prevent accidental misuse
- **Circulation Pump Protection**: Pump is automatically controlled to prevent heating unit overheating
- **Over-temperature Protection**: Built-in safety limits with automatic shutdown
- **Sensor Failure Detection**: Safe fallback behavior when sensors fail
- **Database Backup**: All operations logged; database deletion requires super admin password

## License

See LICENSE file for details.

## Contributing

Contributions are welcome. Please ensure code follows PEP 8 standards and includes appropriate error handling.
