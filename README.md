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

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
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

4. Configure Evok for Unipi 1.1 according to hardware setup

5. Run the application:
```bash
python app.py
```

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

Deploy as a systemd service for automatic startup on boot. See deployment documentation for detailed instructions.

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
├── static/                # CSS, JS, images
├── templates/             # HTML templates (Czech language)
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
