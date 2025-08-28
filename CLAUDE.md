# CLAUDE.md

## Key Development Conversations

These Claude/Gemini conversations were instrumental in building this app:

1. **"Rotate Wifi Script (Amtrak)"**  
   Created a script to rotate wifi between iPhone and Amtrak when each fails. Finished detection part but not rotating part. Won't do latter. Can re-use code.  
   https://gemini.google.com/app/fe52f9e69b031ac7

2. **"macOS Network Connection Automation Scripts" (8-28-25)**  
   Picking up from above script where figured out finicky way to detect iPhone and iPad hotspots  
   https://claude.ai/chat/6352b4fc-cb06-475b-81bc-d0b3a95418d8

3. **"Ping Time Color Monitoring Utility" (8-28-25)**  
   What led to the creation of this repo!  
   https://claude.ai/chat/0d7bec5c-61a8-413f-be9d-fb468aa8d4e5

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

```bash
# Install dependencies
pip install -r requirements.txt
# or install manually:
pip install rumps ping3 py2app

# Run the application directly (for development/debugging)
python ping_app.py

# Build the macOS app bundle
python setup.py py2app

# Launch the built app
open dist/ping_app.app

# If macOS security blocks the app (rare)
xattr -d com.apple.quarantine dist/ping_app.app

# Set up auto-launch at login
./setup_autostart.sh

# Remove auto-launch
./remove_autostart.sh
```

## Architecture Overview

**Ping Overlay** is a macOS menu bar application that monitors network latency using ICMP pings. Built with Python, it uses the `rumps` framework for macOS menu bar integration and `ping3` for network monitoring.

### Core Components

1. **Main Application (`ping_app.py`)**
   - `PingStatusBarApp` class extends `rumps.App` to create the menu bar interface
   - Uses threading via rumps.Timer for non-blocking ping operations
   - Maintains rolling statistics (last 50 pings) and full history (up to 100 entries)
   - Configuration persists to `~/.ping_overlay_config.json`

2. **Key Features**
   - Real-time latency monitoring with color-coded status indicators (🟢 <50ms, 🟡 <100ms, 🟠 <200ms, 🔴 ≥200ms)
   - Dynamic menu system with settings for host, refresh rate, timeout
   - Statistics tracking (min/max/avg latency, packet loss percentage)
   - Pause/resume functionality
   - Custom host validation using socket resolution

3. **Build System**
   - `setup.py` configures py2app packaging with LSUIElement=True (no dock icon)
   - Creates standalone .app bundle in `dist/` directory
   - Auto-launch scripts use macOS LaunchAgents for login startup

### Configuration System

The app uses a JSON config file at `~/.ping_overlay_config.json` with these settings:
- `host`: Target IP/hostname to ping
- `refresh_rate`: Seconds between pings (1, 2, 5, or 10)
- `timeout`: Ping timeout in seconds
- `show_stats`: Toggle statistics display in menu
- `sound_alerts`: (unused) Alert sounds feature
- `alert_threshold`: (unused) Latency threshold for alerts

### Threshold Configuration

The `ping_overlay_thresholds.json` file defines customizable latency thresholds (currently unused in code):
- Color indicators are hardcoded in `_update_ui()` method
- Could be modified to use this configuration file for dynamic thresholds

## Testing Approach

No formal test suite exists. Testing involves:
1. Running the app directly: `python ping_app.py`
2. Checking error logs at `/tmp/ping_app_error_*.log`
3. Verifying menu functionality manually
4. Testing build with `python setup.py py2app`


## More info on my fork of this specifically - Ping Overlay macOS - Project Context

## Folders / Paths

* My forked repo is located at https://github.com/joethemonk/ping-overlay-macos
* On my hard drive, it's at "/Users/eshashoua/Library/CloudStorage/GoogleDrive-eshashoua@gmail.com/My Drive/PythonDrive/wifi-tools/ping_overlay/ping-overlay-macos"
* My github username is joethemonk
* My name is Eric


## Overview
This is a fork of `Kafaquest/ping-overlay-macos` - a macOS menu bar application that displays real-time network latency monitoring with color-coded indicators. The app lives in the menu bar and shows ping times to various hosts with visual feedback based on connection quality.

## Why This Fork Exists
Eric (eshashoua@gmail.com) created this fork to customize the latency thresholds for monitoring terrible WiFi connections during Amtrak train trips between NYC and Boston. The default thresholds were too optimistic for train WiFi quality.

