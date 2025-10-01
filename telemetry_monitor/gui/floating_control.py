"""
Floating control window component for the Telemetry Monitor application.
Provides a draggable overlay with monitoring controls that stays on top.
"""

import tkinter as tk
from typing import Optional, Callable
from ..config.settings import Config


class FloatingControlWindow:
    """
    Draggable floating control window with monitoring controls.
    
    Features:
    - Always on top overlay window
    - Draggable by header
    - Pause/Resume monitoring
    - Stop monitoring
    - Show main window
    - Real-time timer display
    - Status indicator
    """

    def __init__(
        self,
        on_pause: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_show_window: Optional[Callable] = None
    ):
        """
        Initialize floating control window.
        
        Args:
            on_pause: Callback for pause/resume action
            on_stop: Callback for stop action
            on_show_window: Callback for showing main window
        """
        # Window reference
        self.window = None
        
        # Callbacks
        self.on_pause = on_pause
        self.on_stop = on_stop
        self.on_show_window = on_show_window
        
        # Dragging state
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        
        # Widget references
        self.pause_btn = None
        self.stop_btn = None
        self.indicator = None
        self.timer_var = None
        self.timer_label = None
        
        # State tracking
        self.is_paused = False
        self.is_visible = False

    def create_window(self):
        """Create and configure the floating window."""
        if self.window:
            return
        
        # Create toplevel window
        self.window = tk.Toplevel()
        self.window.title("Telemetry Monitor")
        
        # Configure window properties
        self._configure_window_properties()
        
        # Build UI
        main_frame = self._create_main_frame()
        self._create_header(main_frame)
        self._create_controls(main_frame)
        
        # Position window
        self._position_window()
        
        self.is_visible = True

    def _configure_window_properties(self):
        """Configure window-level properties."""
        # Remove window decorations for clean look
        self.window.overrideredirect(True)
        
        # Keep window always on top
        self.window.attributes('-topmost', True)
        
        # Set transparency for modern look
        self.window.attributes('-alpha', 0.95)
        
        # Prevent window from appearing in taskbar (Windows)
        try:
            self.window.attributes('-toolwindow', True)
        except:
            pass

    def _create_main_frame(self) -> tk.Frame:
        """Create and return the main container frame."""
        main_frame = tk.Frame(
            self.window,
            bg=Config.COLORS.get('floating_bg', Config.COLORS['bg_secondary']),
            highlightbackground=Config.COLORS.get('floating_border', Config.COLORS['primary_start']),
            highlightthickness=2
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        return main_frame

    def _create_header(self, parent: tk.Frame):
        """Create the draggable header with title and controls."""
        header_frame = tk.Frame(
            parent,
            bg=Config.COLORS['bg_tertiary'],
            cursor="fleur"
        )
        header_frame.pack(fill=tk.X, padx=2, pady=(2, 0))
        
        # Left side - Status indicator and title
        self._create_status_section(header_frame)
        
        # Center - Timer
        self._create_timer_section(header_frame)
        
        # Right side - Show window button
        self._create_window_control(header_frame)
        
        # Bind dragging events
        self._bind_drag_events(header_frame)

    def _create_status_section(self, parent: tk.Frame):
        """Create status indicator and title."""
        # Status indicator
        indicator_frame = tk.Frame(parent, bg=Config.COLORS['bg_tertiary'])
        indicator_frame.pack(side=tk.LEFT, padx=Config.PADDING_SMALL, pady=Config.PADDING_SMALL)
        
        self.indicator = tk.Canvas(
            indicator_frame,
            width=12,
            height=12,
            bg=Config.COLORS['bg_tertiary'],
            highlightthickness=0
        )
        self.indicator.pack()
        self.update_indicator('success')
        
        # Title
        title_label = tk.Label(
            parent,
            text="Telemetry Monitor",
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE, "bold"),
            bg=Config.COLORS['bg_tertiary'],
            fg=Config.COLORS['text_primary'],
            cursor="fleur"
        )
        title_label.pack(side=tk.LEFT, padx=(0, Config.PADDING_SMALL), pady=Config.PADDING_SMALL)
        
        # Make title draggable too
        title_label.bind('<Button-1>', self.start_drag)
        title_label.bind('<B1-Motion>', self.on_drag)
        title_label.bind('<ButtonRelease-1>', self.stop_drag)

    def _create_timer_section(self, parent: tk.Frame):
        """Create timer display."""
        self.timer_var = tk.StringVar(value="0s")
        self.timer_label = tk.Label(
            parent,
            textvariable=self.timer_var,
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            bg=Config.COLORS['bg_tertiary'],
            fg=Config.COLORS['text_secondary']
        )
        self.timer_label.pack(side=tk.LEFT, padx=(Config.PADDING_SMALL, 0), pady=Config.PADDING_SMALL)

    def _create_window_control(self, parent: tk.Frame):
        """Create show main window button."""
        show_btn = tk.Button(
            parent,
            text="◱",  # Window icon
            command=self.show_main_window,
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE + 2),
            bg=Config.COLORS['bg_tertiary'],
            fg=Config.COLORS['text_primary'],
            relief=tk.FLAT,
            padx=Config.PADDING_SMALL,
            pady=2,
            cursor="hand2",
            width=2
        )
        show_btn.pack(side=tk.RIGHT, padx=Config.PADDING_SMALL)
        
        # Hover effect
        show_btn.bind('<Enter>', lambda e: show_btn.config(bg=Config.COLORS['bg_primary']))
        show_btn.bind('<Leave>', lambda e: show_btn.config(bg=Config.COLORS['bg_tertiary']))

    def _create_controls(self, parent: tk.Frame):
        """Create control buttons (pause and stop)."""
        buttons_frame = tk.Frame(
            parent,
            bg=Config.COLORS['bg_secondary']
        )
        buttons_frame.pack(fill=tk.X, padx=Config.PADDING_SMALL, pady=Config.PADDING_SMALL)
        
        # Pause/Resume button
        self.pause_btn = self._create_control_button(
            buttons_frame,
            text="Pause",
            command=self.handle_pause,
            bg_color=Config.COLORS['warning']
        )
        self.pause_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Stop button
        self.stop_btn = self._create_control_button(
            buttons_frame,
            text="Stop",
            command=self.handle_stop,
            bg_color=Config.COLORS['danger']
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

    def _create_control_button(
        self,
        parent: tk.Frame,
        text: str,
        command: Callable,
        bg_color: str
    ) -> tk.Button:
        """Create a styled control button."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg='white',
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            relief=tk.FLAT,
            padx=Config.PADDING_MEDIUM,
            pady=Config.PADDING_SMALL,
            cursor="hand2",
            state=tk.DISABLED
        )
        
        # Hover effects
        darker_color = self._darken_color(bg_color)
        btn.bind('<Enter>', lambda e: btn.config(bg=darker_color) if btn['state'] == tk.NORMAL else None)
        btn.bind('<Leave>', lambda e: btn.config(bg=bg_color) if btn['state'] == tk.NORMAL else None)
        
        return btn

    def _bind_drag_events(self, widget: tk.Widget):
        """Bind drag events to make widget draggable."""
        widget.bind('<Button-1>', self.start_drag)
        widget.bind('<B1-Motion>', self.on_drag)
        widget.bind('<ButtonRelease-1>', self.stop_drag)

    def _position_window(self):
        """Position window at bottom-right of screen."""
        self.window.update_idletasks()
        
        # Get dimensions
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate position (20px from right, 60px from bottom)
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60
        
        self.window.geometry(f"+{x}+{y}")

    # Drag and Drop Methods
    
    def start_drag(self, event):
        """Start dragging the window."""
        self.dragging = True
        self.offset_x = event.x
        self.offset_y = event.y

    def on_drag(self, event):
        """Handle window dragging motion."""
        if self.dragging:
            x = self.window.winfo_x() + event.x - self.offset_x
            y = self.window.winfo_y() + event.y - self.offset_y
            self.window.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        """Stop dragging the window."""
        self.dragging = False

    # Button Action Handlers
    
    def handle_pause(self):
        """Handle pause/resume button click."""
        if self.on_pause:
            self.on_pause()

    def handle_stop(self):
        """Handle stop button click."""
        if self.on_stop:
            self.on_stop()

    def show_main_window(self):
        """Handle show main window button click."""
        if self.on_show_window:
            self.on_show_window()

    # Public Control Methods
    
    def show(self):
        """Show the floating control window."""
        if not self.window:
            self.create_window()
        else:
            self.window.deiconify()
            self.window.lift()
        self.is_visible = True

    def hide(self):
        """Hide the floating control window."""
        if self.window:
            self.window.withdraw()
        self.is_visible = False

    def destroy(self):
        """Destroy the floating control window."""
        if self.window:
            self.window.destroy()
            self.window = None
        self.is_visible = False

    def toggle_visibility(self):
        """Toggle window visibility."""
        if self.is_visible:
            self.hide()
        else:
            self.show()

    # State Update Methods
    
    def update_button_states(self, state: str):
        """
        Update button states based on monitoring state.
        
        Args:
            state: 'running', 'paused', or 'stopped'
        """
        if not self.window:
            return
        
        state_config = {
            'running': {
                'pause_enabled': True,
                'stop_enabled': True,
                'pause_text': 'Pause',
                'indicator_color': 'success',
                'is_paused': False
            },
            'paused': {
                'pause_enabled': True,
                'stop_enabled': True,
                'pause_text': 'Resume',
                'indicator_color': 'warning',
                'is_paused': True
            },
            'stopped': {
                'pause_enabled': False,
                'stop_enabled': False,
                'pause_text': 'Pause',
                'indicator_color': 'danger',
                'is_paused': False
            }
        }
        
        config = state_config.get(state, state_config['stopped'])
        
        # Update button states
        self.pause_btn.config(
            state=tk.NORMAL if config['pause_enabled'] else tk.DISABLED,
            text=config['pause_text']
        )
        self.stop_btn.config(
            state=tk.NORMAL if config['stop_enabled'] else tk.DISABLED
        )
        
        # Update internal state
        self.is_paused = config['is_paused']
        
        # Update indicator
        self.update_indicator(config['indicator_color'])

    def update_indicator(self, color_name: str):
        """
        Update the status indicator color.
        
        Args:
            color_name: Color key from Config.COLORS
        """
        if not self.indicator:
            return
        
        color = Config.COLORS.get(color_name, Config.COLORS['success'])
        self.indicator.delete("all")
        self.indicator.create_oval(
            0, 0, 12, 12,
            fill=color,
            outline=""
        )

    def set_timer(self, text: str):
        """
        Update the timer display.
        
        Args:
            text: Timer text (e.g., "2m 13s")
        """
        if self.timer_var:
            self.timer_var.set(text)

    def set_title(self, title: str):
        """
        Update the window title.
        
        Args:
            title: New title text
        """
        if self.window:
            # Note: overrideredirect windows can't change title in taskbar
            # but we can update the label
            pass  # Could update title label if we store a reference

    # Utility Methods
    
    def _darken_color(self, color: str, factor: float = 0.2) -> str:
        """
        Darken a hex color by a factor.
        
        Args:
            color: Hex color string
            factor: Darkening factor (0-1)
            
        Returns:
            Darkened hex color
        """
        try:
            color = color.lstrip('#')
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color

    def move_to_position(self, x: int, y: int):
        """
        Move window to specific position.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        if self.window:
            self.window.geometry(f"+{x}+{y}")

    def get_position(self) -> tuple:
        """
        Get current window position.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        if self.window:
            return (self.window.winfo_x(), self.window.winfo_y())
        return (0, 0)

    def is_window_created(self) -> bool:
        """Check if window has been created."""
        return self.window is not None

    def get_state(self) -> dict:
        """
        Get current state of the floating window.
        
        Returns:
            Dictionary with current state information
        """
        return {
            'visible': self.is_visible,
            'paused': self.is_paused,
            'position': self.get_position() if self.window else None,
            'timer': self.timer_var.get() if self.timer_var else "0s"
        }