import rumps
import threading
import time
import socket
from ping3 import ping
import json
import os
from datetime import datetime, timedelta
from Foundation import NSAttributedString, NSMutableAttributedString, NSMutableParagraphStyle
from AppKit import NSFont, NSFontAttributeName, NSParagraphStyleAttributeName, NSCenterTextAlignment, NSBaselineOffsetAttributeName

# Configuration file paths
CONFIG_FILE = os.path.expanduser("~/.ping_overlay_config.json")
THRESHOLDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ping_overlay_thresholds.json")

# Default thresholds (fallback if config file doesn't exist)
DEFAULT_THRESHOLDS = {
    "excellent": 120,
    "good": 250,
    "fair": 500,
    "poor": 1000
}

# Default configuration
DEFAULT_CONFIG = {
    "host": "8.8.8.8",
    "refresh_rate": 2,
    "timeout": 3,
    "show_stats": True,
    "sound_alerts": False,
    "alert_threshold": 500
}

# Load thresholds from file or use defaults
def load_thresholds():
    """Load thresholds from config file or use defaults"""
    # First try ping_overlay_config.json with thresholds key
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ping_overlay_config.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                data = json.load(f)
                if "thresholds" in data:
                    return data["thresholds"]
    except Exception as e:
        print(f"Error loading ping_overlay_config.json: {e}")
    
    # Then try ping_overlay_thresholds.json 
    try:
        if os.path.exists(THRESHOLDS_FILE):
            with open(THRESHOLDS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading thresholds: {e}, using defaults")
    
    return DEFAULT_THRESHOLDS.copy()

# Load thresholds at module level so they're available to all instances
THRESHOLDS = load_thresholds()

class PingStatusBarApp(rumps.App):
    def __init__(self):
        super(PingStatusBarApp, self).__init__("PingOverlay", icon=None, quit_button=None)
        
        # Load configuration
        self.config = self.load_config()

        # Initialize state
        self.title = "..."
        self.is_paused = False
        self.ping_history = []
        self.max_history = 100
        self.stats = {"min": None, "max": None, "avg": None, "packet_loss": 0}

        # Setup menu
        self.setup_menu()

        # Start ping monitoring immediately
        self.timer = None
        self.start_monitoring()

        # Perform first ping immediately
        self.title = "..."
        self.update_ping(None)

    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                # Ensure all required keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def create_attributed_title(self, value, unit, status_indicator="●"):
        """Create an attributed string with colored status indicator and different sized fonts for value and unit"""
        # Create: "value\n [indicator] unit" with proper spacing
        
        # Create paragraph style with center alignment
        paragraph_style = NSMutableParagraphStyle.alloc().init()
        paragraph_style.setAlignment_(NSCenterTextAlignment)
        paragraph_style.setLineSpacing_(-8.0)  # Tight line spacing
        paragraph_style.setMaximumLineHeight_(8.0)
        
        # Create mutable attributed string
        attr_string = NSMutableAttributedString.alloc().init()
        
        # Font sizes
        number_font = NSFont.systemFontOfSize_(12.0)
        unit_font = NSFont.systemFontOfSize_(8.0)
        indicator_font = NSFont.systemFontOfSize_(7.0)  # Even smaller indicator for bottom row
        
        # First row: just the number
        number_attributes = {
            NSFontAttributeName: number_font,
            NSParagraphStyleAttributeName: paragraph_style,
            NSBaselineOffsetAttributeName: -6.0
        }
        number_str = NSAttributedString.alloc().initWithString_attributes_(value + "\n", number_attributes)
        attr_string.appendAttributedString_(number_str)
        
        # Second row: properly spaced indicator and unit
        # Format: " [indicator] unit " for ms, " [indicator]  unit " for s
        bottom_row_attributes = {
            NSFontAttributeName: unit_font,
            NSParagraphStyleAttributeName: paragraph_style,
            NSBaselineOffsetAttributeName: -4.0
        }
        
        # Add space before indicator
        space_str = NSAttributedString.alloc().initWithString_attributes_(" ", bottom_row_attributes)
        attr_string.appendAttributedString_(space_str)
        
        # Add the indicator (colored dot or X)
        indicator_attributes = {
            NSFontAttributeName: indicator_font,
            NSParagraphStyleAttributeName: paragraph_style,
            NSBaselineOffsetAttributeName: -4.0
        }
        indicator_str = NSAttributedString.alloc().initWithString_attributes_(status_indicator, indicator_attributes)
        attr_string.appendAttributedString_(indicator_str)
        
        # Add space(s) between indicator and unit
        # Two spaces for seconds, one space for milliseconds
        spacing = "  " if unit == "s" else " "
        spacing_str = NSAttributedString.alloc().initWithString_attributes_(spacing, bottom_row_attributes)
        attr_string.appendAttributedString_(spacing_str)
        
        # Add the unit
        unit_str = NSAttributedString.alloc().initWithString_attributes_(unit, bottom_row_attributes)
        attr_string.appendAttributedString_(unit_str)
        
        # Add space after unit
        trailing_space = NSAttributedString.alloc().initWithString_attributes_(" ", bottom_row_attributes)
        attr_string.appendAttributedString_(trailing_space)
        
        return attr_string

    def setup_menu(self):
        """Setup the application menu"""
        # Current status
        self.status_item = rumps.MenuItem("Status: Initializing...", callback=None)
        self.menu.add(self.status_item)

        # Statistics
        if self.config["show_stats"]:
            self.menu.add(rumps.separator)
            self.stats_min = rumps.MenuItem("Min: --", callback=None)
            self.stats_max = rumps.MenuItem("Max: --", callback=None)
            self.stats_avg = rumps.MenuItem("Avg: --", callback=None)
            self.stats_loss = rumps.MenuItem("Loss: 0%", callback=None)
            self.menu.add(self.stats_min)
            self.menu.add(self.stats_max)
            self.menu.add(self.stats_avg)
            self.menu.add(self.stats_loss)

        self.menu.add(rumps.separator)

        # Control buttons
        self.pause_item = rumps.MenuItem("Pause", callback=self.toggle_pause)
        self.menu.add(self.pause_item)

        self.menu.add(rumps.MenuItem("Reset Statistics", callback=self.reset_stats))

        self.menu.add(rumps.separator)

        # Configuration submenu
        config_menu = rumps.MenuItem("Settings")

        # Host selection
        host_menu = rumps.MenuItem("Target Host")
        host_menu.add(rumps.MenuItem("Google DNS (8.8.8.8)", callback=lambda _: self.set_host("8.8.8.8")))
        host_menu.add(rumps.MenuItem("Cloudflare DNS (1.1.1.1)", callback=lambda _: self.set_host("1.1.1.1")))
        host_menu.add(rumps.MenuItem("OpenDNS (208.67.222.222)", callback=lambda _: self.set_host("208.67.222.222")))
        host_menu.add(rumps.separator)
        host_menu.add(rumps.MenuItem("Custom Host...", callback=self.set_custom_host))
        config_menu.add(host_menu)

        # Refresh rate
        rate_menu = rumps.MenuItem("Refresh Rate")
        for rate in [1, 2, 5, 10]:
            title = f"{rate} second{'s' if rate != 1 else ''}"
            if rate == self.config["refresh_rate"]:
                title += " ✓"
            rate_menu.add(rumps.MenuItem(title, callback=lambda _, r=rate: self.set_refresh_rate(r)))
        config_menu.add(rate_menu)

        # Timeout setting
        timeout_menu = rumps.MenuItem("Timeout")
        for timeout in [1, 3, 5, 10]:
            title = f"{timeout} second{'s' if timeout != 1 else ''}"
            if timeout == self.config["timeout"]:
                title += " ✓"
            timeout_menu.add(rumps.MenuItem(title, callback=lambda _, t=timeout: self.set_timeout(t)))
        config_menu.add(timeout_menu)

        config_menu.add(rumps.separator)
        stats_toggle = rumps.MenuItem("Show Statistics", callback=self.toggle_stats)
        if self.config["show_stats"]:
            stats_toggle.state = True
        config_menu.add(stats_toggle)

        self.menu.add(config_menu)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("About", callback=self.show_about))
        self.menu.add(rumps.MenuItem("Quit", callback=self.quit_app))

    def start_monitoring(self):
        """Start the ping monitoring timer"""
        if self.timer:
            self.timer.stop()

        # Start timer immediately instead of waiting for first interval
        self.timer = rumps.Timer(self.update_ping, self.config["refresh_rate"])
        self.timer.start()

    def update_ping(self, _):
        """Update ping status - runs in timer"""
        if self.is_paused:
            return

        # Perform ping directly - rumps handles threading
        try:
            latency = ping(self.config["host"], timeout=self.config["timeout"], unit='ms')
            self._update_ui(latency)
        except Exception as e:
            self._update_ui(None, str(e))



    def _update_ui(self, latency, error=None):
        """Update UI with ping results - runs on main thread"""
        current_time = datetime.now()

        if error:
            # Set attributed title directly on the NSStatusItem
            if hasattr(self, '_nsapp') and hasattr(self._nsapp, 'nsstatusitem'):
                self._nsapp.nsstatusitem.setAttributedTitle_(self.create_attributed_title("Err", "", "❌"))
            self.status_item.title = f"Status: Error - {error[:50]}"
            self.ping_history.append({"time": current_time, "latency": None, "error": error})
        elif latency is None:
            # Set attributed title directly on the NSStatusItem
            if hasattr(self, '_nsapp') and hasattr(self._nsapp, 'nsstatusitem'):
                self._nsapp.nsstatusitem.setAttributedTitle_(self.create_attributed_title("T/O", "", "❌"))
            self.status_item.title = f"Status: Timeout to {self.config['host']}"
            self.ping_history.append({"time": current_time, "latency": None, "timeout": True})
        else:
            ms = round(latency)

            # Update title with latency in two rows (number on top, unit below)
            # Using different font sizes for value and unit
            # Determine status indicator color based on thresholds
            if ms < THRESHOLDS["excellent"]:
                indicator = "🟢"
            elif ms < THRESHOLDS["good"]:
                indicator = "🟡"
            elif ms < THRESHOLDS["fair"]:
                indicator = "🟠"
            elif ms < THRESHOLDS["poor"]:
                indicator = "🔴"
            else:
                indicator = "❌"  # Red X emoji for >= poor threshold
            
            # Handle different display modes based on latency
            if ms >= 3000:
                # Over 3 seconds: just show the X with no numbers
                if hasattr(self, '_nsapp') and hasattr(self._nsapp, 'nsstatusitem'):
                    self._nsapp.nsstatusitem.setAttributedTitle_(self.create_attributed_title("", "", indicator))
            elif ms >= THRESHOLDS["poor"]:
                # Between poor threshold and 3 seconds: show in seconds format with X
                seconds = ms / 1000.0
                # Format with 1 decimal place (e.g., "1.2", "2.5")
                value = f"{seconds:.1f}"
                # Pad to ensure minimum width for 3 characters
                if len(value) < 3:
                    padding = " " * (3 - len(value))
                    value = padding + value
                # Set attributed title directly on the NSStatusItem
                if hasattr(self, '_nsapp') and hasattr(self._nsapp, 'nsstatusitem'):
                    self._nsapp.nsstatusitem.setAttributedTitle_(self.create_attributed_title(value, "s", indicator))
            else:
                # Show milliseconds without padding - just center naturally
                value = str(ms)
                # Set attributed title directly on the NSStatusItem
                if hasattr(self, '_nsapp') and hasattr(self._nsapp, 'nsstatusitem'):
                    self._nsapp.nsstatusitem.setAttributedTitle_(self.create_attributed_title(value, "ms", indicator))

            self.status_item.title = f"Status: {ms}ms to {self.config['host']}"
            self.ping_history.append({"time": current_time, "latency": ms})

        # Maintain history limit
        if len(self.ping_history) > self.max_history:
            self.ping_history = self.ping_history[-self.max_history:]

        # Update statistics
        self.update_statistics()

    def update_statistics(self):
        """Update ping statistics"""
        if not self.ping_history or not self.config["show_stats"]:
            return

        # Get successful pings from last 50 entries
        recent_pings = [entry for entry in self.ping_history[-50:]
                       if entry.get("latency") is not None]

        if recent_pings:
            latencies = [entry["latency"] for entry in recent_pings]
            self.stats["min"] = min(latencies)
            self.stats["max"] = max(latencies)
            self.stats["avg"] = sum(latencies) / len(latencies)

        # Calculate packet loss for last 50 attempts
        last_50 = self.ping_history[-50:]
        if last_50:
            failed = len([entry for entry in last_50
                         if entry.get("latency") is None])
            self.stats["packet_loss"] = (failed / len(last_50)) * 100

        # Update menu items
        if hasattr(self, 'stats_min'):
            self.stats_min.title = f"Min: {self.stats['min']:.0f}ms" if self.stats['min'] else "Min: --"
            self.stats_max.title = f"Max: {self.stats['max']:.0f}ms" if self.stats['max'] else "Max: --"
            self.stats_avg.title = f"Avg: {self.stats['avg']:.0f}ms" if self.stats['avg'] else "Avg: --"
            self.stats_loss.title = f"Loss: {self.stats['packet_loss']:.1f}%"

    def toggle_pause(self, sender):
        """Toggle pause/resume monitoring"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_item.title = "Resume"
            self.title = "Paused"
            self.status_item.title = "Status: Paused"
        else:
            self.pause_item.title = "Pause"
            self.title = "Resuming..."
            # Trigger an immediate ping when resuming
            self.update_ping(None)

    def reset_stats(self, sender):
        """Reset statistics and history"""
        self.ping_history.clear()
        self.stats = {"min": None, "max": None, "avg": None, "packet_loss": 0}
        if hasattr(self, 'stats_min'):
            self.stats_min.title = "Min: --"
            self.stats_max.title = "Max: --"
            self.stats_avg.title = "Avg: --"
            self.stats_loss.title = "Loss: 0%"

    def set_host(self, host):
        """Set ping target host"""
        self.config["host"] = host
        self.save_config()
        self.reset_stats(None)
        self.title = "Switching..."

    def set_custom_host(self, sender):
        """Set custom host via dialog"""
        response = rumps.Window(
            title="Custom Host",
            message="Enter hostname or IP address:",
            default_text=self.config["host"],
            cancel=True
        ).run()

        if response.clicked and response.text.strip():
            new_host = response.text.strip()
            # Basic validation
            if self.validate_host(new_host):
                self.set_host(new_host)
            else:
                rumps.alert("Invalid Host", "Please enter a valid hostname or IP address.")

    def validate_host(self, host):
        """Basic host validation"""
        try:
            socket.gethostbyname(host)
            return True
        except socket.gaierror:
            return False

    def set_refresh_rate(self, rate):
        """Set ping refresh rate"""
        self.config["refresh_rate"] = rate
        self.save_config()
        self.start_monitoring()  # Restart timer with new rate
        # Trigger an immediate ping with new rate
        self.update_ping(None)
        self.setup_menu()  # Refresh menu to show new selection

    def set_timeout(self, timeout):
        """Set ping timeout"""
        self.config["timeout"] = timeout
        self.save_config()
        self.setup_menu()  # Refresh menu to show new selection

    def toggle_stats(self, sender):
        """Toggle statistics display"""
        self.config["show_stats"] = not self.config["show_stats"]
        self.save_config()
        sender.state = self.config["show_stats"]
        # Rebuild menu to add/remove stats
        self.menu.clear()
        self.setup_menu()

    def show_about(self, sender):
        """Show about dialog"""
        rumps.alert(
            title="Ping Overlay for macOS",
            message="A simple menu bar app that monitors network latency.\n\n"
                   f"Current target: {self.config['host']}\n"
                   f"Refresh rate: {self.config['refresh_rate']} seconds\n"
                   f"Timeout: {self.config['timeout']} seconds\n\n"
                   f"Thresholds:\n"
                   f"  🟢 Excellent: <{THRESHOLDS['excellent']}ms\n"
                   f"  🟡 Good: {THRESHOLDS['excellent']}-{THRESHOLDS['good']-1}ms\n"
                   f"  🟠 Fair: {THRESHOLDS['good']}-{THRESHOLDS['fair']-1}ms\n"
                   f"  🔴 Poor: {THRESHOLDS['fair']}-{THRESHOLDS['poor']-1}ms\n"
                   f"  ❌ Timeout: ≥{THRESHOLDS['poor']}ms\n\n"
                   "© 2024 Ping Overlay App"
        )

    def quit_app(self, sender):
        """Quit the application"""
        if self.timer:
            self.timer.stop()
        rumps.quit_application()

if __name__ == "__main__":
    try:
        # Check if we can import required modules
        import rumps
        from ping3 import ping

        # Test ping capability
        test_ping = ping("8.8.8.8", timeout=1)
        if test_ping is None:
            print("Warning: Ping test failed. App may need elevated privileges on some systems.")

        app = PingStatusBarApp()
        app.run()

    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install with: pip install rumps ping3")
    except Exception as e:
        import traceback
        error_log = f"/tmp/ping_app_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(error_log, "w") as f:
            f.write(f"Ping Overlay App Error - {datetime.now()}\n")
            f.write("="*50 + "\n")
            traceback.print_exc(file=f)
        print(f"Error occurred. Log saved to: {error_log}")
