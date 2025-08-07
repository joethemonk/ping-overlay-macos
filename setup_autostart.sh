#!/bin/bash

# Ping Overlay Auto-Launch Setup Script
# This script helps you set up the Ping Overlay app to start automatically when you log in

echo "🚀 Ping Overlay Auto-Launch Setup"
echo "=================================="

APP_NAME="ping_app"
APP_PATH="/Applications/ping_app.app"
PLIST_NAME="com.pingoverlay.autostart"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# Check if app exists in Applications
if [ ! -d "$APP_PATH" ]; then
    echo "❌ App not found at $APP_PATH"
    echo "   Please run: cp -R dist/ping_app.app /Applications/"
    exit 1
fi

echo "✅ Found app at $APP_PATH"

# Create LaunchAgent plist file
echo "📝 Creating LaunchAgent configuration..."

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>$APP_PATH</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>

    <key>LaunchOnlyOnce</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/ping_overlay_launch.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/ping_overlay_launch_error.log</string>
</dict>
</plist>
EOF

# Set proper permissions
chmod 644 "$PLIST_PATH"

echo "✅ Created LaunchAgent at $PLIST_PATH"

# Load the LaunchAgent
echo "🔄 Loading LaunchAgent..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true  # Ignore errors if not loaded
launchctl load "$PLIST_PATH"

if [ $? -eq 0 ]; then
    echo "✅ LaunchAgent loaded successfully!"
    echo ""
    echo "🎉 Setup Complete!"
    echo "   Ping Overlay will now start automatically when you log in."
    echo ""
    echo "📋 Management Commands:"
    echo "   Disable: launchctl unload $PLIST_PATH"
    echo "   Enable:  launchctl load $PLIST_PATH"
    echo "   Remove:  rm $PLIST_PATH"
    echo ""
    echo "📁 Log files (if needed for troubleshooting):"
    echo "   Output: /tmp/ping_overlay_launch.log"
    echo "   Errors: /tmp/ping_overlay_launch_error.log"
else
    echo "❌ Failed to load LaunchAgent"
    echo "   You can try loading it manually: launchctl load $PLIST_PATH"
fi

echo ""
echo "🚀 Want to test it now? The app should start automatically on your next login."
echo "   Or you can test it manually: launchctl start $PLIST_NAME"
