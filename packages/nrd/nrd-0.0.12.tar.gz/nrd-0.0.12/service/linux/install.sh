#!/bin/bash
set -e

echo "Installing NRD service for Linux..."

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

echo "Installing for user: $ACTUAL_USER"

# Find Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Python 3 not found in PATH"
    exit 1
fi

echo "Using Python: $PYTHON_PATH"

# Create the systemd service file
SERVICE_FILE="/etc/systemd/system/nrd@.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=NRD - Vite Dev Server Background Service
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i
ExecStart=$PYTHON_PATH -m nrd.nrd
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment
Environment="PATH=/usr/local/bin:/usr/bin:/bin:/home/%i/.local/bin"

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at: $SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

# Enable and start the service for the user
systemctl enable "nrd@$ACTUAL_USER.service"
systemctl start "nrd@$ACTUAL_USER.service"

echo "✓ NRD service installed and started successfully!"
echo ""
echo "To check status: sudo systemctl status nrd@$ACTUAL_USER"
echo "To view logs: sudo journalctl -u nrd@$ACTUAL_USER -f"
echo "To stop: sudo systemctl stop nrd@$ACTUAL_USER"
echo "To start: sudo systemctl start nrd@$ACTUAL_USER"
echo "To disable autostart: sudo systemctl disable nrd@$ACTUAL_USER"
