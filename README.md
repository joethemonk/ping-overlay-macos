# Ping Overlay for macOS - Enhanced Menu Bar Network Monitor (with edits by JoeTheMonk)

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

A powerful and user-friendly macOS menu bar application that provides real-time network latency monitoring with rich statistics and customizable settings.

![Menu Bar Demo](https://via.placeholder.com/400x200?text=Ping+Overlay+Demo)

## ✨ Features

### 🎯 **Real-time Ping Monitoring**
- Live latency display in the menu bar with color-coded status indicators
- Visual feedback: 🟢 Excellent (<50ms) | 🟡 Good (<100ms) | 🟠 Fair (<200ms) | 🔴 Poor (≥200ms)
- Automatic timeout detection and error handling

### 📊 **Advanced Statistics**
- Min, Max, and Average latency tracking
- Packet loss percentage calculation
- Rolling statistics for the last 50 ping attempts
- History tracking with up to 100 recent pings

### ⚙️ **Flexible Configuration**
- **Multiple Target Hosts**: Google DNS (8.8.8.8), Cloudflare (1.1.1.1), OpenDNS, or custom hosts
- **Adjustable Refresh Rates**: 1, 2, 5, or 10-second intervals
- **Configurable Timeouts**: 1, 3, 5, or 10-second timeouts
- **Persistent Settings**: Configuration automatically saved and restored

### 🎮 **Control Features**
- Pause/Resume monitoring
- Reset statistics and history
- Toggle statistics display on/off
- About dialog with current configuration

### 🔧 **Technical Improvements**
- Threaded ping operations to prevent UI blocking
- Robust error handling and logging
- Host validation for custom targets
- Background operation (LSUIElement) - no dock icon
- Detailed error logs with timestamps

## 🚀 Quick Start

### Prerequisites
- macOS 10.14 or later
- Python 3.11+ (recommended)
- Administrator privileges may be required for ping operations

### Installation & Build

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd ping-overlay-macos
   ```

2. **Install Python dependencies**
   ```bash
   pip install rumps ping3 py2app
   ```

3. **Build the application**
   ```bash
   python setup.py py2app
   ```

4. **Launch the app**
   ```bash
   open dist/ping_app.app
   ```

5. **If macOS security blocks the app** (rare):
   ```bash
   xattr -d com.apple.quarantine dist/ping_app.app
   ```

6. **Set up auto-launch at login** (optional):
   ```bash
   ./setup_autostart.sh
   ```

## 🚀 Auto-Launch Setup

To have Ping Overlay start automatically when you log in:

### Quick Setup
```bash
# Run the auto-launch setup script
./setup_autostart.sh
```

This will:
- Copy the app to `/Applications/ping_app.app`
- Create a LaunchAgent to start the app at login
- Load the LaunchAgent immediately

### Manual Management
```bash
# Disable auto-launch
launchctl unload ~/Library/LaunchAgents/com.pingoverlay.autostart.plist

# Re-enable auto-launch
launchctl load ~/Library/LaunchAgents/com.pingoverlay.autostart.plist

# Remove auto-launch completely
./remove_autostart.sh
```

## 📱 Usage

### First Launch
- The app appears in your menu bar as "⏳ Starting..."
- Default configuration pings Google DNS (8.8.8.8) every 2 seconds
- Statistics are enabled by default

### Menu Options
- **Current Status**: Shows real-time ping results
- **Statistics Section**: Min/Max/Average latency and packet loss
- **Pause/Resume**: Temporarily stop monitoring
- **Reset Statistics**: Clear history and reset counters
- **Settings Menu**:
  - Target Host selection (preset or custom)
  - Refresh rate adjustment
  - Timeout configuration
  - Toggle statistics display
- **About**: View current configuration
- **Quit**: Exit the application

### Visual Indicators
| Icon | Status | Latency Range |
|------|--------|---------------|
| 🟢 | Excellent | < 50ms |
| 🟡 | Good | 50-99ms |
| 🟠 | Fair | 100-199ms |
| 🔴 | Poor | ≥ 200ms |
| ❌ | Error | Connection failed |
| ⏸️ | Paused | Monitoring paused |

## 🛠️ Configuration

### Settings File
Configuration is automatically saved to `~/.ping_overlay_config.json` with the following options:

```json
{
  "host": "8.8.8.8",
  "refresh_rate": 2,
  "timeout": 3,
  "show_stats": true,
  "sound_alerts": false,
  "alert_threshold": 500
}
```

### Preset Hosts
- **Google DNS**: 8.8.8.8 (default)
- **Cloudflare DNS**: 1.1.1.1
- **OpenDNS**: 208.67.222.222
- **Custom Host**: Enter any valid hostname or IP address

## 🔍 Troubleshooting

### Common Issues

**App won't start**
- Check Python version: `python --version` (should be 3.11+)
- Verify dependencies: `pip list | grep -E "(rumps|ping3)"`
- Check error logs in `/tmp/ping_app_error_*.log`

**Permission denied for ping**
- Some systems may require elevated privileges for ICMP packets
- Try running the built app with administrator privileges
- Alternative: Use network diagnostic tools to verify connectivity

**Build fails with py2app**
- Ensure py2app is properly installed: `pip install --upgrade py2app`
- Clean previous builds: `rm -rf build dist`
- Check Python environment setup

**Custom host not working**
- Verify the hostname resolves: `nslookup your-host.com`
- Check firewall settings that might block ICMP
- Try using IP address instead of hostname

### Debug Mode
Run the Python script directly for debugging:
```bash
python ping_app.py
```

## 🏗️ Dependencies

- **rumps**: macOS menu bar app framework
- **ping3**: Pure Python ICMP ping implementation  
- **py2app**: Python to macOS app packager

## 📋 System Requirements

- **OS**: macOS 10.14 Mojave or later
- **Python**: 3.11 or higher
- **RAM**: 50MB minimum
- **Disk**: 100MB for app bundle
- **Network**: Internet connection for ping targets

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup
```bash
git clone <repository-url>
cd ping-overlay-macos
pip install -r requirements.txt  # if requirements.txt exists
python ping_app.py  # Run directly for development
```

## 📄 License

This project is open source. See LICENSE file for details.

## 🙏 Acknowledgments

- Built with [rumps](https://github.com/jaredks/rumps) - Simple macOS menu bar apps
- Uses [ping3](https://github.com/kyan001/ping3) - Pure Python ping implementation
- Packaged with [py2app](https://py2app.readthedocs.io/) - Python to macOS app converter

---

**Version**: 2.0.0  
**Last Updated**: January 2024  
**Author**: Ping Overlay Team

For support or questions, please open an issue on the project repository.
