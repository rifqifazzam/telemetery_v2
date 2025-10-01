# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based telemetry monitoring application with a modular Tkinter GUI. It tracks system performance metrics, user input rates, and active window information in real-time.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Main entry point
python main.py

# Run with virtual environment
venv\Scripts\python main.py
```

### Testing Dependencies
```bash
# Test core functionality
venv\Scripts\python -c "import psutil, pynput, win32gui, win32process, pystray, cv2, numpy; print('Dependencies loaded successfully')"
```

## Architecture

### Modular Design Pattern
The application follows a clean modular architecture organized in packages:

- **main.py**: Entry point only - instantiates and starts the application
- **telemetry_monitor/**: Main package containing all application modules
  - **core/**: Core application logic (app.py, monitoring_controller.py)
  - **gui/**: All Tkinter UI components and display logic
  - **monitoring/**: Data collection and tracking modules
    - metrics_tracker.py: Metrics calculation and management
    - input_monitor.py: User input monitoring
    - system_monitor.py: System performance monitoring
    - screen_recorder.py: Screen recording functionality
  - **config/**: Centralized configuration settings
  - **utils/**: Utility functions and helpers

### Key Architecture Decisions

1. **Separation of Concerns**: Each module handles one specific responsibility
2. **Dependency Injection**: Components are passed dependencies rather than creating them
3. **Configuration Centralization**: All UI and behavioral settings in config.py
4. **Real-time Monitoring**: Background thread for data collection with GUI updates via root.after()

### Data Flow
1. **Input Monitoring** (pynput) → **MetricsTracker** → Rate calculations
2. **System Monitoring** (psutil) → **MetricsTracker** → Performance metrics
3. **Background Thread** → **Data Processing** → **GUI Updates** (thread-safe via root.after())

### Monitoring Loop
- Runs every 10 seconds (configurable in config.py)
- Collects system metrics and calculates rates
- Updates display via main thread using root.after()
- Handles network/disk rate calculations using previous values

### Input Tracking
- Uses pynput for keyboard/mouse monitoring
- Tracks cumulative counts and historical data (600 sample window)
- Calculates per-minute rates from historical data

### Windows-Specific Features
- Active window tracking using win32gui and win32process
- Process name extraction via psutil
- Screen recording capabilities using opencv-python and pyautogui
- System tray integration with pystray
- Limited functionality on non-Windows systems

## Important Implementation Details

### Thread Safety
- GUI updates must use root.after() to execute in main thread
- Background monitoring runs in separate daemon thread
- Input listeners run in separate threads managed by pynput

### Configuration Management
- All UI settings (colors, fonts, sizes) in config.py
- Monitoring interval and history size configurable
- Metrics grid layout defined in configuration

### Error Handling
- Graceful degradation when Windows-specific features unavailable
- Exception handling in monitoring loop prevents crashes
- Input monitoring setup catches ImportError and other errors

### Performance Considerations
- Deque structures for efficient historical data management
- Minimal UI updates - only changed values
- Background thread prevents GUI freezing during data collection
- Screen recording uses opencv for efficient video encoding
- System tray integration allows background operation