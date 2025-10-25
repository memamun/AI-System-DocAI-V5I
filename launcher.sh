#!/bin/bash
# Linux/macOS Launcher for AI-System-DocAI V5I
# Handles venv setup and application launch

set -e

APP_NAME="AI-System-DocAI"
APP_VERSION="5I.2025"
MIN_PYTHON_VERSION="3.8"

echo "============================================================"
echo "$APP_NAME V$APP_VERSION - Enterprise Edition (Linux/macOS)"
echo "============================================================"
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found"
    echo "Please install Python $MIN_PYTHON_VERSION or later"
    exit 1
fi

# Get Python version
PY_VERSION=$(python3 --version | awk '{print $2}')
echo "[INFO] Python version: $PY_VERSION"

# Create logs directory
mkdir -p logs

# Log startup
LOG_FILE="logs/${APP_NAME}_Startup.log"
{
    echo "================================================================================"
    echo "$APP_NAME V$APP_VERSION - Linux/macOS Launcher"
    echo "Timestamp: $(date)"
    echo "Python Version: $PY_VERSION"
    echo "================================================================================"
    echo
} | tee -a "$LOG_FILE"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv .venv
    echo "[SUCCESS] Virtual environment created"
else
    echo "[INFO] Virtual environment found"
fi

# Activate virtual environment
source .venv/bin/activate

# Check for requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] requirements.txt not found"
    exit 1
fi

# Install/upgrade pip
echo "[INFO] Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install dependencies
echo "[INFO] Installing dependencies..."
python -m pip install -r requirements.txt --quiet || echo "[WARNING] Some dependencies failed to install"

echo
echo "[INFO] Launching $APP_NAME..."
echo "============================================================"
echo

# Launch the application
python main.py | tee -a "$LOG_FILE"

# Deactivate virtual environment
deactivate

echo
echo "============================================================"
echo "Application closed"
echo "============================================================"

