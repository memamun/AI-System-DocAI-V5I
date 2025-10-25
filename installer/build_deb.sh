#!/bin/bash
# Build Debian package for AI-System-DocAI V5I
# Requires: fpm (gem install fpm)

set -e

APP_NAME="ai-system-docai"
APP_VERSION="5I.2025"
APP_DESCRIPTION="Offline AI-assisted document reasoning system with PyQt6 GUI"
APP_VENDOR="AI-System-Solutions"
APP_URL="https://github.com/ai-system-solutions/docai-v5i"
INSTALL_PREFIX="/opt/ai-system-docai"

echo "============================================================"
echo "Building Debian package for $APP_NAME"
echo "============================================================"
echo

# Check for FPM
if ! command -v fpm &> /dev/null; then
    echo "[ERROR] FPM not found. Install with: gem install fpm"
    exit 1
fi

# Check for required tools
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build_deb"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create directory structure
mkdir -p "$BUILD_DIR$INSTALL_PREFIX"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/usr/local/bin"

# Copy application files
echo "[INFO] Copying application files..."
cp -r "$PROJECT_DIR/main.py" "$BUILD_DIR$INSTALL_PREFIX/"
cp -r "$PROJECT_DIR/launcher.py" "$BUILD_DIR$INSTALL_PREFIX/"
cp -r "$PROJECT_DIR/launcher.sh" "$BUILD_DIR$INSTALL_PREFIX/"
cp -r "$PROJECT_DIR/requirements.txt" "$BUILD_DIR$INSTALL_PREFIX/"
cp -r "$PROJECT_DIR/src" "$BUILD_DIR$INSTALL_PREFIX/"
cp -r "$PROJECT_DIR/assets" "$BUILD_DIR$INSTALL_PREFIX/"

# Copy README and LICENSE
if [ -f "$PROJECT_DIR/README.md" ]; then
    cp "$PROJECT_DIR/README.md" "$BUILD_DIR$INSTALL_PREFIX/"
fi
if [ -f "$PROJECT_DIR/LICENSE" ]; then
    cp "$PROJECT_DIR/LICENSE" "$BUILD_DIR$INSTALL_PREFIX/"
fi

# Make launcher executable
chmod +x "$BUILD_DIR$INSTALL_PREFIX/launcher.sh"
chmod +x "$BUILD_DIR$INSTALL_PREFIX/launcher.py"

# Create desktop entry
cat > "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=AI-System-DocAI
Comment=$APP_DESCRIPTION
Exec=$INSTALL_PREFIX/launcher.sh
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Office;Utility;Education;
Keywords=AI;document;search;RAG;
EOF

# Copy icon if available
if [ -f "$PROJECT_DIR/assets/app-icon.ico" ]; then
    # Convert ICO to PNG if ImageMagick is available
    if command -v convert &> /dev/null; then
        convert "$PROJECT_DIR/assets/app-icon.ico" -resize 256x256 "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png" || true
    fi
fi

# Create symlink
ln -s "$INSTALL_PREFIX/launcher.sh" "$BUILD_DIR/usr/local/bin/$APP_NAME"

# Build .deb package
echo "[INFO] Building .deb package..."
fpm -s dir -t deb \
    -n "$APP_NAME" \
    -v "$APP_VERSION" \
    --description "$APP_DESCRIPTION" \
    --vendor "$APP_VENDOR" \
    --url "$APP_URL" \
    --license "MIT" \
    --category "office" \
    --architecture "amd64" \
    --depends "python3 (>= 3.8)" \
    --depends "python3-venv" \
    --depends "python3-pip" \
    --after-install "$SCRIPT_DIR/postinstall.sh" \
    --after-remove "$SCRIPT_DIR/postremove.sh" \
    -C "$BUILD_DIR" \
    -p "$PROJECT_DIR/dist/${APP_NAME}_${APP_VERSION}_amd64.deb" \
    .

echo
echo "============================================================"
echo "✅ Debian package built successfully!"
echo "Location: $PROJECT_DIR/dist/${APP_NAME}_${APP_VERSION}_amd64.deb"
echo "============================================================"

