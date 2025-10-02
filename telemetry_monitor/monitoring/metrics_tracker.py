"""
Metrics tracking and calculation module for the Telemetry Monitor.
"""

import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Any
from .input_monitor import InputMonitor
from .system_monitor import SystemMonitor
from .screen_recorder import ScreenRecorder
from ..config.settings import Config
from ..utils.helpers import create_timestamp
from .activity_tracker import ActivityTracker

class MetricsTracker:
    """Coordinates all metrics tracking and calculations."""

    def __init__(self):
        # Initialize monitoring components
        self.input_monitor = InputMonitor()
        self.system_monitor = SystemMonitor()
        self.screen_recorder = ScreenRecorder()
        self.activity_tracker = ActivityTracker()

        # Data logging
        self.telemetry_log = deque(maxlen=Config.MAX_LOG_ENTRIES)
        self.last_log_time = 0

        # Set up callbacks between components
        self._setup_callbacks()

    def _setup_callbacks(self):
        """Set up callbacks between monitoring components."""
        # Set up input monitoring callbacks
        self.input_monitor.set_callbacks()

    def get_input_rates(self) -> Dict[str, float]:
        """Get input rates from input monitor."""
        return self.input_monitor.calculate_rates()

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information from system monitor."""
        return self.system_monitor.get_system_info()

    def get_active_window_info(self) -> tuple:
        """Get active window information."""
        return self.system_monitor.get_active_window_info()

    def get_total_counts(self) -> Dict[str, int]:
        """Get total input counts."""
        return self.input_monitor.get_total_counts()

    def get_uptime_minutes(self) -> int:
        """Get application uptime in minutes."""
        return self.input_monitor.get_uptime_minutes()

    def get_network_rate(self) -> float:
        """Get network throughput rate in MB/s."""
        return self.system_monitor.calculate_network_rate()

    def get_disk_rate(self) -> float:
        """Get disk I/O rate in MB/s."""
        return self.system_monitor.calculate_disk_rate()

    def update_rate_tracking(self):
        """Update rate tracking calculations."""
        self.system_monitor.update_rate_tracking()

    def log_telemetry_data(self, display_data: Dict[str, Any]):
        """Log telemetry data for the table."""
        current_time = time.time()

        # Only log at configured interval to avoid flooding
        if current_time - self.last_log_time < Config.LOG_INTERVAL:
            return

        self.last_log_time = current_time

        log_entry = {
            'timestamp': create_timestamp(),
            'app_name': display_data['app_name'],
            'window_title': display_data['window_title'],
            'key_rate': display_data['key_rate'],
            'movement_rate': display_data['movement_rate'],
            'click_rate': display_data['click_rate'],
            'scroll_rate': display_data['scroll_rate'],
            'cpu_percent': display_data['cpu_percent'],
            'memory_percent': display_data['memory_percent'],
            'network_mbps': display_data['network_mbps'],
            'disk_mbps': display_data['disk_mbps'],
            'activity': self.activity_tracker.get_current_activity_name() or 'None',
            'rec_timestamp': self.screen_recorder.get_recording_timestamp()
        }

        self.telemetry_log.append(log_entry)

    def get_telemetry_log(self) -> List[Dict]:
        """Get all logged telemetry data."""
        return list(self.telemetry_log)

    def clear_telemetry_log(self):
        """Clear the telemetry log."""
        self.telemetry_log.clear()

    def get_export_data(self) -> List[List[str]]:
        """Get telemetry data formatted for export."""
        if not self.telemetry_log:
            return []

        # Convert deque to list and format for export
        export_data = []
        for entry in self.telemetry_log:
            export_data.append([
                entry['timestamp'],
                entry['app_name'],
                entry['window_title'],
                f"{entry['key_rate']:.2f}",
                f"{entry['movement_rate']:.2f}",
                f"{entry['click_rate']:.2f}",
                f"{entry['scroll_rate']:.2f}",
                f"{entry['cpu_percent']:.2f}",
                f"{entry['memory_percent']:.2f}",
                f"{entry['network_mbps']:.2f}",
                f"{entry['disk_mbps']:.2f}",
                entry.get('rec_timestamp', '')
            ])

        return export_data

    def start_input_monitoring(self) -> bool:
        """Start input monitoring."""
        return self.input_monitor.start_monitoring()

    def stop_input_monitoring(self):
        """Stop input monitoring."""
        self.input_monitor.stop_monitoring()

    def reset_input_counters(self):
        """Reset input monitoring counters."""
        self.input_monitor.reset_counters()

    def start_screen_recording(self, output_path: Optional[str] = None) -> tuple:
        """Start screen recording."""
        return self.screen_recorder.start_recording(output_path)

    def stop_screen_recording(self) -> tuple:
        """Stop screen recording."""
        return self.screen_recorder.stop_recording()

    def pause_screen_recording(self) -> tuple:
        """Pause screen recording."""
        return self.screen_recorder.pause_recording()

    def resume_screen_recording(self) -> tuple:
        """Resume screen recording."""
        return self.screen_recorder.resume_recording()

    def set_recording_screen(self, screen_id: int) -> tuple:
        """Set which screen to record."""
        return self.screen_recorder.set_screen(screen_id)

    def get_recording_status(self) -> Dict:
        """Get current screen recording status."""
        return self.screen_recorder.get_recording_status()

    @property
    def available_screens(self) -> List[Dict]:
        """Get available screens for recording."""
        return self.screen_recorder.get_available_screens()

    def get_input_history_summary(self) -> Dict[str, int]:
        """Get summary of input history."""
        return self.input_monitor.get_history_summary()

    def get_process_list(self, limit: int = 10) -> Dict:
        """Get list of top processes."""
        return self.system_monitor.get_process_list(limit)

    def get_system_uptime(self) -> float:
        """Get system uptime in seconds."""
        return self.system_monitor.get_system_uptime()

    def get_battery_info(self) -> Dict[str, float]:
        """Get battery information if available."""
        return self.system_monitor.get_battery_info()

    def get_temperature_info(self) -> Dict[str, float]:
        """Get temperature information if available."""
        return self.system_monitor.get_temperature_info()

    def cleanup(self):
        """Clean up all monitoring resources."""
        self.stop_input_monitoring()
        self.screen_recorder.cleanup()
        self.activity_tracker.pause_current_activity()

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics data for display update."""
        # Get input rates
        input_rates = self.get_input_rates()

        # Get system info
        system_info = self.get_system_info()

        # Get active window info
        app_name, window_title = self.get_active_window_info()

        # Get network and disk rates
        network_mbps = self.get_network_rate()
        disk_mbps = self.get_disk_rate()

        result = {
            'app_name': app_name,
            'window_title': window_title,
            'key_rate': input_rates.get('key_rate', 0),
            'movement_rate': input_rates.get('movement_rate', 0),
            'click_rate': input_rates.get('click_rate', 0),
            'scroll_rate': input_rates.get('scroll_rate', 0),
            'cpu_percent': system_info.get('cpu_percent', 0),
            'memory_percent': system_info.get('memory_percent', 0),
            'network_mbps': network_mbps,
            'disk_mbps': disk_mbps
        }

        return result

    def get_system_summary(self) -> Dict[str, Any]:
        """Get a comprehensive system summary."""
        return {
            'platform': self.system_monitor.platform_info,
            'uptime': {
                'application': self.get_uptime_minutes(),
                'system': self.get_system_uptime()
            },
            'input': {
                'totals': self.get_total_counts(),
                'rates': self.get_input_rates(),
                'history': self.get_input_history_summary()
            },
            'system': {
                'cpu': self.system_monitor.get_cpu_info(),
                'memory': self.system_monitor.get_memory_info(),
                'disk': self.system_monitor.get_disk_info(),
                'network': self.system_monitor.get_network_info()
            },
            'recording': self.get_recording_status(),
            'log_size': len(self.telemetry_log),
            'process name': self.activity_tracker.get_activity_summary(),
        }