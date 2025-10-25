#!/bin/bash
# Post-installation script for AI-System-DocAI V5I (Linux)

INSTALL_DIR="/opt/ai-system-docai"
CONFIG_DIR="$HOME/.config/AI-System-DocAI"

echo "Configuring AI-System-DocAI..."

# Create config directory
mkdir -p "$CONFIG_DIR"

# Create logs directory
mkdir -p "$INSTALL_DIR/logs"

# Create cache directory
mkdir -p "$INSTALL_DIR/cache"

# Create index directory
mkdir -p "$INSTALL_DIR/faiss_index"

# Set permissions
chmod 755 "$INSTALL_DIR/launcher.sh"
chmod 755 "$INSTALL_DIR/launcher.py"

# Create initial startup log
LOG_FILE="$INSTALL_DIR/logs/AI-System-DocAI_Startup.log"
cat > "$LOG_FILE" <<EOF
================================================================================
AI-System-DocAI V5I - Installed
Installation Date: $(date)
Installation Directory: $INSTALL_DIR
================================================================================

EOF

echo "✅ AI-System-DocAI configured successfully"
echo "Run 'ai-system-docai' or '/opt/ai-system-docai/launcher.sh' to start"

