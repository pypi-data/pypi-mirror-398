#!/bin/bash
set -e

echo "Uninstalling NRD service for Linux..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo "Error: Cannot determine actual user. Please run with sudo as a regular user."
    exit 1
fi

echo "Uninstalling for user: $ACTUAL_USER"

SERVICE_NAME="nrd@$ACTUAL_USER.service"
SERVICE_FILE="/etc/systemd/system/nrd@.service"

# Check if the service exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "NRD service is not installed at: $SERVICE_FILE"
    exit 1
fi

# Stop the service
echo "Stopping service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# Disable the service
echo "Disabling service..."
systemctl disable "$SERVICE_NAME" 2>/dev/null || true

# Remove the service file
echo "Removing service file..."
rm "$SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

echo "✓ NRD service uninstalled successfully!"
echo ""
echo "Note: Logs are still available via journalctl if needed:"
echo "  sudo journalctl -u $SERVICE_NAME"
