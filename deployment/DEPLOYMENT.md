# Deployment Guide

This guide explains how to deploy the Hot Water Tank Control System to a Raspberry Pi with Unipi 1.1.

## Prerequisites

### Hardware
- Raspberry Pi 4 with Unipi 1.1
- 3x DS18B20 temperature sensors connected to 1-wire bus
- Relays wired to heating unit and circulation pump
- Network connectivity (Ethernet recommended)

### Software
- Raspberry Pi OS (32-bit or 64-bit)
- Evok installed and running
- SSH access enabled
- Git installed

## Installation Methods

### Method 1: Automated Installation (Recommended)

1. **SSH to Raspberry Pi**
   ```bash
   ssh pi@<raspberry-pi-ip>
   ```

2. **Clone Repository**
   ```bash
   cd ~
   git clone https://github.com/jardahrazdera/beatrice-ttcs-flask.git
   cd beatrice-ttcs-flask
   ```

3. **Run Installation Script**
   ```bash
   ./deployment/install.sh
   ```

   The script will:
   - Check for Evok installation
   - Install system dependencies
   - Create installation directory (`/opt/water-tank-control`)
   - Set up Python virtual environment
   - Install Python dependencies
   - Generate secure secret key
   - Install systemd service
   - Optionally start the service

4. **Access Web Interface**
   ```
   http://<raspberry-pi-ip>:5000
   ```

   Default credentials:
   - Username: `admin`
   - Password: `admin123`

### Method 2: Manual Installation

1. **Install Dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv git
   ```

2. **Create Installation Directory**
   ```bash
   sudo mkdir -p /opt/water-tank-control
   sudo chown $USER:$USER /opt/water-tank-control
   cd /opt/water-tank-control
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/jardahrazdera/beatrice-ttcs-flask.git .
   ```

4. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit configuration
   ```

6. **Install Systemd Service**
   ```bash
   sudo cp deployment/water-tank-control.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable water-tank-control
   sudo systemctl start water-tank-control
   ```

## Configuration

### Environment Variables (.env)

Edit `/opt/water-tank-control/.env`:

```bash
# Flask Configuration
FLASK_DEBUG=false
SECRET_KEY=<generated-during-installation>

# Evok API Configuration
EVOK_HOST=127.0.0.1
EVOK_PORT=8080

# Production Mode
USE_MOCK_EVOK=false
```

### System Configuration (config.json)

Default settings are created automatically. Modify via web interface:

```json
{
  "setpoint": 60.0,
  "hysteresis": 2.0,
  "pump_delay": 60,
  "sensor_timeout": 30,
  "update_interval": 5,
  "max_temperature": 85.0,
  "relay_heating": "1_01",
  "relay_pump": "1_02"
}
```

### Hardware Configuration

Verify relay assignments in Evok match your wiring:
- **Relay 1_01**: Heating unit control
- **Relay 1_02**: Circulation pump control

**Note**: Relay circuits use Unipi format with underscore (e.g., "1_01", "1_02", etc.)

Update `config.json` if different:
```bash
nano /opt/water-tank-control/config.json
```

## Service Management

### Start/Stop/Restart Service

```bash
# Start service
sudo systemctl start water-tank-control

# Stop service
sudo systemctl stop water-tank-control

# Restart service
sudo systemctl restart water-tank-control

# Check status
sudo systemctl status water-tank-control
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable water-tank-control

# Disable auto-start
sudo systemctl disable water-tank-control
```

### View Logs

```bash
# Follow logs in real-time
sudo journalctl -u water-tank-control -f

# View last 50 lines
sudo journalctl -u water-tank-control -n 50

# View logs since today
sudo journalctl -u water-tank-control --since today
```

## Verification

### 1. Check Service Status

```bash
sudo systemctl status water-tank-control
```

Should show: `Active: active (running)`

### 2. Check Evok Communication

```bash
# Test Evok API - get all devices
curl http://localhost:8080/json/all

# Filter for temperature sensors
curl http://localhost:8080/json/all | grep -A5 '"dev": "temp"'
```

### 3. Check Application Logs

```bash
sudo journalctl -u water-tank-control -n 50
```

Look for:
- "System initialization complete"
- "Temperature controller started"
- No error messages

### 4. Access Web Interface

Open browser to `http://<raspberry-pi-ip>:5000`

Should see login page.

### 5. Verify Temperature Readings

After login, dashboard should display:
- Individual tank temperatures
- Average temperature
- Heating/pump status

## Security

### Change Default Password

