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

# Check if Mise is available and use it, otherwise fall back to manual venv
if command -v mise &> /dev/null; then
    echo "Using Mise-managed Python 3.11 environment..."
    # Mise will automatically use the correct Python version and venv
    # Just ensure dependencies are installed
    if [ ! -d ".venv" ]; then
        echo "Virtual environment not found. Running mise install..."
        mise install
    fi
    # Activate the Mise-managed venv
    source .venv/bin/activate
else
    # Fallback to manual venv management if Mise is not available
    echo "Mise not found. Using manual virtual environment..."
    if [ ! -d ".venv" ]; then
        echo "Virtual environment not found. Creating..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        source .venv/bin/activate
    fi
fi

echo "Python version: $(python --version)"
echo "Starting Flask application..."
echo "Access the application at: http://localhost:5000"
echo "Default credentials: admin / admin123"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python app.py
