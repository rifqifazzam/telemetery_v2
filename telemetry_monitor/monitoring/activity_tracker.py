"""
Activity tracking module for monitoring user activities during telemetry recording.
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime

class Activity:
    """Represents a single activity with timing information."""
    
    def __init__(self, name: str):
        self.name = name
        self.total_duration = 0.0  # Total accumulated seconds
        self.start_time = None  # When activity was last started
        self.is_active = False
        self.history = []  # List of (start_time, end_time) tuples
    
    def start(self):
        """Start or resume this activity."""
        if not self.is_active:
            self.start_time = time.time()
            self.is_active = True
    
    def pause(self):
        """Pause this activity and accumulate duration."""
        if self.is_active and self.start_time:
            duration = time.time() - self.start_time
            self.total_duration += duration
            self.history.append((self.start_time, time.time()))
            self.start_time = None
            self.is_active = False
    
    def get_current_duration(self) -> float:
        """Get current total duration including active time."""
        total = self.total_duration
        if self.is_active and self.start_time:
            total += time.time() - self.start_time
        return total
    
    def get_formatted_duration(self) -> str:
        """Get duration formatted as MM:SS or HH:MM:SS."""
        duration = self.get_current_duration()
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary for export."""
        return {
            'name': self.name,
            'total_duration': self.get_current_duration(),
            'formatted_duration': self.get_formatted_duration(),
            'history': [
                {
                    'start': datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S'),
                    'end': datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': end - start
                }
                for start, end in self.history
            ]
        }

class ActivityTracker:
    """Manages multiple activities and tracks which is currently active."""
    
    def __init__(self):
        self.activities: Dict[str, Activity] = {}
        self.current_activity: Optional[str] = None
        self.activity_order: List[str] = []  # Maintain insertion order
        self.reset()
    
    def add_activity(self, name: str) -> bool:
        """
        Add a new activity.
        
        Args:
            name: Name of the activity
            
        Returns:
            True if added successfully, False if already exists
        """
        if name in self.activities:
            return False
        
        self.activities[name] = Activity(name)
        self.activity_order.append(name)
        return True
    
    def set_active_activity(self, name: str) -> bool:
        """
        Set an activity as active (pauses current activity if any).
        
        Args:
            name: Name of the activity to activate
            
        Returns:
            True if successful, False if activity doesn't exist
        """
        if name not in self.activities:
            return False
        
        # Pause current activity if any
        if self.current_activity and self.current_activity in self.activities:
            self.activities[self.current_activity].pause()
        
        # Start new activity
        self.current_activity = name
        self.activities[name].start()
        return True
    
    def get_current_activity_name(self) -> Optional[str]:
        """Get the name of currently active activity."""
        return self.current_activity
    
    def get_activity(self, name: str) -> Optional[Activity]:
        """Get an activity by name."""
        return self.activities.get(name)
    
    def get_all_activities(self) -> List[Activity]:
        """Get all activities in insertion order."""
        return [self.activities[name] for name in self.activity_order if name in self.activities]
    
    def pause_current_activity(self):
        """Pause the currently active activity."""
        if self.current_activity and self.current_activity in self.activities:
            self.activities[self.current_activity].pause()
            self.current_activity = None
    
    def reset(self):
        """Reset all activities and clear tracking."""
        # Pause current activity if any
        if self.current_activity and self.current_activity in self.activities:
            self.activities[self.current_activity].pause()
        
        self.activities.clear()
        self.activity_order.clear()
        self.current_activity = None    
        
    def get_activity_summary(self) -> Dict[str, Any]:
        """Get summary of all activities for export."""
        return {
            'current_activity': self.current_activity,
            'activities': [activity.to_dict() for activity in self.get_all_activities()],
            'total_activities': len(self.activities)
        }
    
    def get_activity_for_timestamp(self, timestamp: float) -> Optional[str]:
        """
        Get which activity was active at a given timestamp.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            Activity name or None
        """
        for activity in self.get_all_activities():
            for start, end in activity.history:
                if start <= timestamp <= end:
                    return activity.name
            
            # Check if currently active
            if activity.is_active and activity.start_time and timestamp >= activity.start_time:
                return activity.name
        
        return None