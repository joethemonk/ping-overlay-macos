#!/bin/bash

# Ping Overlay Auto-Launch Removal Script
# This script removes the auto-launch configuration for Ping Overlay

echo "🗑️  Ping Overlay Auto-Launch Removal"
echo "===================================="

PLIST_NAME="com.pingoverlay.autostart"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# Check if LaunchAgent exists
if [ ! -f "$PLIST_PATH" ]; then
    echo "❌ Auto-launch is not configured (LaunchAgent not found)"
    echo "   Looking for: $PLIST_PATH"
    exit 0
fi

echo "✅ Found LaunchAgent at $PLIST_PATH"

# Unload the LaunchAgent
echo "🔄 Unloading LaunchAgent..."
launchctl unload "$PLIST_PATH" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ LaunchAgent unloaded successfully"
else
    echo "⚠️  LaunchAgent may not have been loaded (this is usually fine)"
fi

# Remove the plist file
echo "🗑️  Removing LaunchAgent file..."
rm "$PLIST_PATH"

if [ $? -eq 0 ]; then
    echo "✅ LaunchAgent file removed successfully"
else
    echo "❌ Failed to remove LaunchAgent file"
    exit 1
fi

# Clean up any log files
echo "🧹 Cleaning up log files..."
rm -f /tmp/ping_overlay_launch.log /tmp/ping_overlay_launch_error.log

echo ""
echo "🎉 Auto-launch removal complete!"
echo "   Ping Overlay will no longer start automatically when you log in."
echo ""
echo "💡 Note: The app is still installed at /Applications/ping_app.app"
echo "   You can still launch it manually or re-enable auto-launch by running:"
echo "   ./setup_autostart.sh"

echo ""
echo "📋 To completely remove the app:"
echo "   rm -rf /Applications/ping_app.app"
