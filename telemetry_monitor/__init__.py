"""
Telemetry Monitor - A modular system performance monitoring application.

This package provides real-time monitoring of system metrics, user input rates,
and active window information with screen recording capabilities.
"""

__version__ = "1.0.0"
__author__ = "Telemetry Monitor Team"

from .core.app import TelemetryMonitor
from .core.monitoring_controller import MonitoringController
from .gui.main_window import TelemetryGUI
from .monitoring.metrics_tracker import MetricsTracker
from .monitoring.input_monitor import InputMonitor
from .monitoring.system_monitor import SystemMonitor
from .monitoring.screen_recorder import ScreenRecorder
from .config.settings import Config

__all__ = [
    'TelemetryMonitor',
    'MonitoringController',
    'TelemetryGUI',
    'MetricsTracker',
    'InputMonitor',
    'SystemMonitor',
    'ScreenRecorder',
    'Config'
]