#!/bin/bash
set -e

echo "Uninstalling NRD service for macOS..."

PLIST_FILE="li.problem.nrd.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$PLIST_FILE"

# Check if the service exists
if [ ! -f "$PLIST_PATH" ]; then
    echo "NRD service is not installed at: $PLIST_PATH"
    exit 1
fi

# Unload the service
echo "Stopping service..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# Remove the plist file
echo "Removing service file..."
rm "$PLIST_PATH"

# Optionally remove log files
read -p "Do you want to remove log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f /tmp/nrd.log /tmp/nrd.error.log
    echo "Log files removed."
fi

echo "✓ NRD service uninstalled successfully!"
