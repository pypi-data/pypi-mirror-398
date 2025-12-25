#!/bin/bash
set -e

echo "Installing NRD service for macOS..."

# Get the current user
CURRENT_USER=$(whoami)
PLIST_FILE="li.problem.nrd.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Find Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Python 3 not found in PATH"
    exit 1
fi

echo "Using Python: $PYTHON_PATH"

# Create a temporary plist file with the correct paths
TEMP_PLIST=$(mktemp)
cat > "$TEMP_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>li.problem.nrd</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>-m</string>
        <string>nrd.nrd</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/tmp/nrd.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/nrd.error.log</string>
    
    <key>WorkingDirectory</key>
    <string>$HOME</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$HOME/.local/bin</string>
    </dict>
</dict>
</plist>
EOF

# Copy to LaunchAgents directory
cp "$TEMP_PLIST" "$LAUNCH_AGENTS_DIR/$PLIST_FILE"
rm "$TEMP_PLIST"

echo "Plist file installed to: $LAUNCH_AGENTS_DIR/$PLIST_FILE"

# Unload if already loaded (ignore errors)
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_FILE" 2>/dev/null || true

# Load the service
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_FILE"

echo "✓ NRD service installed and started successfully!"
echo "Logs available at:"
echo "  - /tmp/nrd.log"
echo "  - /tmp/nrd.error.log"
echo ""
echo "To check status: launchctl list | grep nrd"
echo "To stop: launchctl unload $LAUNCH_AGENTS_DIR/$PLIST_FILE"
echo "To start: launchctl load $LAUNCH_AGENTS_DIR/$PLIST_FILE"
