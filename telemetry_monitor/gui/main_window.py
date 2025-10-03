"""
Main window GUI component for the Telemetry Monitor application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import csv
import os
from datetime import datetime
from .widgets import ModernTable, MetricCard, StatusIndicator
from .floating_control import FloatingControlWindow
from ..monitoring.metrics_tracker import MetricsTracker
from ..config.settings import Config
from ..utils.helpers import create_timestamp, format_duration


class TelemetryGUI:
    """Main GUI class for the Telemetry Monitor application."""

    def __init__(self, root: tk.Tk, metrics_tracker: MetricsTracker):
        self.root = root
        self.metrics_tracker = metrics_tracker
        self.colors = Config.COLORS

        # Initialize labels and widgets
        self.app_name_label = None
        self.window_title_label = None
        self.metric_labels = {}
        self.screen_recording_labels = {}
        self.status_indicator = None
        self.last_update_label = None
        self.uptime_label = None
        self.total_keys_label = None
        self.total_clicks_label = None
        self.table_widget = None
        self.screen_selector = None
        self.start_btn = None
        self.pause_btn = None
        self.stop_btn = None
        self.floating_window = None

        # Setup window
        self.setup_window()
        self.create_widgets()

        # Start display update loop
        self.update_display_loop()

    def setup_window(self):
        """Setup main window with modern styling."""
        self.root.title(Config.WINDOW_TITLE)
        self.root.geometry(Config.WINDOW_GEOMETRY)
        self.root.configure(bg=self.colors['bg_primary'])

        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Modern window styling
        self.root.tk_setPalette(background=self.colors['bg_primary'])

    def create_widgets(self):
        """Create all GUI widgets."""
        self.create_header()
        self.create_scrollable_content()
        self.create_status_bar()
        self.create_floating_window()

    def create_scrollable_content(self):
        """Create scrollable content container."""
        # Create main scrollable container
        self.scrollable_canvas = tk.Canvas(
            self.root,
            bg=self.colors['bg_primary'],
            highlightthickness=0
        )
        self.scrollable_canvas.pack(fill=tk.BOTH, expand=True, padx=Config.PADDING_MEDIUM, pady=(0, Config.PADDING_MEDIUM))

        # Configure canvas scrolling (scrollbar hidden)
        # Note: Scrollbar is removed, only mouse wheel scrolling available

        # Ensure canvas can receive focus for mouse wheel events
        self.scrollable_canvas.focus_set()

        # Create content frame inside canvas
        self.content_frame = tk.Frame(
            self.scrollable_canvas,
            bg=self.colors['bg_primary']
        )

        # Create window on canvas for content frame
        self.canvas_window = self.scrollable_canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="nw"
        )

        # Configure scroll region
        self.content_frame.bind('<Configure>', self.configure_scroll_region)
        self.scrollable_canvas.bind('<Configure>', self.on_canvas_configure)

        # Add mouse wheel scrolling to canvas and root window
        self.scrollable_canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.scrollable_canvas.bind('<Button-4>', self.on_mouse_wheel)  # Linux scroll up
        self.scrollable_canvas.bind('<Button-5>', self.on_mouse_wheel)  # Linux scroll down
        self.root.bind('<MouseWheel>', self.on_mouse_wheel)  # Bind to root as well

        # Bind canvas click to ensure focus for scrolling
        self.scrollable_canvas.bind('<Button-1>', lambda e: self.scrollable_canvas.focus_set())

        # Create all content sections
        self.create_overview_section()
        self.create_metrics_grid()
        self.create_screen_recording_section()
        self.create_table_section()

    def configure_scroll_region(self, event=None):
        """Configure the scroll region when content changes."""
        self.scrollable_canvas.configure(scrollregion=self.scrollable_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Handle canvas configure event to resize content width."""
        # Resize content frame to canvas width
        canvas_width = event.width
        self.scrollable_canvas.itemconfig(self.canvas_window, width=canvas_width)

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        # Handle different platforms
        if event.num == 4:  # Linux scroll up
            scroll_amount = -1
        elif event.num == 5:  # Linux scroll down
            scroll_amount = 1
        else:  # Windows/macOS scroll
            scroll_amount = int(-1 * (event.delta / 120))

        # Scroll the canvas
        self.scrollable_canvas.yview_scroll(scroll_amount, "units")

    def create_header(self):
        """Create modern header with gradient background."""
        self.header_frame = tk.Frame(
            self.root,
            bg=self.colors['bg_secondary'],
            height=80
        )
        self.header_frame.pack(fill=tk.X, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_MEDIUM)
        self.header_frame.pack_propagate(False)

        # Title with gradient effect simulation
        title_container = tk.Frame(self.header_frame, bg=self.colors['bg_secondary'])
        title_container.pack(side=tk.LEFT, padx=Config.PADDING_LARGE, pady=Config.PADDING_LARGE)

        title_label = tk.Label(
            title_container,
            text=Config.WINDOW_TITLE,
            font=(Config.FONT_FAMILY, Config.HEADER_FONT_SIZE, "bold"),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_container,
            text="Real-time System Performance Monitoring",
            font=(Config.FONT_FAMILY, Config.SUBTITLE_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        )
        subtitle_label.pack()

        # Right side container for controls and status
        right_container = tk.Frame(self.header_frame, bg=self.colors['bg_secondary'])
        right_container.pack(side=tk.RIGHT, padx=Config.PADDING_LARGE, pady=Config.PADDING_LARGE)

        # Status indicator
        self.status_indicator = StatusIndicator(right_container, size=12, initial_color='danger')
        self.status_indicator.pack(side=tk.RIGHT, padx=(Config.PADDING_MEDIUM, 0))

        # Control buttons
        control_frame = tk.Frame(right_container, bg=self.colors['bg_secondary'])
        control_frame.pack(side=tk.RIGHT, padx=(Config.PADDING_MEDIUM, Config.PADDING_MEDIUM))

        self.start_btn = tk.Button(
            control_frame,
            text="Start",
            command=self.start_logging,
            bg=self.colors['success'],
            fg='white',
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            relief=tk.FLAT,
            padx=Config.PADDING_MEDIUM,
            pady=Config.PADDING_SMALL,
            state=tk.DISABLED
        )
        self.start_btn.pack(side=tk.LEFT, padx=Config.PADDING_SMALL)

        self.pause_btn = tk.Button(
            control_frame,
            text="Pause",
            command=self.pause_logging,
            bg=self.colors['warning'],
            fg='white',
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            relief=tk.FLAT,
            padx=Config.PADDING_MEDIUM,
            pady=Config.PADDING_SMALL,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=Config.PADDING_SMALL)

        self.stop_btn = tk.Button(
            control_frame,
            text="Stop",
            command=self.stop_logging,
            bg=self.colors['danger'],
            fg='white',
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            relief=tk.FLAT,
            padx=Config.PADDING_MEDIUM,
            pady=Config.PADDING_SMALL,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=Config.PADDING_SMALL)

    def create_overview_section(self):
        """Create overview section with key metrics."""
        self.overview_frame = tk.Frame(
            self.content_frame,
            bg=self.colors['bg_secondary'],
            relief=tk.RAISED,
            bd=1
        )
        self.overview_frame.pack(fill=tk.X, padx=Config.PADDING_MEDIUM, pady=(Config.PADDING_MEDIUM, Config.PADDING_MEDIUM))

        # Overview container
        overview_container = tk.Frame(self.overview_frame, bg=self.colors['bg_secondary'])
        overview_container.pack(fill=tk.X, padx=Config.PADDING_LARGE, pady=Config.PADDING_LARGE)

        # Uptime
        uptime_frame = tk.Frame(overview_container, bg=self.colors['bg_secondary'])
        uptime_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.uptime_label = tk.Label(
            uptime_frame,
            text="0m",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_VALUE_FONT_SIZE, "bold"),
            bg=self.colors['bg_secondary'],
            fg=self.colors['primary_start']
        )
        self.uptime_label.pack()

        tk.Label(
            uptime_frame,
            text="Uptime",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_LABEL_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        ).pack()

        # Active window
        window_frame = tk.Frame(overview_container, bg=self.colors['bg_secondary'])
        window_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(Config.PADDING_LARGE, 0))

        self.app_name_label = tk.Label(
            window_frame,
            text="Unknown",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_VALUE_FONT_SIZE - 4, "bold"),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            wraplength=200
        )
        self.app_name_label.pack()

        self.window_title_label = tk.Label(
            window_frame,
            text="No active window",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_LABEL_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary'],
            wraplength=200
        )
        self.window_title_label.pack()

        # Total keys
        keys_frame = tk.Frame(overview_container, bg=self.colors['bg_secondary'])
        keys_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.total_keys_label = tk.Label(
            keys_frame,
            text="0",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_VALUE_FONT_SIZE, "bold"),
            bg=self.colors['bg_secondary'],
            fg=self.colors['warning']
        )
        self.total_keys_label.pack()

        tk.Label(
            keys_frame,
            text="Total Keys",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_LABEL_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        ).pack()

        # Total clicks
        clicks_frame = tk.Frame(overview_container, bg=self.colors['bg_secondary'])
        clicks_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.total_clicks_label = tk.Label(
            clicks_frame,
            text="0",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_VALUE_FONT_SIZE, "bold"),
            bg=self.colors['bg_secondary'],
            fg=self.colors['danger']
        )
        self.total_clicks_label.pack()

        tk.Label(
            clicks_frame,
            text="Total Clicks",
            font=(Config.FONT_FAMILY, Config.OVERVIEW_LABEL_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        ).pack()

    def create_metrics_grid(self):
        """Create modern metrics grid with gradient cards."""
        self.metrics_frame = tk.Frame(
            self.content_frame,
            bg=self.colors['bg_primary']
        )
        self.metrics_frame.pack(fill=tk.BOTH, expand=True, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_MEDIUM)

        # Create grid of metric cards
        for i, (title, initial_value, color_scheme, icon) in enumerate(Config.METRICS_INFO):
            row = i // Config.METRICS_GRID_COLUMNS
            col = i % Config.METRICS_GRID_COLUMNS

            card_frame = self.create_metric_card(
                self.metrics_frame,
                title,
                initial_value,
                color_scheme,
                icon
            )
            card_frame.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=Config.PADDING_SMALL,
                pady=Config.PADDING_SMALL
            )

            # Configure grid weights
            self.metrics_frame.grid_rowconfigure(row, weight=1)
            self.metrics_frame.grid_columnconfigure(col, weight=1)

    def create_metric_card(self, parent, title: str, initial_value: str, color_scheme: str, icon: str):
        """Create a modern metric card with gradient styling."""
        card = MetricCard(parent, title, initial_value, color_scheme, icon)

        # Store reference for updates
        metric_key = title.lower().replace(" ", "_").replace("/", "_")
        self.metric_labels[metric_key] = card

        return card

    def create_table_section(self):
        """Create modern table section."""
        self.table_frame = tk.Frame(
            self.content_frame,
            bg=self.colors['bg_primary']
        )
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_MEDIUM)

        # Table header
        table_header = tk.Frame(self.table_frame, bg=self.colors['bg_secondary'])
        table_header.pack(fill=tk.X, pady=(0, Config.PADDING_SMALL))

        tk.Label(
            table_header,
            text="Telemetry Data Log",
            font=(Config.FONT_FAMILY, Config.HEADER_FONT_SIZE - 4, "bold"),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_SMALL)

        
        # Create modern table
        self.table_widget = ModernTable(
            self.table_frame,
            columns=Config.TABLE_COLUMNS,
            height=Config.TABLE_HEIGHT
        )
        self.table_widget.pack(fill=tk.BOTH, expand=True)

    def create_screen_recording_section(self):
        """Create screen recording section with controls."""
        self.screen_recording_frame = tk.Frame(
            self.content_frame,
            bg=self.colors['bg_secondary'],
            relief=tk.RAISED,
            bd=1
        )
        self.screen_recording_frame.pack(fill=tk.X, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_MEDIUM)

        # Screen recording container
        recording_container = tk.Frame(self.screen_recording_frame, bg=self.colors['bg_secondary'])
        recording_container.pack(fill=tk.X, padx=Config.PADDING_LARGE, pady=Config.PADDING_LARGE)

        # Title
        title_frame = tk.Frame(recording_container, bg=self.colors['bg_secondary'])
        title_frame.pack(fill=tk.X, pady=(0, Config.PADDING_MEDIUM))

        tk.Label(
            title_frame,
            text=Config.SCREEN_CARD_TITLE,
            font=(Config.FONT_FAMILY, Config.HEADER_FONT_SIZE - 6, "bold"),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT)

        # Screen selector
        selector_frame = tk.Frame(recording_container, bg=self.colors['bg_secondary'])
        selector_frame.pack(fill=tk.X, pady=Config.PADDING_SMALL)

        tk.Label(
            selector_frame,
            text="Screen:",
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, Config.PADDING_SMALL))

        self.screen_selector = ttk.Combobox(
            selector_frame,
            state="readonly",
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            width=20
        )
        self.screen_selector.pack(side=tk.LEFT, padx=Config.PADDING_SMALL)
        self.screen_selector.bind('<<ComboboxSelected>>', self.on_screen_selected)

        # Recording metrics
        metrics_container = tk.Frame(recording_container, bg=self.colors['bg_secondary'])
        metrics_container.pack(fill=tk.X, pady=Config.PADDING_MEDIUM)

        # Create recording metric cards
        for i, (title, initial_value, color_scheme, icon) in enumerate(Config.SCREEN_RECORDING_METRIC_INFO):
            card_frame = self.create_screen_recording_metric_card(
                metrics_container,
                title,
                initial_value,
                color_scheme,
                icon
            )
            card_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=Config.PADDING_SMALL)

        # Update screen selector with available screens
        self.update_screen_selector()

    def create_screen_recording_metric_card(self, parent, title: str, initial_value: str, color_scheme: str, icon: str):
        """Create a metric card for screen recording."""
        card = MetricCard(parent, title, initial_value, color_scheme, icon)

        # Store reference for updates
        metric_key = title.lower().replace(" ", "_").replace("/", "_")
        self.screen_recording_labels[metric_key] = card

        return card

    def update_screen_selector(self):
        """Update screen selector with available screens."""
        screens = self.metrics_tracker.available_screens
        screen_names = [screen["name"] for screen in screens]

        self.screen_selector['values'] = screen_names
        if screen_names:
            self.screen_selector.current(0)

    def on_screen_selected(self, event):
        """Handle screen selection."""
        selected_index = self.screen_selector.current()
        if selected_index >= 0:
            success, message = self.metrics_tracker.set_recording_screen(selected_index)
            if not success:
                self.show_error(message)

    def create_status_bar(self):
        """Create modern status bar."""
        self.status_frame = tk.Frame(
            self.root,
            bg=self.colors['bg_secondary'],
            height=30
        )
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_frame.pack_propagate(False)

        # Status content
        status_content = tk.Frame(self.status_frame, bg=self.colors['bg_secondary'])
        status_content.pack(fill=tk.X, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_SMALL)

        # Last update time
        self.last_update_label = tk.Label(
            status_content,
            text="Last update: Never",
            font=(Config.FONT_FAMILY, Config.STATUS_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_muted']
        )
        self.last_update_label.pack(side=tk.LEFT)

        # Status text
        self.status_text_label = tk.Label(
            status_content,
            text="● Monitoring Active",
            font=(Config.FONT_FAMILY, Config.STATUS_FONT_SIZE),
            bg=self.colors['bg_secondary'],
            fg=self.colors['success']
        )
        self.status_text_label.pack(side=tk.RIGHT)

    def update_display_loop(self):
        """Start the display update loop with optimized batching."""
        def update_loop():
            while True:
                try:
                    # Get all data in one batch to minimize overhead
                    total_counts = self.metrics_tracker.get_total_counts()
                    uptime = self.metrics_tracker.get_uptime_minutes()
                    telemetry_log = self.metrics_tracker.get_telemetry_log()
                    recording_status = self.metrics_tracker.get_recording_status()
                    display_data = self.metrics_tracker.get_current_metrics()

                    # Batch all GUI updates into a single call
                    self.root.after(0, self.batch_update_gui, display_data, total_counts, uptime, telemetry_log, recording_status)

                    # Sleep for longer interval to reduce CPU usage
                    time.sleep(2.0)  # Increased from 1.0 to 2.0 seconds
                except Exception as e:
                    print(f"Error in display update loop: {e}")
                    time.sleep(2.0)

        # Start update thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    def update_display(self, display_data: dict):
        """Update the display with new data."""
        try:
            # Update active window info
            self.app_name_label.config(text=display_data['app_name'])
            self.window_title_label.config(text=display_data['window_title'])

            # Update metric labels
            self.metric_labels['keystroke_rate'].update_value(f"{display_data['key_rate']:.1f} keys/min")
            self.metric_labels['mouse_movement'].update_value(f"{display_data['movement_rate']:.0f} px/min")
            self.metric_labels['mouse_clicks'].update_value(f"{display_data['click_rate']:.1f} clicks/min")
            self.metric_labels['mouse_scroll'].update_value(f"{display_data['scroll_rate']:.1f} px/min")
            self.metric_labels['cpu_usage'].update_value(f"{display_data['cpu_percent']:.1f}%")
            self.metric_labels['memory_usage'].update_value(f"{display_data['memory_percent']:.1f}%")
            self.metric_labels['network_throughput'].update_value(f"{display_data['network_mbps']:.2f} MBps")
            self.metric_labels['disk_i_o_speed'].update_value(f"{display_data['disk_mbps']:.2f} MBps")

        except Exception as e:
            print(f"Error updating display: {e}")

    def batch_update_gui(self, display_data: dict, total_counts: dict, uptime_minutes: int, telemetry_log: list, recording_status: dict):
        """Batch all GUI updates into a single operation for better performance."""
        try:
            # Update display data
            self.update_display(display_data)
            self.update_total_counts(total_counts)
            self.update_uptime(uptime_minutes)
            self.update_table(telemetry_log)
            self.update_last_update_time()
            self.update_screen_recording_display(recording_status)
        except Exception as e:
            print(f"Error in batch GUI update: {e}")

    def update_total_counts(self, total_counts: dict):
        """Update total counts display."""
        if self.total_keys_label:
            self.total_keys_label.config(text=str(total_counts['keys']))
        if self.total_clicks_label:
            self.total_clicks_label.config(text=str(total_counts['clicks']))

    def update_uptime(self, uptime_minutes: int):
        """Update uptime display."""
        if self.uptime_label:
            if uptime_minutes < 60:
                self.uptime_label.config(text=f"{uptime_minutes}m")
            else:
                hours = uptime_minutes // 60
                minutes = uptime_minutes % 60
                self.uptime_label.config(text=f"{hours}h {minutes}m")

    def update_table(self, telemetry_log: list):
        """Update table with latest telemetry data with optimized batching."""
        if self.table_widget:
            # Limit to last 25 entries instead of 50 for better performance
            table_data = []
            for entry in reversed(list(telemetry_log)[-25:]):  # Reduced from 50 to 25
                row_data = [
                    entry['timestamp'],
                    entry['app_name'],
                    entry['window_title'],
                    f"{entry['key_rate']:.1f}",
                    f"{entry['movement_rate']:.0f}",
                    f"{entry['click_rate']:.1f}",
                    f"{entry['scroll_rate']:.1f}",
                    f"{entry['cpu_percent']:.1f}",
                    f"{entry['memory_percent']:.1f}",
                    f"{entry['network_mbps']:.2f}",
                    f"{entry['disk_mbps']:.2f}",
                    entry['rec_timestamp'] if entry.get('rec_timestamp') else "",
                    entry.get('activity', 'None')
                ]
                table_data.append(row_data)

            self.table_widget.update_data(table_data)

            # Update scroll region immediately without additional delay
            self.configure_scroll_region()

    def update_last_update_time(self):
        """Update the last update time."""
        if self.last_update_label:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.config(text=f"Last update: {current_time}")

    def update_screen_recording_display(self, recording_status: dict):
        """Update screen recording display with current status."""
        try:
            # Update recording status
            if recording_status["recording"]:
                self.screen_recording_labels["screen_recording"].update_value("Recording")
                self.screen_recording_labels["screen_recording"].update_color('success')
            else:
                self.screen_recording_labels["screen_recording"].update_value("Stopped")
                self.screen_recording_labels["screen_recording"].update_color('danger')

            # Update screen name
            if recording_status["screen_name"]:
                self.screen_recording_labels["recording_screen"].update_value(recording_status["screen_name"])

            # Update duration
            duration = recording_status["duration"]
            if duration > 0:
                duration_text = format_duration(duration)

                # Add actual FPS if available
                if "actual_fps" in recording_status and recording_status["actual_fps"] > 0:
                    actual_fps = recording_status["actual_fps"]
                    target_fps = recording_status["fps"]
                    fps_text = f"{duration_text} ({actual_fps:.1f}/{target_fps} FPS)"
                else:
                    fps_text = duration_text

                self.screen_recording_labels["recording_duration"].update_value(fps_text)
                
                if self.floating_window:
                    self.floating_window.set_timer(duration_text)
                
            else:
                self.screen_recording_labels["recording_duration"].update_value("0s")
                
                if self.floating_window:
                    self.floating_window.set_timer("0s")

        except Exception as e:
            print(f"Error updating screen recording display: {e}")

    def _auto_export_data(self,  export_format: str = "xlsx"):
        """Auto-export telemetry data to the existing export directory."""
        telemetry_log = self.metrics_tracker.get_telemetry_log()
        if not telemetry_log:
            return

        export_dir = self.export_directory
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        exported_files = []

        if export_format.lower() == "csv":
            # CSV export
            csv_filename = f"{Config.DEFAULT_EXPORT_FILENAME}_{timestamp}.csv"
            csv_path = os.path.join(export_dir, csv_filename)

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                header = [col[0] for col in Config.TABLE_COLUMNS]
                writer.writerow(header)
                for entry in telemetry_log:
                    writer.writerow([
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
                        entry.get('rec_timestamp', ''),
                        entry.get('activity', 'None')
                    ])
            exported_files.append(csv_path)

        elif export_format.lower() == "xlsx":
            # XLSX export
            from openpyxl import Workbook
            xlsx_filename = f"{Config.DEFAULT_EXPORT_FILENAME}_{timestamp}.xlsx"
            xlsx_path = os.path.join(export_dir, xlsx_filename)

            wb = Workbook()
            ws = wb.active
            ws.title = "Telemetry Log"

            # Header
            header = [col[0] for col in Config.TABLE_COLUMNS]
            ws.append(header)

            # Data
            for entry in telemetry_log:
                ws.append([
                    entry['timestamp'],
                    entry['app_name'],
                    entry['window_title'],
                    float(f"{entry['key_rate']:.2f}"),
                    float(f"{entry['movement_rate']:.2f}"),
                    float(f"{entry['click_rate']:.2f}"),
                    float(f"{entry['scroll_rate']:.2f}"),
                    float(f"{entry['cpu_percent']:.2f}"),
                    float(f"{entry['memory_percent']:.2f}"),
                    float(f"{entry['network_mbps']:.2f}"),
                    float(f"{entry['disk_mbps']:.2f}"),
                    entry.get('rec_timestamp', ''),
                    entry.get('activity', 'None')
                ])

            wb.save(xlsx_path)
            exported_files.append(xlsx_path)

        # Add screen recording file if available
        recording_status = self.metrics_tracker.get_recording_status()
        if recording_status["output_path"] and os.path.exists(recording_status["output_path"]):
            exported_files.append(recording_status["output_path"])

        # Create summary file
        summary_path = os.path.join(export_dir, "export_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as summary_file:
            summary_file.write("Telemetry Monitor Export Summary\n")
            summary_file.write("==============================\n\n")
            summary_file.write(f"Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary_file.write(f"Export Directory: {export_dir}\n\n")
            summary_file.write("Files Exported:\n")
            for file_path in exported_files:
                summary_file.write(f"- {os.path.basename(file_path)}\n")
            summary_file.write(f"\nTotal Log Entries: {len(telemetry_log)}\n")
            
            # Activity summary
            activity_summary = self.metrics_tracker.activity_tracker.get_activity_summary()
            if activity_summary['activities']:
                summary_file.write("\nActivity Summary:\n")
                for activity_data in activity_summary['activities']:
                    summary_file.write(f"- {activity_data['name']}: {activity_data['formatted_duration']}\n")

            if recording_status["output_path"]:
                summary_file.write("\nScreen Recording:\n")
                summary_file.write(f"- Duration: {recording_status['duration']:.1f} seconds\n")
                summary_file.write(f"- FPS: {recording_status['fps']}\n")
                summary_file.write(f"- Screen: {recording_status['screen_name']}\n")

            """Auto-export telemetry data to the existing export directory."""
            telemetry_log = self.metrics_tracker.get_telemetry_log()
            if not telemetry_log:
                return

            export_dir = self.export_directory
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    def start_logging(self):
        """Start the logging process."""
        if hasattr(self.root, 'monitor'):
            
            # confirmation dialog  
            confirm = messagebox.askyesno(
                "Start Recording",
                "Are you sure you want to start monitoring and recording?\n\n"
                "This will:\n"
                "• Start tracking system metrics\n"
                "• Begin screen recording\n"
                "• Hide the main window",
                icon='question'
            )
            
            if not confirm:
                return
            
            # Ask for export directory
            directory_path = filedialog.askdirectory(
                title="Select Export Directory",
                initialdir=os.getcwd()
            )

            if not directory_path:
                return

            # Create timestamped directory
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            export_dir = os.path.join(directory_path, f"log-{timestamp}")
            os.makedirs(export_dir, exist_ok=True)

            # Store export directory for later use
            self.export_directory = export_dir
            
            # Start monitoring
            self.root.monitor.start_monitoring()
            
            # Start screen recording with export directory path
            video_path = os.path.join(export_dir, f"screen_recording_{timestamp}.mp4")
            success, message = self.metrics_tracker.start_screen_recording(video_path)
            if not success:
                self.show_error(f"Failed to start screen recording: {message}")

            # Update button states
            self.update_button_states('running')
            self.update_status_text('Monitoring Active', 'success')
            self.status_indicator.set_color('success')
            
            # Hide main window and show floating button
            self.root.withdraw()
            self.floating_window.show()
            self.floating_window.update_button_states('running')
            self.floating_window.set_timer("0s")
            self.floating_window._update_all_activity_buttons()
            
            self._create_screen_border(color="#FF0000", thickness=4)
            self._show_screen_border()

    def pause_logging(self):
        """Pause/Resume the logging process."""
        if hasattr(self.root, 'monitor'):
            monitor = self.root.monitor
            recording_status = self.metrics_tracker.get_recording_status()

            if recording_status.get("paused", False):
                # Resume monitoring
                monitor.resume_monitoring()

                # Resume screen recording
                success, message = self.metrics_tracker.resume_screen_recording()
                if not success:
                    self.show_error(f"Failed to resume screen recording: {message}")

                self.update_button_states('running')
                self.update_status_text('Monitoring Active', 'success')
                self.status_indicator.set_color('success')
                self.pause_btn.config(text="Pause")
                
                # Update floating button
                if self.floating_window:
                    self.floating_window.update_button_states('running')
                    
            else:
                # Pause monitoring
                monitor.pause_monitoring()

                # Pause screen recording
                success, message = self.metrics_tracker.pause_screen_recording()
                if not success:
                    self.show_error(f"Failed to pause screen recording: {message}")

                self.update_button_states('paused')
                self.update_status_text('Monitoring Paused', 'warning')
                self.status_indicator.set_color('warning')
                self.pause_btn.config(text="Resume")
                
                # pause the activity timer
                self.metrics_tracker.activity_tracker.pause_current_activity()
                
                # Update floating button
                if self.floating_window:
                    self.floating_window.update_button_states('paused')
                

    def stop_logging(self):
        """Stop the logging process and auto-export data."""
        if hasattr(self.root, 'monitor'):
            
            # confirmation dialog
            confirm = messagebox.askyesno(
                "Stop Recording",
                "Are you sure you want to stop monitoring and recording?\n\n"
                "This will:\n"
                "• Stop tracking system metrics\n"
                "• End screen recording\n"
                "• Show the main window",
                icon='warning'
            )
            
            if not confirm:
                return
            
            # stop the activity tracker
            self.metrics_tracker.activity_tracker.pause_current_activity()
            
            # Stop monitoring
            self.root.monitor.stop_monitoring()

            # Stop screen recording
            success, message = self.metrics_tracker.stop_screen_recording()
            if not success:
                self.show_error(f"Failed to stop screen recording: {message}")

            # Auto-export data if we have an export directory
            if hasattr(self, 'export_directory') and self.export_directory:
                try:
                    self._auto_export_data()
                    self.show_info("Data exported successfully to the selected directory")
                    # Clear the export directory after successful export
                    delattr(self, 'export_directory')
                except Exception as e:
                    self.show_error(f"Failed to auto-export data: {str(e)}")
            
            self.update_button_states('stopped')
            self.update_status_text('Monitoring Stopped', 'danger')
            self.status_indicator.set_color('danger')
            self.pause_btn.config(text="Pause")

            
            # Hide floating button and show main window
            if self.floating_window:
                self.floating_window.set_timer("0s")
                self.floating_window.update_button_states('stopped')
                self.metrics_tracker.activity_tracker.reset()
                self.floating_window.clear_activities() 
            
            self.root.after(200, self.floating_window.hide)
    
            self.root.deiconify()
            self.root.lift()
            
            self._hide_screen_border()

    def update_button_states(self, state: str):
        """Update button states based on monitoring state."""
        if state == 'running':
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
        elif state == 'paused':
            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.NORMAL)  # Keep pause button enabled for resume
            self.stop_btn.config(state=tk.NORMAL)
        elif state == 'stopped':
            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)

    def update_status_text(self, text: str, color: str):
        """Update status text with color."""
        self.status_text_label.config(text=f"● {text}", fg=self.colors[color])

    def set_initial_button_state(self):
        """Set initial button state when GUI is created."""
        self.update_button_states('stopped')
        self.update_status_text('Monitoring Stopped', 'danger')
        self.status_indicator.set_color('danger')

    def show_error(self, message: str):
        """Show error message."""
        messagebox.showerror("Error", message)

    def show_info(self, message: str):
        """Show info message."""
        messagebox.showinfo("Information", message)
        
    def create_floating_window(self):
        """Create the floating action button."""
        self.floating_window = FloatingControlWindow(
            on_pause=self.pause_logging,
            on_stop=self.stop_logging,
            on_show_window=self.show_main_window_from_floating,
            activity_tracker=self.metrics_tracker.activity_tracker  
        )
    
    def show_main_window_from_floating(self):
        """Show main window when clicked from floating button."""
        self.root.deiconify()
        self.root.lift()
        
    def _create_screen_border(self, color: str = "#FF0000", thickness: int = 4):
        """Create 4 border overlays around the screen."""
        if hasattr(self, "_screen_border_created") and self._screen_border_created:
            # Already created; just recolor and resize below
            self._update_screen_border(color=color, thickness=thickness)
            return

        self._border_thickness = thickness
        self._border_color = color
        self._border_windows = {}

        # Screen geometry (primary display)
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        def make_border(name, x, y, w, h):
            win = tk.Toplevel(self.root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            # Slight transparency if you like; set to 1.0 for solid
            win.attributes("-alpha", 1.0)
            # No focus
            try:
                win.attributes("-disabled", True)
            except Exception:
                pass
            # Use a Frame to color it
            frame = tk.Frame(win, bg=self._border_color)
            frame.pack(fill=tk.BOTH, expand=True)
            win.geometry(f"{w}x{h}+{x}+{y}")
            win.withdraw()
            self._border_windows[name] = win

        # Create 4 sides
        make_border("top",    0, 0,                    screen_w, thickness)
        make_border("bottom", 0, screen_h - thickness, screen_w, thickness)
        make_border("left",   0, 0,                    thickness, screen_h)
        make_border("right",  screen_w - thickness, 0, thickness, screen_h)

        self._screen_border_created = True


    def _update_screen_border(self, color: str = None, thickness: int = None):
        """Update border color/thickness & reposition if screen changes."""
        if not getattr(self, "_screen_border_created", False):
            return

        if color:
            self._border_color = color
        if thickness:
            self._border_thickness = thickness

        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        t = self._border_thickness

        # Recolor + reposition
        for name, win in self._border_windows.items():
            # Rebuild frame color
            for child in win.winfo_children():
                child.configure(bg=self._border_color)

        self._border_windows["top"].geometry(f"{screen_w}x{t}+0+0")
        self._border_windows["bottom"].geometry(f"{screen_w}x{t}+0+{screen_h - t}")
        self._border_windows["left"].geometry(f"{t}x{screen_h}+0+0")
        self._border_windows["right"].geometry(f"{t}x{screen_h}+{screen_w - t}+0")


    def _show_screen_border(self):
        """Show the 4 border overlays (create if needed)."""
        self._create_screen_border()
        for win in self._border_windows.values():
            win.deiconify()
            win.lift()


    def _hide_screen_border(self):
        """Hide the border overlays."""
        if not getattr(self, "_screen_border_created", False):
            return
        for win in self._border_windows.values():
            win.withdraw()


    def _destroy_screen_border(self):
        """Destroy border overlays (on app exit, optional)."""
        if not getattr(self, "_screen_border_created", False):
            return
        for win in self._border_windows.values():
            try:
                win.destroy()
            except Exception:
                pass
        self._border_windows.clear()
        self._screen_border_created = False
