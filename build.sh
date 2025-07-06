#!/bin/bash
# Build script for SPF Time Tracking Application

set -e  # Exit on any error

echo "Building SPF Time Tracking Application..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_DIR="build"
DIST_DIR="dist"

# Clean previous build
echo "Cleaning previous build..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Create application bundle
echo "Creating application bundle..."
APP_BUNDLE="$BUILD_DIR/spf-time"
mkdir -p "$APP_BUNDLE"

# Copy application files (excluding cache)
echo "Copying application files..."
rsync -av --exclude='__pycache__' --exclude='*.pyc' spf_time/ "$APP_BUNDLE/spf_time/"
cp pyproject.toml "$APP_BUNDLE/"
cp generate_report.py "$APP_BUNDLE/"
cp run.sh "$APP_BUNDLE/"
cp spf-time.desktop "$APP_BUNDLE/"
cp README.md "$APP_BUNDLE/"

# Copy example settings (will not overwrite existing)
echo "Copying example configuration..."
cp settings.toml "$APP_BUNDLE/settings.toml.example"

# Create a simple icon (placeholder)
echo "Creating application icon..."
cat > "$APP_BUNDLE/icon.png.txt" << 'EOF'
# Placeholder for application icon
# Replace this file with an actual icon.png file
# Recommended size: 48x48 or 64x64 pixels
EOF

# Create installation script
echo "Creating installation script..."
cat > "$APP_BUNDLE/install.sh" << 'EOF'
#!/bin/bash
# Installation script for SPF Time Tracking

set -e

TARGET_DIR="$HOME/spf-time"

echo "Installing SPF Time Tracking to $TARGET_DIR..."

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy files (preserving existing settings.toml and time_tracking.db)
echo "Copying application files..."
cp -r spf_time/ "$TARGET_DIR/" 2>/dev/null || true
cp pyproject.toml "$TARGET_DIR/" 2>/dev/null || true
cp generate_report.py "$TARGET_DIR/" 2>/dev/null || true
cp run.sh "$TARGET_DIR/" 2>/dev/null || true
cp README.md "$TARGET_DIR/" 2>/dev/null || true

# Copy example settings if settings.toml doesn't exist
if [ ! -f "$TARGET_DIR/settings.toml" ]; then
    echo "Creating initial settings.toml..."
    cp settings.toml.example "$TARGET_DIR/settings.toml"
else
    echo "Preserving existing settings.toml"
fi

# Copy icon if it exists
if [ -f "icon.png" ]; then
    cp icon.png "$TARGET_DIR/"
fi

# Make run script executable
chmod +x "$TARGET_DIR/run.sh"

# Install/update desktop file for autostart
echo "Setting up autostart..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Update desktop file with correct paths
sed "s|/home/pi/spf-time|$TARGET_DIR|g" spf-time.desktop > "$AUTOSTART_DIR/spf-time.desktop"

# Also install to applications menu
APPLICATIONS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPLICATIONS_DIR"
cp "$AUTOSTART_DIR/spf-time.desktop" "$APPLICATIONS_DIR/"

echo "Installation complete!"
echo "Application installed to: $TARGET_DIR"
echo "Autostart configured in: $AUTOSTART_DIR"
echo ""
echo "To run manually: $TARGET_DIR/run.sh"
echo "To generate reports: cd $TARGET_DIR && uv run python generate_report.py <weeks>"
echo ""
echo "The application will start automatically on next boot."
EOF

chmod +x "$APP_BUNDLE/install.sh"

# Create archive
echo "Creating distribution archive..."
cd "$BUILD_DIR"
tar -czf "../$DIST_DIR/spf-time.tar.gz" spf-time/
cd ..

echo "Build complete!"
echo "Distribution archive: $DIST_DIR/spf-time.tar.gz"
echo ""
echo "To deploy to Raspberry Pi:"
echo "  ./deploy.sh user@raspberry-pi-hostname"