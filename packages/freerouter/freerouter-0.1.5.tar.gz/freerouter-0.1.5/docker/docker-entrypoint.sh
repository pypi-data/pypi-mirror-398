#!/bin/bash
set -e

# Docker entrypoint for FreeRouter

CONFIG_DIR="/root/.config/freerouter"
PROVIDER_CONFIG="$CONFIG_DIR/providers.yaml"

# Check if providers.yaml exists
if [ ! -f "$PROVIDER_CONFIG" ]; then
    echo "ERROR: $PROVIDER_CONFIG not found!"
    echo "Please mount your config directory with providers.yaml"
    echo "Example: docker run -v ./config:/root/.config/freerouter ..."
    exit 1
fi

echo "Starting FreeRouter..."

# Start freerouter in background
freerouter start

# Wait for service to be ready
sleep 3

# Follow logs in foreground (keeps container running)
exec freerouter logs --requests
