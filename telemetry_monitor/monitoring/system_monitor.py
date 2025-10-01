"""
System monitoring module for tracking system performance metrics.
"""

import time
import platform
import psutil
from typing import Dict, Tuple, Optional
from ..config.settings import Config
from ..utils.helpers import safe_divide, validate_platform


class SystemMonitor:
    """Handles monitoring of system performance metrics."""

    def __init__(self):
        self.platform_info = validate_platform()
        self.start_time = time.time()

        # Network and disk tracking for rate calculations
        self.last_network_bytes = 0
        self.last_disk_bytes = 0
        self.last_update_time = time.time()

    def get_active_window_info(self) -> Tuple[str, str]:
        """Get active window information."""
        try:
            if self.platform_info['is_windows']:
                import win32gui
                import win32process

                hwnd = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                # Validate PID before using it
                if pid <= 0:
                    return "Unknown", "Invalid Process"

                process = psutil.Process(pid)
                app_name = process.name()

                window_title = win32gui.GetWindowText(hwnd)
                if not window_title:
                    window_title = "No Title"

                return app_name, window_title
            else:
                # For non-Windows systems
                return "Unknown", "Not supported"
        except Exception as e:
            print(f"Error getting active window: {e}")
            return "Unknown", "No Title"

    def get_cpu_info(self) -> Dict[str, float]:
        """Get CPU information including usage and frequency."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_freq = psutil.cpu_freq()
            cpu_speed_ghz = safe_divide(cpu_freq.current, 1000, 0) if cpu_freq else 0

            # Get CPU core count
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)

            # Get CPU load averages (Unix-like systems)
            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()

            return {
                'cpu_percent': cpu_percent,
                'cpu_speed_ghz': cpu_speed_ghz,
                'cpu_count_logical': cpu_count_logical,
                'cpu_count_physical': cpu_count_physical,
                'load_avg': load_avg
            }
        except Exception as e:
            print(f"Error getting CPU info: {e}")
            return {
                'cpu_percent': 0,
                'cpu_speed_ghz': 0,
                'cpu_count_logical': 0,
                'cpu_count_physical': 0,
                'load_avg': None
            }

    def get_memory_info(self) -> Dict[str, float]:
        """Get memory information including usage and totals."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            memory_used_gb = safe_divide(memory.used, 1024**3, 0)
            memory_total_gb = safe_divide(memory.total, 1024**3, 0)
            swap_used_gb = safe_divide(swap.used, 1024**3, 0)
            swap_total_gb = safe_divide(swap.total, 1024**3, 0)

            return {
                'memory_used_gb': memory_used_gb,
                'memory_total_gb': memory_total_gb,
                'memory_percent': memory.percent,
                'memory_available_gb': safe_divide(memory.available, 1024**3, 0),
                'swap_used_gb': swap_used_gb,
                'swap_total_gb': swap_total_gb,
                'swap_percent': swap.percent
            }
        except Exception as e:
            print(f"Error getting memory info: {e}")
            return {
                'memory_used_gb': 0,
                'memory_total_gb': 0,
                'memory_percent': 0,
                'memory_available_gb': 0,
                'swap_used_gb': 0,
                'swap_total_gb': 0,
                'swap_percent': 0
            }

    def get_disk_info(self) -> Dict[str, float]:
        """Get disk I/O and storage information."""
        try:
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = safe_divide(disk_io.read_bytes, 1024**2, 0) if disk_io else 0
            disk_write_mb = safe_divide(disk_io.write_bytes, 1024**2, 0) if disk_io else 0
            disk_bytes_sec = disk_read_mb + disk_write_mb

            # Disk usage for primary partition
            disk_usage = psutil.disk_usage('/')
            disk_used_gb = safe_divide(disk_usage.used, 1024**3, 0)
            disk_total_gb = safe_divide(disk_usage.total, 1024**3, 0)

            return {
                'disk_bytes_sec': disk_bytes_sec,
                'disk_read_mb': disk_read_mb,
                'disk_write_mb': disk_write_mb,
                'disk_used_gb': disk_used_gb,
                'disk_total_gb': disk_total_gb,
                'disk_percent': safe_divide(disk_usage.used, disk_usage.total, 0) * 100
            }
        except Exception as e:
            print(f"Error getting disk info: {e}")
            return {
                'disk_bytes_sec': 0,
                'disk_read_mb': 0,
                'disk_write_mb': 0,
                'disk_used_gb': 0,
                'disk_total_gb': 0,
                'disk_percent': 0
            }

    def get_network_info(self) -> Dict[str, float]:
        """Get network information including throughput."""
        try:
            network = psutil.net_io_counters()
            network_bytes_sent_mb = safe_divide(network.bytes_sent, 1024**2, 0)
            network_bytes_recv_mb = safe_divide(network.bytes_recv, 1024**2, 0)
            network_bytes_sec = network_bytes_sent_mb + network_bytes_recv_mb

            # Get network interface information
            net_io = psutil.net_io_counters(pernic=True)
            interfaces = {}
            for interface, stats in net_io.items():
                interfaces[interface] = {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv
                }

            return {
                'network_bytes_sec': network_bytes_sec,
                'network_bytes_sent_mb': network_bytes_sent_mb,
                'network_bytes_recv_mb': network_bytes_recv_mb,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv,
                'error_in': network.errin,
                'error_out': network.errout,
                'drop_in': network.dropin,
                'drop_out': network.dropout,
                'interfaces': interfaces
            }
        except Exception as e:
            print(f"Error getting network info: {e}")
            return {
                'network_bytes_sec': 0,
                'network_bytes_sent_mb': 0,
                'network_bytes_recv_mb': 0,
                'packets_sent': 0,
                'packets_recv': 0,
                'error_in': 0,
                'error_out': 0,
                'drop_in': 0,
                'drop_out': 0,
                'interfaces': {}
            }

    def get_system_info(self) -> Dict[str, float]:
        """Get comprehensive system information."""
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        disk_info = self.get_disk_info()
        network_info = self.get_network_info()

        return {
            **cpu_info,
            **memory_info,
            **disk_info,
            **network_info
        }

    def calculate_network_rate(self) -> float:
        """Calculate network throughput rate in MB/s."""
        current_time = time.time()
        network_info = self.get_network_info()
        current_network_bytes = network_info['network_bytes_sec']

        network_mbps = 0
        if self.last_network_bytes > 0:
            network_diff = current_network_bytes - self.last_network_bytes
            time_diff = current_time - self.last_update_time
            network_mbps = safe_divide(network_diff, time_diff, 0)

        self.last_network_bytes = current_network_bytes
        return network_mbps

    def calculate_disk_rate(self) -> float:
        """Calculate disk I/O rate in MB/s."""
        current_time = time.time()
        disk_info = self.get_disk_info()
        current_disk_bytes = disk_info['disk_bytes_sec']

        disk_mbps = 0
        if self.last_disk_bytes > 0:
            disk_diff = current_disk_bytes - self.last_disk_bytes
            time_diff = current_time - self.last_update_time
            disk_mbps = safe_divide(disk_diff, time_diff, 0)

        self.last_disk_bytes = current_disk_bytes
        return disk_mbps

    def update_rate_tracking(self):
        """Update the tracking for rate calculations."""
        self.last_update_time = time.time()

    def get_process_list(self, limit: int = 10) -> list:
        """Get list of top processes by CPU and memory usage."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # Sort by CPU usage
            cpu_top = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:limit]

            # Sort by memory usage
            mem_top = sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)[:limit]

            return {
                'top_cpu': cpu_top,
                'top_memory': mem_top
            }
        except Exception as e:
            print(f"Error getting process list: {e}")
            return {'top_cpu': [], 'top_memory': []}

    def get_system_uptime(self) -> float:
        """Get system uptime in seconds."""
        try:
            import datetime
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            current_time = datetime.datetime.now()
            return (current_time - boot_time).total_seconds()
        except Exception as e:
            print(f"Error getting system uptime: {e}")
            return 0

    def get_battery_info(self) -> Dict[str, float]:
        """Get battery information if available."""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'percent': battery.percent,
                    'secs_left': battery.secsleft,
                    'power_plugged': battery.power_plugged
                }
            else:
                return {}
        except Exception as e:
            print(f"Error getting battery info: {e}")
            return {}

    def get_temperature_info(self) -> Dict[str, float]:
        """Get temperature information if available."""
        try:
            temps = {}
            if hasattr(psutil, 'sensors_temperatures'):
                temp_data = psutil.sensors_temperatures()
                for name, entries in temp_data.items():
                    temps[name] = []
                    for entry in entries:
                        temps[name].append({
                            'label': entry.label or name,
                            'current': entry.current,
                            'high': entry.high,
                            'critical': entry.critical
                        })
            return temps
        except Exception as e:
            print(f"Error getting temperature info: {e}")
            return {}