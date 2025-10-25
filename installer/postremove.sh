#!/bin/bash
# Post-removal script for AI-System-DocAI V5I (Linux)

CONFIG_DIR="$HOME/.config/AI-System-DocAI"

echo "Cleaning up AI-System-DocAI..."

# Ask user if they want to remove config and data
read -p "Remove configuration and data files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Removing configuration directory..."
    rm -rf "$CONFIG_DIR"
    echo "✅ Configuration removed"
else
    echo "Configuration preserved at: $CONFIG_DIR"
fi

echo "✅ AI-System-DocAI uninstalled"