**IMPORTANT**: Change default credentials immediately!

Currently, passwords are hardcoded in `auth.py`. To change:

1. Edit auth.py:
   ```bash
   nano /opt/water-tank-control/auth.py
   ```

2. Change password hash:
   ```python
   # Generate new hash
   python3 -c "import hashlib; print(hashlib.sha256('your-new-password'.encode()).hexdigest())"

   # Update CREDENTIALS in auth.py
   ```

3. Restart service:
   ```bash
   sudo systemctl restart water-tank-control
   ```

### Firewall Configuration

If using firewall, allow appropriate ports:

```bash
# For standalone mode (direct access on port 5000)
sudo ufw allow 5000/tcp

# For nginx reverse proxy mode (HTTP on port 80)
sudo ufw allow 80/tcp

# For nginx with SSL (HTTPS on port 443)
sudo ufw allow 443/tcp
```

## Nginx Reverse Proxy (Recommended for Production)

Using nginx as a reverse proxy provides better performance, proper static file serving, and professional deployment.

### Basic HTTP Setup (Access Point Mode)

This configuration is ideal when Unipi runs in WiFi Access Point mode for local access.

1. **Install nginx**
   ```bash
   sudo apt-get update
   sudo apt-get install -y nginx
   ```

2. **Copy nginx configuration**
   ```bash
   sudo cp /opt/water-tank-control/deployment/nginx-water-tank.conf \
       /etc/nginx/sites-available/water-tank-control

   # Remove default site
   sudo rm /etc/nginx/sites-enabled/default

   # Enable water tank control site
   sudo ln -s /etc/nginx/sites-available/water-tank-control \
       /etc/nginx/sites-enabled/
   ```

3. **Test nginx configuration**
   ```bash
   sudo nginx -t
   ```

4. **Restart nginx**
   ```bash
   sudo systemctl restart nginx
   sudo systemctl enable nginx
   ```

5. **Restart application service** (now uses gunicorn on 127.0.0.1:5000)
   ```bash
   sudo systemctl restart water-tank-control
   ```

6. **Access web interface**
   ```
   http://<unipi-ip>
   ```

   Note: No port number needed! Nginx listens on port 80 (default HTTP port).

   For Access Point mode, typical IP is: `http://192.168.4.1`

### HTTPS/SSL Setup (Optional)

For encrypted communication, especially if connecting over network:

1. **Generate self-signed certificate**
   ```bash
   sudo mkdir -p /etc/nginx/ssl
   sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
       -keyout /etc/nginx/ssl/water-tank.key \
       -out /etc/nginx/ssl/water-tank.crt \
       -subj "/C=CZ/ST=Prague/L=Prague/O=Home/CN=unipi.local"
   ```

2. **Use SSL configuration**
   ```bash
   # Remove HTTP-only configuration
   sudo rm /etc/nginx/sites-enabled/water-tank-control

   # Copy SSL configuration
   sudo cp /opt/water-tank-control/deployment/nginx-water-tank-ssl.conf \
       /etc/nginx/sites-available/water-tank-control

   # Enable SSL site
   sudo ln -s /etc/nginx/sites-available/water-tank-control \
       /etc/nginx/sites-enabled/
   ```

3. **Test and restart nginx**
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **Access via HTTPS**
   ```
   https://<unipi-ip>
   ```

   Note: Browser will show security warning (self-signed certificate). This is normal - accept the exception.

### Standalone Mode (Without Nginx)

If you prefer direct access without nginx:

1. **Modify systemd service**

   Edit `/etc/systemd/system/water-tank-control.service` and change bind address:
   ```
   ExecStart=/opt/water-tank-control/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
   ```

2. **Reload and restart**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart water-tank-control
   ```

3. **Access web interface**
   ```
   http://<unipi-ip>:5000
   ```

## Updating

### Update from Git

```bash
cd /opt/water-tank-control
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart water-tank-control
```

### Manual File Update

```bash
# Stop service
sudo systemctl stop water-tank-control

# Update files
cd /opt/water-tank-control
# Copy updated files...

# Restart service
sudo systemctl start water-tank-control
```

## Backup

### Backup Configuration

```bash
# Backup configuration and data
tar -czf backup-$(date +%Y%m%d).tar.gz \
    /opt/water-tank-control/config.json \
    /opt/water-tank-control/.env \
    /opt/water-tank-control/logs/
```

### Restore Configuration

```bash
# Extract backup
tar -xzf backup-20250110.tar.gz -C /

