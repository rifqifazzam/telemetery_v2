# Telemetry Monitor

A modern Python/Tkinter application that monitors and displays real-time system telemetry data with a beautiful GUI interface.

## Features

- **Active Window Tracking**: Shows current foreground application name and window title
- **Input Rate Monitoring**: Tracks keystrokes, mouse movement, clicks, and scrolling
- **System Performance**: Monitors CPU usage, memory usage, network throughput, and disk speed
- **Real-time Updates**: Data sampled and calculated every 10 seconds
- **Modern UI**: Clean, responsive design with Tkinter
- **Modular Architecture**: Well-organized codebase for easy maintenance

## Installation

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

The application is organized into modular components:

- **main.py** - Application entry point
- **monitor.py** - Main monitoring class and coordination
- **gui.py** - All GUI components and display logic
- **metrics.py** - Metrics tracking and calculations
- **config.py** - Configuration settings and constants

## Telemetry Data Tracked

1. **Foreground App Name**: Current active application
2. **Foreground App Title**: Window title of active application
3. **Keystroke Rate**: Keys pressed per minute
4. **Mouse Movement Rate**: Pixels moved per minute
5. **Mouse Click Rate**: Clicks per minute
6. **Mouse Scroll Rate**: Scroll pixels per minute
7. **CPU Usage**: Current CPU usage percentage and speed
8. **Memory Usage**: RAM usage in GB and percentage
9. **Network Throughput**: Network throughput in MBps
10. **Disk I/O Speed**: Disk read/write speed in MBps

## Performance Overview

The application also provides:
- **Performance Score**: Calculated based on system resources and input activity
- **Uptime**: Application running time
- **Total Keys**: Cumulative keystroke count
- **Total Clicks**: Cumulative mouse click count

## Technologies Used

- Python 3.7+ (Core language)
- Tkinter (GUI framework)
- psutil (System metrics)
- pynput (Input monitoring)
- pywin32 (Windows-specific window tracking)

## Requirements

- Python 3.7 or higher
- Windows OS (for full functionality including active window tracking)
- psutil >= 5.9.0
- pynput >= 1.7.0
- pywin32 >= 305 (Windows only)

## Notes

- On non-Windows systems, active window tracking functionality is limited
- Input monitoring requires appropriate system permissions
- The application uses a modular architecture for better maintainability and extensibility