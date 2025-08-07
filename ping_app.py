import rumps
import threading
import time
import socket
from ping3 import ping
import json
import os
from datetime import datetime, timedelta

# Configuration file path
CONFIG_FILE = os.path.expanduser("~/.ping_overlay_config.json")

# Default configuration
DEFAULT_CONFIG = {
    "host": "8.8.8.8",
    "refresh_rate": 2,
    "timeout": 3,
    "show_stats": True,
    "sound_alerts": False,
    "alert_threshold": 500
}

class PingStatusBarApp(rumps.App):
    def __init__(self):
        super(PingStatusBarApp, self).__init__("PingOverlay", icon=None, quit_button=None)

        # Load configuration
        self.config = self.load_config()

        # Initialize state
        self.title = "⏳ Starting..."
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
        self.title = "⏳ Pinging..."
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
            self.title = "❌ Error"
            self.status_item.title = f"Status: Error - {error[:50]}"
            self.ping_history.append({"time": current_time, "latency": None, "error": error})
        elif latency is None:
            self.title = "🔴 Timeout"
            self.status_item.title = f"Status: Timeout to {self.config['host']}"
            self.ping_history.append({"time": current_time, "latency": None, "timeout": True})
        else:
            ms = round(latency)

            # Update title with status and latency
            if ms < 50:
                self.title = f"🟢 {ms}ms"
            elif ms < 100:
                self.title = f"🟡 {ms}ms"
            elif ms < 200:
                self.title = f"🟠 {ms}ms"
            else:
                self.title = f"🔴 {ms}ms"

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
            self.title = "⏸️ Paused"
            self.status_item.title = "Status: Paused"
        else:
            self.pause_item.title = "Pause"
            self.title = "▶️ Resuming..."
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
        self.title = "⏳ Switching..."

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
