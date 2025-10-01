"""
Main application class for the Telemetry Monitor.
"""

import tkinter as tk
import threading
from PIL import Image, ImageDraw
import pystray
from .monitoring_controller import MonitoringController
from ..monitoring.metrics_tracker import MetricsTracker
from ..gui.main_window import TelemetryGUI
from ..config.settings import Config


class TelemetryMonitor:
    """Main telemetry monitoring class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.running = False
        self.paused = False
        self.icon = None

        # Initialize components
        self.metrics_tracker = MetricsTracker()
        self.monitoring_controller = MonitoringController(root, self.metrics_tracker)
        self.gui = TelemetryGUI(root, self.metrics_tracker)

        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create system tray icon
        self.setup_system_tray()

    def setup_system_tray(self):
        """Setup system tray icon and menu."""
        try:
            # Create menu items
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Hide", self.hide_window),
                pystray.MenuItem("Exit", self.exit_app)
            )

            # Create icon
            self.icon = pystray.Icon(
                "telemetry_monitor",
                self.create_icon_image(),
                "Telemetry Monitor",
                menu
            )

            # Start icon in a separate thread
            icon_thread = threading.Thread(target=self.icon.run, daemon=True)
            icon_thread.start()

        except Exception as e:
            print(f"Error setting up system tray: {e}")

    def create_icon_image(self):
        """Create a simple icon image for the system tray."""
        # Create a simple 64x64 icon with a blue background
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)

        # Draw a simple "T" for Telemetry
        draw.rectangle([20, 10, 44, 50], fill='white')
        draw.rectangle([24, 10, 40, 25], fill='blue')

        return image

    def start_monitoring(self):
        """Start the monitoring system."""
        self.monitoring_controller.start_monitoring()

    def pause_monitoring(self):
        """Pause the monitoring system."""
        self.monitoring_controller.pause_monitoring()

    def resume_monitoring(self):
        """Resume the monitoring system."""
        self.monitoring_controller.resume_monitoring()

    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_controller.stop_monitoring()

    def get_paused_status(self):
        """Get pause status."""
        return self.monitoring_controller.paused

    def show_window(self, icon=None, item=None):
        """Show the main window."""
        self.root.deiconify()
        self.root.lift()

    def hide_window(self, icon=None, item=None):
        """Hide the main window."""
        self.root.withdraw()

    def exit_app(self, icon=None, item=None):
        """Exit the application completely."""
        if self.icon:
            self.icon.stop()
        self.stop_monitoring()
        self.metrics_tracker.cleanup()
        
        if hasattr(self.gui, 'floating_button') and self.gui.floating_button:
            self.gui.floating_button.destroy()
        
        self.root.quit()
        self.root.destroy()

    def on_closing(self):
        """Handle window closing - minimize to tray instead."""
        self.hide_window()