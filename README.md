# Hot Water Tank Temperature Control System

A temperature control system for three 1000-liter hot water storage tanks using Unipi 1.1 controller with Raspberry Pi 4.

## Overview

This system monitors and controls water temperature in three interconnected storage tanks using DS18B20 temperature sensors and manages heating through a bivalent heating unit with automatic circulation pump control.

## Features

- **Real-time Temperature Monitoring**: Individual monitoring of three tanks via DS18B20 1-wire sensors
- **Intelligent Control**: Hysteresis-based temperature control with average temperature calculation
- **Web Interface**: Responsive web UI for monitoring and configuration
- **Safety Features**: Over-temperature protection, sensor failure detection, and manual override
- **Historical Data**: Temperature graphs and logging for system analysis
- **Automatic Circulation**: Smart pump control to prevent heating unit overheating

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
- Manual override controls
- View real-time monitoring data

## Deployment

Deploy as a systemd service for automatic startup on boot. See deployment documentation for detailed instructions.

## Project Structure

```
/
├── app.py                 # Main application
├── config.py              # Configuration management
├── control.py             # Temperature control logic
├── evok_client.py         # Evok API client
├── auth.py                # Authentication handler
├── static/                # CSS, JS, images
├── templates/             # HTML templates
└── logs/                  # Application logs
```

## Safety

- Circulation pump is automatically controlled and should not be manually overridden to prevent heating unit damage
- Over-temperature protection is built into the control logic
- Sensor failure detection with safe fallback behavior

## License

See LICENSE file for details.

## Contributing

Contributions are welcome. Please ensure code follows PEP 8 standards and includes appropriate error handling.
