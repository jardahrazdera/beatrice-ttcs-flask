#!/bin/bash
# Development run script for local testing without hardware

echo "Starting Hot Water Tank Control System in DEVELOPMENT MODE"
echo "============================================================"
echo ""
echo "Using MOCK Evok client (simulated hardware)"
echo ""

# Set environment variables for development
export USE_MOCK_EVOK=true
export FLASK_DEBUG=true

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Starting Flask application..."
echo "Access the application at: http://localhost:5000"
echo "Default credentials: admin / admin123"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python app.py