# Restart service
sudo systemctl restart water-tank-control
```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   sudo journalctl -u water-tank-control -n 100
   ```

2. Check Evok status:
   ```bash
   sudo systemctl status evok
   ```

3. Test manually:
   ```bash
   cd /opt/water-tank-control
   source venv/bin/activate
   python app.py
   ```

### Temperature Sensors Not Found

1. Check 1-wire devices:
   ```bash
   # Get all devices and look for temp sensors
   curl http://localhost:8080/json/all | grep -A5 '"dev": "temp"'

   # Or check specific sensor by circuit ID
   curl http://localhost:8080/json/temp/289CD2A908000010
   ```

2. Verify sensor connections to 1-wire bus
3. Check Evok configuration and service status

### Web Interface Not Accessible

1. Check if service is running:
   ```bash
   sudo systemctl status water-tank-control
   ```

2. Check port binding:
   ```bash
   sudo netstat -tlnp | grep 5000
   ```

3. Check firewall settings

### Relays Not Responding

1. Test relay via Evok (use correct circuit format):
   ```bash
   # Turn relay ON (circuit format: "1_01", "1_02", etc.)
   curl -X POST http://localhost:8080/json/ro/1_01 \
     -H "Content-Type: application/json" \
     -d '{"value": 1}'

   # Turn relay OFF
   curl -X POST http://localhost:8080/json/ro/1_01 \
     -H "Content-Type: application/json" \
     -d '{"value": 0}'

   # Check relay state
   curl http://localhost:8080/json/ro/1_01
   ```

2. Check relay wiring to heating unit and pump
3. Verify relay circuit numbers in config.json match your hardware
4. Note: Relay circuits use format "1_01", "1_02", etc. (not integers)

### Nginx Issues

1. **Nginx won't start**
   ```bash
   # Check nginx configuration syntax
   sudo nginx -t

   # Check nginx logs
   sudo tail -f /var/log/nginx/error.log

   # Check if port 80 is already in use
   sudo netstat -tlnp | grep :80
   ```

2. **502 Bad Gateway error**

   This means nginx can't connect to the backend application.

   ```bash
   # Check if water-tank-control service is running
   sudo systemctl status water-tank-control

   # Check if gunicorn is listening on correct port
   sudo netstat -tlnp | grep 5000

   # Check application logs
   sudo journalctl -u water-tank-control -n 50
   ```

3. **WebSocket connection fails**

   Real-time temperature updates won't work without WebSocket.

   ```bash
   # Check nginx error log for WebSocket errors
   sudo tail -f /var/log/nginx/water-tank-error.log

   # Verify Socket.IO endpoint is accessible
   curl -I http://localhost/socket.io/

   # Test backend WebSocket directly
   curl -I http://localhost:5000/socket.io/
   ```

4. **Static files not loading (CSS/JS missing)**

   ```bash
   # Verify static files path exists
   ls -la /opt/water-tank-control/static/

   # Check nginx access log
   sudo tail -f /var/log/nginx/water-tank-access.log

   # Test static file directly
   curl -I http://localhost/static/css/style.css
   ```

5. **Can't access from other devices (Access Point mode)**

   ```bash
   # Check if nginx is listening on all interfaces
   sudo netstat -tlnp | grep :80
   # Should show: 0.0.0.0:80 or :::80

   # Check firewall
   sudo ufw status

   # Verify WiFi AP is working
   ip addr show wlan0  # or relevant interface
   ```

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop water-tank-control
sudo systemctl disable water-tank-control

# Remove service file
sudo rm /etc/systemd/system/water-tank-control.service
sudo systemctl daemon-reload

# Remove installation directory
sudo rm -rf /opt/water-tank-control

# Remove firewall rule (if added)
sudo ufw delete allow 5000/tcp
```

## Support

For issues or questions:
- Check logs: `sudo journalctl -u water-tank-control -f`
- Review documentation in repository
- Check GitHub issues

## Advanced Configuration

### Custom Port

Edit systemd service file:
```bash
sudo nano /etc/systemd/system/water-tank-control.service
```

Modify ExecStart to include port:
```
ExecStart=/opt/water-tank-control/venv/bin/python /opt/water-tank-control/app.py --port 8000
```

### Auto-Restart on Failure

Already configured in systemd service:
- `Restart=always`
- `RestartSec=10`

### Log Rotation

Application uses Python's RotatingFileHandler:
- Max file size: 10KB
- Backup count: 10 files

For systemd logs:
```bash
sudo journalctl --vacuum-time=30d  # Keep 30 days
```