## Custom Threshold Requirements
The original thresholds need to be modified to:
- 🟢 **Excellent**: <120ms (originally <50ms)
- 🟡 **Good**: 120-249ms (originally 50-99ms)
- 🟠 **Fair**: 250-499ms (originally 100-199ms)
- 🔴 **Poor**: 500-999ms (originally ≥200ms)
- ❌ **Disconnected**: ≥1000ms (timeout)

## Project Structure
```
ping-overlay-macos/
├── ping_app.py           # Main application (needs threshold modifications)
├── setup.py              # py2app build configuration
├── requirements.txt      # Python dependencies (rumps, ping3, py2app)
├── setup_autostart.sh    # Script to enable auto-launch at login
├── remove_autostart.sh   # Script to disable auto-launch
└── README.md            # Documentation
```

## Key Files to Modify

### ping_app.py
The main application file containing:
- `get_status_icon()` function that determines which emoji to display based on latency
- Threshold values that need updating (search for: 50, 100, 200)
- Status text that shows threshold ranges

## Dependencies
- Python 3.11+
- rumps (macOS menu bar framework)
- ping3 (ICMP ping implementation)
- py2app (builds macOS .app bundles)

## Building & Installation

### Quick Build
```bash
# Install dependencies
pip3 install rumps ping3 py2app

# Build the app
python3 setup.py py2app

# Remove quarantine flag if needed
xattr -d com.apple.quarantine dist/ping_app.app

# Install to Applications
cp -r dist/ping_app.app /Applications/
```

### Development Testing
```bash
# Run directly without building
python3 ping_app.py
```

## Git Workflow

### Initial Setup
```bash
# This is Eric's fork
git clone https://github.com/joethemonk/ping-overlay-macos.git
cd ping-overlay-macos

# Add original repo as upstream for pulling updates
git remote add upstream https://github.com/Kafaquest/ping-overlay-macos.git
```

### Getting Updates from Original
```bash
# Fetch updates
git fetch upstream

# Merge them (watch for conflicts in threshold values)
git merge upstream/main

# Push to your fork
git push origin main
```

## Configuration Ideas for Future

Consider making thresholds configurable via JSON file at `~/.ping_overlay_config.json`:
```json
{
  "thresholds": {
    "excellent": 120,
    "good": 250,
    "fair": 500,
    "poor": 1000
  },
  "host": "8.8.8.8",
  "refresh_rate": 2
}
```

This would make merging upstream changes easier and allow runtime configuration without rebuilding.

## Testing Scenarios
- Normal home WiFi (baseline performance)
- Amtrak WiFi (high latency, frequent timeouts)
- Phone hotspot (variable performance)
- Coffee shop WiFi (moderate performance)

## Related Files
- Eric's original colored ping script: `~/ping_color.py` (command-line version)
- Uses similar color coding concept but runs in terminal

## Notes
- The app requires admin privileges for ICMP packets
- Default ping target is Google DNS (8.8.8.8)
- Can be changed to other hosts via menu
- Statistics show min/max/average and packet loss

## Purpose
Replace Eric's terminal-based `pingcolor` utility with a menu bar indicator for passive monitoring during train trips where connection quality is critical for remote work.

## TODO - Future Enhancements

### High Priority
- **Settings UI**: Add in-app settings dialog to adjust thresholds without rebuilding
  - Editable threshold values (excellent/good/fair/poor)
  - "Open at Login" checkbox with LaunchAgent integration
  - Host selection dropdown/text field
  - Refresh rate slider/dropdown
  
- **Auto-launch on network connection**: Automatically launch this app when connecting to iPad, iPhone, Amtrak WiFi or wired connections, and automatically quit when disconnecting
  - See conversations: https://gemini.google.com/app/fe52f9e69b031ac7 and https://claude.ai/chat/6352b4fc-cb06-475b-81bc-d0b3a95418d8
  - Reference file: "WIP_detect_launch_auto_(old_rotate_weak_wifi).sh" in this repo
  - Implement network change detection and conditional app launching
  
### Medium Priority  
- **Bundle threshold config**: Include `ping_overlay_config.json` in app bundle via setup.py
- **Better error handling**: Graceful fallbacks when network is completely unavailable
- **Statistics export**: CSV export of ping history for analysis

### Implementation Notes
- Current thresholds: 🟢<120ms, 🟡120-249ms, 🟠250-499ms, 🔴500-999ms, ❌≥1000ms
- App now has dock icon (removed LSUIElement=True from setup.py)
- Uses two-row display with color indicators and proper font sizing