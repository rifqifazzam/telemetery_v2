"""
Screen recording module for capturing screen activity.
"""

import time
import threading
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from ..config.settings import Config
from ..utils.helpers import format_duration

# Check if screen recording dependencies are available
try:
    import cv2
    import numpy as np
    import pyautogui
    SCREEN_RECORDING_AVAILABLE = True
except ImportError:
    SCREEN_RECORDING_AVAILABLE = False


class ScreenRecorder:
    """Handles screen recording functionality."""

    def __init__(self):
        if not SCREEN_RECORDING_AVAILABLE:
            self.available = False
            return

        self.available = True
        self.recording = False
        self.recording_thread = None
        self.video_writer = None
        self.fps = Config.RECORDING_FPS
        self.screen_index = 0
        self.output_path = None
        self.start_time = None
        self.frame_count = 0
        self.last_frame_time = None
        self.current_frame_timestamp = ""
        self.paused = False
        self.paused_time = 0
        self.pause_start_time = None

        # Recording dimensions (to be set when recording starts)
        self.screen_width = None
        self.screen_height = None

        # Available screens
        self.available_screens = self._get_available_screens()

    def _get_available_screens(self) -> List[Dict]:
        """Get list of available screens for recording."""
        if not self.available:
            return []

        try:
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            return [{"id": 0, "name": "Primary Screen", "width": screen_width, "height": screen_height}]
        except Exception:
            return []

    def get_available_screens(self) -> List[Dict]:
        """Get available screens for recording."""
        return self.available_screens

    def set_screen(self, screen_index: int) -> Tuple[bool, str]:
        """Set which screen to record."""
        if 0 <= screen_index < len(self.available_screens):
            self.screen_index = screen_index
            return True, f"Recording screen set to {self.available_screens[screen_index]['name']}"
        else:
            return False, "Invalid screen ID"

    def start_recording(self, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """Start screen recording."""
        if not self.available:
            return False, "Screen recording dependencies not available"

        if self.recording:
            return False, "Screen recording already in progress"

        if not self.available_screens:
            return False, "No screens available for recording"

        try:
            # Set output path
            if output_path:
                self.output_path = output_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.output_path = f"screen_recording_{timestamp}.mp4"

            # Get screen dimensions and reduce resolution for smaller file size
            screen_info = self.available_screens[self.screen_index]
            original_width = screen_info["width"]
            original_height = screen_info["height"]

            # Scale down resolution to reduce file size (720p or similar)
            target_width = min(Config.MAX_RECORDING_WIDTH, original_width)
            target_height = min(Config.MAX_RECORDING_HEIGHT, original_height)

            # Calculate scaling factor to maintain aspect ratio
            scale_factor = min(target_width / original_width, target_height / original_height)
            self.screen_width = int(original_width * scale_factor)
            self.screen_height = int(original_height * scale_factor)

            # Try codecs with better compression for smaller file size
            codecs_to_try = [
                ('XVID', '.avi'),  # XVID codec - better compression than MJPG
                ('MJPG', '.avi'),  # Motion JPEG - good quality but larger files
                ('mp4v', '.mp4'),  # MP4 codec - fallback
            ]

            video_writer_initialized = False

            for codec_name, extension in codecs_to_try:
                try:
                    # Adjust output path based on codec
                    if self.output_path.endswith('.mp4') and extension != '.mp4':
                        self.output_path = self.output_path.replace('.mp4', extension)
                    elif not self.output_path.endswith(extension):
                        self.output_path = self.output_path.rsplit('.', 1)[0] + extension

                    fourcc = cv2.VideoWriter_fourcc(*codec_name)
                    self.video_writer = cv2.VideoWriter(
                        self.output_path,
                        fourcc,
                        self.fps,
                        (self.screen_width, self.screen_height),
                        isColor=True
                    )

                    print(f"Recording initialized: {self.screen_width}x{self.screen_height} at {self.fps} FPS using {codec_name}")

                    if self.video_writer.isOpened():
                        print(f"Successfully initialized video writer with codec: {codec_name}")
                        video_writer_initialized = True
                        break
                    else:
                        self.video_writer.release()
                        print(f"Failed to initialize video writer with codec: {codec_name}")

                except Exception as codec_error:
                    print(f"Error trying codec {codec_name}: {codec_error}")
                    if self.video_writer:
                        self.video_writer.release()
                    continue

            if not video_writer_initialized:
                return False, "Failed to initialize video writer with any available codec"

            self.recording = True
            self.paused = False
            self.start_time = time.time()
            self.frame_count = 0
            self.last_frame_time = time.time()
            self.current_frame_timestamp = ""
            self.paused_time = 0
            self.pause_start_time = None

            # Start recording thread
            self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
            self.recording_thread.start()

            return True, f"Screen recording started with codec {codec_name}"
        except Exception as e:
            return False, f"Error starting screen recording: {str(e)}"

    def stop_recording(self) -> Tuple[bool, str]:
        """Stop screen recording."""
        if not self.recording:
            return False, "No screen recording in progress"

        try:
            self.recording = False
            self.paused = False
            self.start_time = None
            self.current_frame_timestamp = ""
            self.paused_time = 0
            self.pause_start_time = None

            # Reset dimensions
            self.screen_width = None
            self.screen_height = None

            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)

            # Release video writer
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None

            return True, f"Screen recording saved to {self.output_path}"
        except Exception as e:
            return False, f"Error stopping screen recording: {str(e)}"

    def pause_recording(self) -> Tuple[bool, str]:
        """Pause screen recording."""
        if not self.recording:
            return False, "No screen recording in progress"

        if self.paused:
            return False, "Recording already paused"

        self.paused = True
        self.pause_start_time = time.time()
        return True, "Screen recording paused"

    def resume_recording(self) -> Tuple[bool, str]:
        """Resume screen recording."""
        if not self.recording:
            return False, "No screen recording in progress"

        if not self.paused:
            return False, "Recording is not paused"

        # Calculate paused time and add to total paused time
        if self.pause_start_time:
            self.paused_time += time.time() - self.pause_start_time
            self.pause_start_time = None

        self.paused = False
        return True, "Screen recording resumed"

    def _recording_loop(self):
        """Optimized screen recording loop with simplified timing."""
        if not self.available:
            return

        try:
            frame_interval = 1.0 / self.fps
            last_frame_time = time.time()

            # Simplified timing with less overhead
            while self.recording:
                if self.paused:
                    time.sleep(0.2)  # Longer sleep when paused
                    continue

                current_time = time.time()

                # Simple timing check - if not enough time passed, sleep
                time_since_last_frame = current_time - last_frame_time
                if time_since_last_frame < frame_interval:
                    sleep_time = frame_interval - time_since_last_frame
                    if sleep_time > 0.01:  # Only sleep for meaningful durations
                        time.sleep(sleep_time * 0.9)  # Sleep slightly less
                    continue

                # Capture frame with resizing for smaller file size
                try:
                    # Capture screenshot
                    screenshot = pyautogui.screenshot()

                    # Resize frame if needed to reduce file size
                    if (self.screen_width is not None and self.screen_height is not None and
                        (self.screen_width < screenshot.width or self.screen_height < screenshot.height)):
                        screenshot = screenshot.resize((self.screen_width, self.screen_height))

                    # Convert to OpenCV format
                    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                    # Write frame immediately
                    if self.video_writer.isOpened():
                        self.video_writer.write(frame)
                        self.frame_count += 1
                    else:
                        print("Warning: Video writer not open")
                        break

                except Exception as capture_error:
                    print(f"Frame capture error: {capture_error}")
                    break

                # Update timing
                last_frame_time = current_time

                # Performance logging reduced to every 120 frames
                if self.frame_count % 120 == 0:
                    actual_fps = self.fps if time_since_last_frame > 0 else 0
                    print(f"Recording: {self.frame_count} frames, Target FPS: {self.fps}")

        except Exception as e:
            print(f"Error in screen recording loop: {e}")
            self.recording = False

    def get_recording_timestamp(self) -> str:
        """Get the elapsed time from the beginning of the video."""
        if not self.available or not self.recording or not self.start_time:
            return ""

        # Calculate elapsed time considering pauses
        current_time = time.time()
        total_elapsed = current_time - self.start_time

        # Subtract paused time
        if self.paused and self.pause_start_time:
            current_pause_duration = current_time - self.pause_start_time
            elapsed_time = total_elapsed - self.paused_time - current_pause_duration
        else:
            elapsed_time = total_elapsed - self.paused_time

        # Ensure elapsed time doesn't go negative
        elapsed_time = max(0, elapsed_time)

        # For active recordings with frames, use frame count for more accurate timing
        if self.frame_count > 0:
            frame_based_time = self.frame_count / self.fps
            # Use frame-based time if it's more accurate (prevents overestimation)
            elapsed_time = min(elapsed_time, frame_based_time)

        # Format as HH:MM:SS
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_recording_status(self) -> Dict:
        """Get current screen recording status."""
        if not self.available:
            return {
                "recording": False,
                "available": False,
                "output_path": None,
                "duration": 0,
                "frame_count": 0,
                "fps": 0,
                "actual_fps": 0
            }

        # Calculate duration considering paused time
        if self.start_time:
            current_time = time.time()
            total_elapsed = current_time - self.start_time

            # If currently paused, add the current pause duration
            if self.paused and self.pause_start_time:
                current_pause_duration = current_time - self.pause_start_time
                duration = total_elapsed - self.paused_time - current_pause_duration
            else:
                duration = total_elapsed - self.paused_time

            # Ensure duration doesn't go negative
            duration = max(0, duration)

            # For active recordings, use frame count for more accurate duration
            if self.recording and not self.paused and self.frame_count > 0:
                frame_based_duration = self.frame_count / self.fps
                # Use the minimum of time-based and frame-based duration to avoid overestimation
                duration = min(duration, frame_based_duration)
        else:
            duration = 0

        actual_fps = (self.frame_count / duration) if duration > 0 else 0

        return {
            "recording": self.recording and not self.paused,
            "paused": self.paused,
            "available": self.available,
            "output_path": self.output_path,
            "screen": self.screen_index,
            "screen_name": self.available_screens[self.screen_index]["name"] if self.available_screens else None,
            "fps": self.fps,
            "actual_fps": actual_fps,
            "frame_count": self.frame_count,
            "duration": duration,
            "duration_formatted": format_duration(duration)
        }

    def get_file_size(self) -> int:
        """Get the size of the output video file in bytes."""
        if self.output_path and os.path.exists(self.output_path):
            return os.path.getsize(self.output_path)
        return 0

    def cleanup(self):
        """Clean up resources."""
        if self.recording:
            self.stop_recording()

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

    def set_fps(self, fps: int) -> Tuple[bool, str]:
        """Set the recording FPS."""
        if fps <= 0:
            return False, "FPS must be greater than 0"

        if fps > 60:
            return False, "FPS cannot exceed 60"

        if self.recording:
            return False, "Cannot change FPS while recording"

        self.fps = fps
        return True, f"FPS set to {fps}"

    def validate_output_path(self, path: str) -> Tuple[bool, str]:
        """Validate output path for recording."""
        try:
            # Check if directory exists
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # Check if we can write to the location
            with open(path + '.test', 'w') as f:
                f.write('test')
            os.remove(path + '.test')

            return True, "Output path is valid"
        except Exception as e:
            return False, f"Invalid output path: {str(e)}"