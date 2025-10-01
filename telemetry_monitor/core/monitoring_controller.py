"""
Main monitoring controller that orchestrates all monitoring activities.
"""

import time
import threading
import tkinter as tk
from typing import Dict, Any, Optional
from ..monitoring.metrics_tracker import MetricsTracker
from ..config.settings import Config


class MonitoringController:
    """Controls the monitoring loop and coordinates all monitoring activities."""

    def __init__(self, root: tk.Tk, metrics_tracker: MetricsTracker):
        self.root = root
        self.metrics_tracker = metrics_tracker
        self.running = False
        self.paused = False
        self.monitoring_thread = None

        # Rate tracking
        self.last_network_bytes = 0
        self.last_disk_bytes = 0
        self.last_time = time.time()

    def start_monitoring(self):
        """Start the monitoring system."""
        if self.running:
            return
        
        # Reset logs
        self.metrics_tracker.clear_telemetry_log()

        self.running = True
        self.paused = False

        # Start input monitoring
        self.metrics_tracker.start_input_monitoring()

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def pause_monitoring(self):
        """Pause the monitoring system."""
        if not self.running:
            return

        self.paused = True

    def resume_monitoring(self):
        """Resume the monitoring system."""
        if not self.running:
            return

        self.paused = False

    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.running = False
        self.paused = False

        # Stop input monitoring
        self.metrics_tracker.stop_input_monitoring()

        # Wait for monitoring thread to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)

    def monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            try:
                current_time = time.time()

                # Get system information
                system_info = self.metrics_tracker.get_system_info()

                # Get active window info
                app_name, window_title = self.metrics_tracker.get_active_window_info()

                # Calculate network and disk rates
                network_mbps = 0
                disk_mbps = 0

                if self.last_network_bytes > 0:
                    network_diff = system_info['network_bytes_sec'] - self.last_network_bytes
                    network_mbps = network_diff / (current_time - self.last_time)

                if self.last_disk_bytes > 0:
                    disk_diff = system_info['disk_bytes_sec'] - self.last_disk_bytes
                    disk_mbps = disk_diff / (current_time - self.last_time)

                # Calculate input rates
                rates = self.metrics_tracker.get_input_rates()

                # Prepare display data
                display_data = {
                    'app_name': app_name,
                    'window_title': window_title,
                    'key_rate': rates['key_rate'],
                    'click_rate': rates['click_rate'],
                    'scroll_rate': rates['scroll_rate'],
                    'movement_rate': rates['movement_rate'],
                    'cpu_percent': system_info['cpu_percent'],
                    'cpu_speed_ghz': system_info['cpu_speed_ghz'],
                    'memory_percent': system_info['memory_percent'],
                    'memory_used_gb': system_info['memory_used_gb'],
                    'memory_total_gb': system_info['memory_total_gb'],
                    'network_mbps': network_mbps,
                    'disk_mbps': disk_mbps
                }

                # Update display in main thread - only if not running to avoid conflicts
                if hasattr(self.root, 'gui') and not hasattr(self.root, '_gui_update_scheduled'):
                    self.root.after(0, lambda: self.root.gui.update_display(display_data))
                    # Set flag to prevent multiple updates
                    self.root._gui_update_scheduled = True
                    # Clear flag after delay
                    self.root.after(100, lambda: delattr(self.root, '_gui_update_scheduled') if hasattr(self.root, '_gui_update_scheduled') else None)

                # Log telemetry data
                self.metrics_tracker.log_telemetry_data(display_data)

                # Update last values
                self.last_network_bytes = system_info['network_bytes_sec']
                self.last_disk_bytes = system_info['disk_bytes_sec']
                self.last_time = current_time

                # Update rate tracking
                self.metrics_tracker.update_rate_tracking()

                # Sleep for monitoring interval (now longer for better performance)
                time.sleep(Config.MONITORING_INTERVAL)

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(1)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'running': self.running,
            'paused': self.paused,
            'uptime': time.time() - self.last_time if self.running else 0,
            'input_monitoring_active': self.metrics_tracker.input_monitor.mouse_listener is not None
        }

    def reset_monitoring(self):
        """Reset monitoring data and counters."""
        self.metrics_tracker.reset_input_counters()
        self.metrics_tracker.clear_telemetry_log()

        # Reset rate tracking
        self.last_network_bytes = 0
        self.last_disk_bytes = 0
        self.last_time = time.time()