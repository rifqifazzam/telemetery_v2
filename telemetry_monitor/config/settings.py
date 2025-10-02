"""
Configuration settings for the Telemetry Monitor application.
"""

class Config:
    """Application configuration constants"""

    # Window settings
    WINDOW_TITLE = "Telemetry Monitor"
    WINDOW_GEOMETRY = "1100x700"

    # Modern dark theme color scheme
    COLORS = {
        # Background colors
        'bg_primary': '#0f172a',      # Deep dark blue background
        'bg_secondary': '#1e293b',    # Dark blue-gray for cards
        'bg_tertiary': '#334155',     # Lighter dark for accents

        # Text colors
        'text_primary': '#f1f5f9',    # Light gray-white for main text
        'text_secondary': '#cbd5e1',  # Medium gray for secondary text
        'text_muted': '#64748b',      # Muted gray for subtle text
        'text_inverse': '#0f172a',    # Dark text for light backgrounds

        # Accent colors (modern gradient)
        'primary_start': '#3b82f6',   # Bright blue
        'primary_end': '#1d4ed8',     # Deep blue
        'secondary_start': '#8b5cf6', # Bright purple
        'secondary_end': '#6d28d9',   # Deep purple
        'success': '#10b981',         # Emerald green
        'warning': '#f59e0b',         # Amber
        'danger': '#ef4444',          # Red
        'info': '#06b6d4',            # Cyan

        # UI elements
        'border': '#334155',          # Subtle border color
        'border_focus': '#3b82f6',    # Focused border color
        'shadow': 'rgba(0, 0, 0, 0.3)', # Drop shadow
        'hover': '#1e293b',           # Hover overlay

        # Gradient definitions
        'primary_gradient': ['#3b82f6', '#1d4ed8'],
        'secondary_gradient': ['#8b5cf6', '#6d28d9'],
        'success_gradient': ['#10b981', '#059669'],
        'warning_gradient': ['#f59e0b', '#d97706'],
        'danger_gradient': ['#ef4444', '#dc2626'],
        
        'floating_bg': '#1e293b',
        'floating_header': '#334155',
        'floating_border': "#f63b3b",
    }

    # Monitoring settings
    MONITORING_INTERVAL = 2.0  # seconds - reduced from 0.1 to improve performance
    HISTORY_MAXLEN = 600  # 10 minutes at 1s intervals
    LOG_INTERVAL = 5  # seconds - interval for logging telemetry data to table
    TIME_WINDOW = 60.0  # seconds - time window for rate calculations

    # Metrics grid settings
    METRICS_GRID_COLUMNS = 4
    METRICS_INFO = [
        ("Keystroke Rate", "0 keys/min", 'primary_gradient', "⌨️"),
        ("Mouse Movement", "0 px/min", 'info_gradient', "🖱️"),
        ("Mouse Clicks", "0 clicks/min", 'danger_gradient', "👆"),
        ("Mouse Scroll", "0 px/min", 'warning_gradient', "📜"),
        ("CPU Usage", "0%", 'warning_gradient', "🖥️"),
        ("Memory Usage", "0%", 'info_gradient', "💾"),
        ("Network Throughput", "0 MBps", 'success_gradient', "🌐"),
        ("Disk I/O Speed", "0 MBps", 'secondary_gradient', "💿"),
    ]

    # Font settings
    FONT_FAMILY = "Segoe UI"
    HEADER_FONT_SIZE = 24
    SUBTITLE_FONT_SIZE = 12
    METRIC_TITLE_FONT_SIZE = 10
    METRIC_VALUE_FONT_SIZE = 20
    METRIC_SUBTITLE_FONT_SIZE = 9
    STATUS_FONT_SIZE = 10
    BUTTON_FONT_SIZE = 10
    OVERVIEW_TITLE_FONT_SIZE = 16
    OVERVIEW_VALUE_FONT_SIZE = 24
    OVERVIEW_LABEL_FONT_SIZE = 10
    TABLE_HEADER_FONT_SIZE = 9
    TABLE_DATA_FONT_SIZE = 8

    # Data logging settings
    MAX_LOG_ENTRIES = 1000  # Maximum number of log entries to keep in memory
    TABLE_HEIGHT = 15  # Number of rows to display in table
    TABLE_PAGE_SIZE = 25  # Number of rows per page in pagination
    TABLE_COLUMNS = [
        ("Timestamp", 90),
        ("App Name", 110),
        ("Window Title", 140),
        ("Keys/min", 70),
        ("Mouse/min", 70),
        ("Clicks/min", 70),
        ("Scroll/min", 70),
        ("CPU %", 60),
        ("Memory %", 70),
        ("Network MBps", 80),
        ("Disk MBps", 70),
        ("Rec Timestamp", 120),
        ("Process Name", 100)
    ]

    # UI spacing and layout
    PADDING_SMALL = 4
    PADDING_MEDIUM = 8
    PADDING_LARGE = 16
    CORNER_RADIUS = 8
    BORDER_WIDTH = 1
    SHADOW_BLUR = 10

    # Export settings
    EXPORT_FORMATS = ["CSV", "Excel"]
    DEFAULT_EXPORT_FILENAME = "telemetry_data"

    # Screen recording settings
    RECORDING_FPS = 10  # Standard recording FPS
    MAX_RECORDING_WIDTH = 1280  # Maximum width for recording to reduce file size
    MAX_RECORDING_HEIGHT = 720  # Maximum height for recording to reduce file size
    SCREEN_CARD_TITLE = "Screen Recording"
    SCREEN_CARD_ICON = "📹"
    SCREEN_RECORDING_METRIC_INFO = [
        ("Screen Recording", "Stopped", 'danger_gradient', "📹"),
        ("Recording Screen", "Primary", 'info_gradient', "🖥️"),
        ("Recording Duration", "0s", 'warning_gradient', "⏱️"),
    ]