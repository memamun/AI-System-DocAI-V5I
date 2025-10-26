#!/bin/bash
# Linux/macOS script to download embedding model for AI-System-DocAI

echo "============================================================"
echo "AI-System-DocAI - Model Download"
echo "============================================================"
echo

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Download the model
python3 download_model.py

echo
echo "Press Enter to exit..."
read

