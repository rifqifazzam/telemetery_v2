"""
Input monitoring module for tracking keyboard and mouse interactions.
"""

import time
import math
from collections import deque
from typing import Dict, Callable, Optional, Tuple
from ..config.settings import Config
from ..utils.helpers import calculate_distance


class InputMonitor:
    """Handles monitoring of keyboard and mouse input events."""

    def __init__(self):
        self.key_count = 0
        self.mouse_click_count = 0
        self.mouse_scroll_count = 0
        self.mouse_distance = 0
        self.last_mouse_pos = None
        self.start_time = time.time()

        # History for rate calculations
        self.key_history = deque(maxlen=Config.HISTORY_MAXLEN)
        self.mouse_click_history = deque(maxlen=Config.HISTORY_MAXLEN)
        self.mouse_scroll_history = deque(maxlen=Config.HISTORY_MAXLEN)
        self._movement_distances = deque(maxlen=Config.HISTORY_MAXLEN)

        # Input listeners
        self.mouse_listener = None
        self.keyboard_listener = None

        # Callbacks for input events
        self.key_callback = None
        self.click_callback = None
        self.scroll_callback = None
        self.move_callback = None

    def set_callbacks(self, key_callback: Optional[Callable] = None,
                     click_callback: Optional[Callable] = None,
                     scroll_callback: Optional[Callable] = None,
                     move_callback: Optional[Callable] = None):
        """Set callback functions for input events."""
        self.key_callback = key_callback
        self.click_callback = click_callback
        self.scroll_callback = scroll_callback
        self.move_callback = move_callback

    def increment_key_count(self):
        """Increment keystroke counter."""
        self.key_count += 1
        self.key_history.append(time.time())
        if self.key_callback:
            self.key_callback()

    def increment_mouse_click(self):
        """Increment mouse click counter."""
        self.mouse_click_count += 1
        self.mouse_click_history.append(time.time())
        if self.click_callback:
            self.click_callback()

    def increment_mouse_scroll(self, delta):
        """Increment mouse scroll counter."""
        self.mouse_scroll_count += abs(delta)
        self.mouse_scroll_history.append(time.time())
        if self.scroll_callback:
            self.scroll_callback(delta)

    def update_mouse_distance(self, x, y):
        """Update mouse distance traveled."""
        if self.last_mouse_pos:
            distance = calculate_distance((x, y), self.last_mouse_pos)
            self.mouse_distance += distance
            self._movement_distances.append((time.time(), distance))
            if self.move_callback:
                self.move_callback(distance)
        self.last_mouse_pos = (x, y)

    def calculate_rates(self) -> Dict[str, float]:
        """Calculate rates from collected data."""
        current_time = time.time()
        time_window = Config.TIME_WINDOW
        cutoff_time = current_time - time_window

        # Count events in the time window
        key_events = sum(1 for timestamp in self.key_history if timestamp > cutoff_time)
        click_events = sum(1 for timestamp in self.mouse_click_history if timestamp > cutoff_time)
        scroll_events = sum(1 for timestamp in self.mouse_scroll_history if timestamp > cutoff_time)

        # Calculate rates per minute (normalize to 60 seconds)
        normalization_factor = 60.0 / time_window
        key_rate = key_events * normalization_factor
        click_rate = click_events * normalization_factor
        scroll_rate = scroll_events * normalization_factor

        # Calculate mouse movement rate
        movement_rate = self._calculate_movement_rate(cutoff_time)

        
        return {
            'key_rate': key_rate,
            'click_rate': click_rate,
            'scroll_rate': scroll_rate,
            'movement_rate': movement_rate
        }

    def _calculate_movement_rate(self, cutoff_time: float) -> float:
        """Calculate mouse movement rate in pixels per minute."""
        if not self._movement_distances:
            return 0

        # Sum distances moved since cutoff time
        recent_distance = sum(
            distance for timestamp, distance in self._movement_distances
            if timestamp > cutoff_time
        )

        return recent_distance  # Already pixels per minute (60-second window)

    def get_total_counts(self) -> Dict[str, int]:
        """Get total counts for all metrics."""
        return {
            'keys': int(self.key_count),
            'clicks': int(self.mouse_click_count),
            'scroll': int(self.mouse_scroll_count),
            'distance': int(self.mouse_distance)
        }

    def get_uptime_minutes(self) -> int:
        """Get application uptime in minutes."""
        return int((time.time() - self.start_time) / 60)

    def start_monitoring(self) -> bool:
        """Start input monitoring."""
        try:
            import pynput
            from pynput import mouse, keyboard

            def on_click(x, y, button, pressed):
                if pressed:
                    self.increment_mouse_click()

            def on_scroll(x, y, dx, dy):
                self.increment_mouse_scroll(dy)

            def on_move(x, y):
                self.update_mouse_distance(x, y)

            def on_press(key):
                self.increment_key_count()

            # Start listeners
            self.mouse_listener = mouse.Listener(
                on_click=on_click,
                on_scroll=on_scroll,
                on_move=on_move
            )

            self.keyboard_listener = keyboard.Listener(
                on_press=on_press
            )

            self.mouse_listener.start()
            self.keyboard_listener.start()

            return True

        except ImportError:
            print("pynput not available. Input monitoring disabled.")
            return False
        except Exception as e:
            print(f"Error setting up input monitoring: {e}")
            return False

    def stop_monitoring(self):
        """Stop input monitoring."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

    def reset_counters(self):
        """Reset all counters and history."""
        self.key_count = 0
        self.mouse_click_count = 0
        self.mouse_scroll_count = 0
        self.mouse_distance = 0
        self.last_mouse_pos = None

        self.key_history.clear()
        self.mouse_click_history.clear()
        self.mouse_scroll_history.clear()
        self._movement_distances.clear()

    def get_history_summary(self) -> Dict[str, int]:
        """Get summary of historical data."""
        current_time = time.time()
        time_window = Config.TIME_WINDOW
        cutoff_time = current_time - time_window

        return {
            'recent_keys': sum(1 for timestamp in self.key_history if timestamp > cutoff_time),
            'recent_clicks': sum(1 for timestamp in self.mouse_click_history if timestamp > cutoff_time),
            'recent_scroll': sum(1 for timestamp in self.mouse_scroll_history if timestamp > cutoff_time),
            'total_history_keys': len(self.key_history),
            'total_history_clicks': len(self.mouse_click_history),
            'total_history_scroll': len(self.mouse_scroll_history)
        }