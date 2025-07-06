#!/bin/bash
# Deployment script for SPF Time Tracking Application

set -e

# Check if SSH target is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 user@hostname"
    echo "Example: $0 pi@raspberrypi.local"
    exit 1
fi

SSH_TARGET="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_FILE="$SCRIPT_DIR/dist/spf-time.tar.gz"

echo "Deploying SPF Time Tracking to $SSH_TARGET..."

# Check if distribution file exists
if [ ! -f "$DIST_FILE" ]; then
    echo "Distribution file not found: $DIST_FILE"
    echo "Please run ./build.sh first"
    exit 1
fi

# Test SSH connection
echo "Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_TARGET" "echo 'SSH connection successful'" 2>/dev/null; then
    echo "Error: Cannot connect to $SSH_TARGET"
    echo "Please ensure:"
    echo "  1. The target host is reachable"
    echo "  2. SSH key authentication is set up"
    echo "  3. The username and hostname are correct"
    exit 1
fi

# Create temporary directory on remote host
TEMP_DIR="/tmp/spf-time-deploy-$$"
echo "Creating temporary directory on remote host..."
ssh "$SSH_TARGET" "mkdir -p $TEMP_DIR"

# Copy distribution archive to remote host
echo "Copying application archive..."
scp "$DIST_FILE" "$SSH_TARGET:$TEMP_DIR/"

# Deploy on remote host
echo "Deploying application on remote host..."
ssh "$SSH_TARGET" << EOF
set -e

cd "$TEMP_DIR"
tar -xzf spf-time.tar.gz
cd spf-time

# Stop any running instance
echo "Stopping any running instances..."
pkill -f "spf_time.main" || true
sleep 2

# Backup existing settings and database if they exist
TARGET_DIR="\$HOME/spf-time"
if [ -d "\$TARGET_DIR" ]; then
    echo "Backing up existing configuration and data..."
    if [ -f "\$TARGET_DIR/settings.toml" ]; then
        cp "\$TARGET_DIR/settings.toml" "\$HOME/settings.toml.backup.\$(date +%Y%m%d_%H%M%S)"
        echo "Backed up settings.toml"
    fi
    if [ -f "\$TARGET_DIR/time_tracking.db" ]; then
        cp "\$TARGET_DIR/time_tracking.db" "\$HOME/time_tracking.db.backup.\$(date +%Y%m%d_%H%M%S)"
        echo "Backed up time_tracking.db"
    fi
fi

# Run installation
echo "Running installation script..."
bash install.sh

# Clean up
cd "\$HOME"
rm -rf "$TEMP_DIR"

echo "Deployment complete!"
echo ""
echo "Application status:"
echo "  - Installed to: \$HOME/spf-time"
echo "  - Autostart configured: Yes"
echo "  - Settings preserved: \$([ -f \$HOME/spf-time/settings.toml ] && echo 'Yes' || echo 'No (using defaults)')"
echo "  - Database preserved: \$([ -f \$HOME/spf-time/time_tracking.db ] && echo 'Yes' || echo 'No (will be created)')"
echo ""
echo "To start the application manually:"
echo "  \$HOME/spf-time/run.sh"
echo ""
echo "To generate reports:"
echo "  cd \$HOME/spf-time && uv run python generate_report.py <weeks>"
echo ""
echo "The application will start automatically on next boot."

EOF

echo ""
echo "Deployment to $SSH_TARGET completed successfully!"
echo ""
echo "Next steps on the Raspberry Pi:"
echo "  1. Reboot to test autostart: sudo reboot"
echo "  2. Or start manually: \$HOME/spf-time/run.sh"
echo "  3. Configure settings: edit \$HOME/spf-time/settings.toml"
echo ""
echo "To generate reports remotely:"
echo "  ssh $SSH_TARGET 'cd spf-time && uv run python generate_report.py 2'"