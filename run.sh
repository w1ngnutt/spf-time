#!/bin/bash
# SPF Time Tracking Application Launcher

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the application directory
cd "$SCRIPT_DIR"

# Set up environment for Raspberry Pi touchscreen
export DISPLAY=:0.0
export KIVY_WINDOW=sdl2
export KIVY_GL_BACKEND=gl

# Touchscreen environment variables
export SDL_MOUSEDEV=/dev/input/mice
export SDL_MOUSEDRV=TSLIB
export TSLIB_TSDEVICE=/dev/input/event0
export TSLIB_CALIBFILE=/etc/pointercal
export TSLIB_CONFFILE=/etc/ts.conf
export TSLIB_PLUGINDIR=/usr/lib/ts

# Disable mouse emulation to prevent conflicts
export KIVY_BCM_DISPMANX_ID=0

# Wait for X11 to be ready (important for autostart)
while ! xset q &>/dev/null; do
    sleep 1
done

# Function to install uv if it doesn't exist
install_uv() {
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
}

# Check if uv is available
if ! command -v uv &> /dev/null; then
    install_uv
fi

# Ensure uv is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Install/sync dependencies
uv sync

# Run the application
uv run python -m spf_time.main

# If the application exits with an error, wait a bit before potential auto-restart
if [ $? -ne 0 ]; then
    sleep 5
fi