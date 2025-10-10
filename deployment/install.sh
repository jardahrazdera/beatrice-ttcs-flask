#!/bin/bash
# Installation script for Hot Water Tank Control System on Raspberry Pi

set -e  # Exit on error

echo "=========================================="
echo "Hot Water Tank Control System"
echo "Installation Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Do not run this script as root or with sudo"
    echo "The script will ask for sudo password when needed"
    exit 1
fi

# Configuration
INSTALL_DIR="/opt/water-tank-control"
SERVICE_NAME="water-tank-control"
REPO_URL="https://github.com/jardahrazdera/beatrice-ttcs-flask.git"

echo "Installation directory: $INSTALL_DIR"
echo ""

# Check if Evok is installed
echo "Checking for Evok installation..."
if ! systemctl is-active --quiet evok; then
    echo "WARNING: Evok service is not running"
    echo "Please ensure Evok is installed and running before continuing"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Evok is running"
fi
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update
echo ""

# Install dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv git
echo ""

# Create installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo "WARNING: Installation directory already exists"
    read -p "Remove existing installation and reinstall? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
        sudo rm -rf $INSTALL_DIR
    else
        echo "Installation cancelled"
        exit 1
    fi
fi

echo "Creating installation directory..."
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR
echo ""

# Clone or copy repository
if [ -d ".git" ]; then
    echo "Copying application files from current directory..."
    cp -r . $INSTALL_DIR/
    cd $INSTALL_DIR
    # Clean up development files
    rm -rf .git venv __pycache__ logs/*.log 2>/dev/null || true
else
    echo "Cloning repository from GitHub..."
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi
echo ""

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo ""

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs
echo ""

# Configure environment
echo "Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template"
    echo "Please edit $INSTALL_DIR/.env to configure your installation"
else
    echo ".env file already exists"
fi
echo ""

# Generate secret key
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
sed -i "s/change-this-to-a-random-secret-key-in-production/$SECRET_KEY/" .env
echo "Generated random SECRET_KEY"
echo ""

# Set proper permissions
echo "Setting permissions..."
chmod +x run_dev.sh
chmod 644 deployment/water-tank-control.service
echo ""

# Install systemd service
echo "Installing systemd service..."
sudo cp deployment/water-tank-control.service /etc/systemd/system/
sudo systemctl daemon-reload
echo ""

# Ask about nginx installation
read -p "Install and configure nginx reverse proxy? (Recommended for production) (y/N) " -n 1 -r
echo
INSTALL_NGINX=$REPLY
if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing nginx..."
    sudo apt-get install -y nginx

    echo "Configuring nginx..."
    sudo cp $INSTALL_DIR/deployment/nginx-water-tank.conf /etc/nginx/sites-available/water-tank-control

    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default

    # Enable water tank control site
    sudo ln -sf /etc/nginx/sites-available/water-tank-control /etc/nginx/sites-enabled/

    # Test nginx configuration
    if sudo nginx -t; then
        echo "✓ Nginx configuration valid"
        sudo systemctl enable nginx
        sudo systemctl restart nginx
        echo "✓ Nginx started"
    else
        echo "ERROR: Nginx configuration test failed"
        echo "Please check the configuration manually"
    fi
    echo ""
fi

# Enable and start service
read -p "Start application service now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    echo ""
    echo "Service started!"
    echo "Checking status..."
    sleep 2
    sudo systemctl status $SERVICE_NAME --no-pager
else
    echo "Service not started"
    echo "To start manually, run:"
    echo "  sudo systemctl enable $SERVICE_NAME"
    echo "  sudo systemctl start $SERVICE_NAME"
fi
echo ""

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Application installed to: $INSTALL_DIR"
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $INSTALL_DIR/.env"
echo "2. Check service status: sudo systemctl status $SERVICE_NAME"
echo "3. View logs: sudo journalctl -u $SERVICE_NAME -f"
if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    echo "4. Access web interface: http://$IP_ADDR"
    echo "   (Nginx reverse proxy on port 80)"
else
    echo "4. Access web interface: http://$IP_ADDR:5000"
    echo "   (Direct access on port 5000)"
fi
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "IMPORTANT: Change default password after first login!"
echo ""
echo "Useful commands:"
echo "  App Start:   sudo systemctl start $SERVICE_NAME"
echo "  App Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  App Restart: sudo systemctl restart $SERVICE_NAME"
echo "  App Status:  sudo systemctl status $SERVICE_NAME"
echo "  App Logs:    sudo journalctl -u $SERVICE_NAME -f"
if [[ $INSTALL_NGINX =~ ^[Yy]$ ]]; then
    echo ""
    echo "  Nginx Restart: sudo systemctl restart nginx"
    echo "  Nginx Status:  sudo systemctl status nginx"
    echo "  Nginx Logs:    sudo tail -f /var/log/nginx/water-tank-error.log"
fi
echo ""
