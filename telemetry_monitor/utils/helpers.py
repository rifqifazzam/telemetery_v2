"""
Utility helper functions for the Telemetry Monitor application.
"""

import time
import math
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024**2:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value / (1024**2):.1f} MB"
    else:
        return f"{bytes_value / (1024**3):.1f} GB"


def calculate_distance(point1: tuple, point2: tuple) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default on division by zero."""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def debounce(delay: float = 0.1):
    """Decorator to debounce function calls."""
    def decorator(func):
        last_called = [0]
        timer = [None]

        def wrapper(*args, **kwargs):
            def call_function():
                func(*args, **kwargs)
                last_called[0] = time.time()
                timer[0] = None

            current_time = time.time()
            if current_time - last_called[0] >= delay:
                if timer[0] is not None:
                    timer[0].cancel()
                timer[0] = threading.Timer(delay, call_function)
                timer[0].start()

        return wrapper
    return decorator


def rate_limiter(max_calls: int, time_window: float):
    """Decorator to rate limit function calls."""
    def decorator(func):
        calls = []

        def wrapper(*args, **kwargs):
            current_time = time.time()

            # Remove calls outside the time window
            calls[:] = [call_time for call_time in calls if current_time - call_time < time_window]

            if len(calls) < max_calls:
                calls.append(current_time)
                return func(*args, **kwargs)
            else:
                raise Exception(f"Rate limit exceeded: {max_calls} calls per {time_window} seconds")

        return wrapper
    return decorator


def create_timestamp(format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Create a formatted timestamp."""
    return datetime.now().strftime(format_string)


def validate_platform() -> Dict[str, Any]:
    """Validate platform compatibility and return platform info."""
    import platform
    import sys

    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': sys.version,
        'is_windows': platform.system() == "Windows",
        'is_linux': platform.system() == "Linux",
        'is_macos': platform.system() == "Darwin"
    }


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_get(dictionary: Dict, keys: List[str], default: Any = None) -> Any:
    """Safely get nested dictionary values."""
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def deep_update(base_dict: Dict, update_dict: Dict) -> Dict:
    """Deep update dictionary with nested updates."""
    result = base_dict.copy()
    for key, value in update_dict.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_update(result[key], value)
        else:
            result[key] = value
    return result