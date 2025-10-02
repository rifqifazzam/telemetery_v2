"""
Floating control window component for the Telemetry Monitor application.
Provides a draggable overlay with monitoring controls that stays on top.
"""

import tkinter as tk
from typing import Optional, Callable
from ..config.settings import Config
from tkinter import simpledialog

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
    - Activity tracking with individual timers
    """

    def __init__(
        self,
        on_pause: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_show_window: Optional[Callable] = None,
        activity_tracker = None
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
        
        # Activity tracker
        self.activity_tracker = activity_tracker
        
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
        self.activity_list_frame = None
        self.activity_buttons = {}
        self.activity_canvas = None
        self.activity_scrollbar = None
        
        # State tracking
        self.is_paused = False
        self.is_visible = False
        
        # Activity update scheduling
        self.activity_update_scheduled = False

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
        self._create_activity_section(main_frame)
        
        # Position window
        self._position_window()
        
        self.is_visible = True
        
        # Start activity update loop
        self._schedule_activity_update()

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
        
    def _create_activity_section(self, parent: tk.Frame):
        """Create activity tracking section."""
        # Activity section container
        activity_section = tk.Frame(
            parent,
            bg=Config.COLORS['bg_secondary']
        )
        activity_section.pack(fill=tk.BOTH, expand=True, padx=Config.PADDING_SMALL, pady=(0, Config.PADDING_SMALL))
        
        # Activity header with Add button
        activity_header = tk.Frame(
            activity_section,
            bg=Config.COLORS['bg_secondary']
        )
        activity_header.pack(fill=tk.X, pady=(Config.PADDING_SMALL, Config.PADDING_SMALL))
        
        tk.Label(
            activity_header,
            text="List of Process",
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE, "bold"),
            bg=Config.COLORS['bg_secondary'],
            fg=Config.COLORS['text_primary']
        ).pack(side=tk.LEFT)
        
        # Add activity button
        add_btn = tk.Button(
            activity_header,
            text="+ Add",
            command=self.add_activity,
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE - 1),
            bg=Config.COLORS['success'],
            fg='white',
            relief=tk.FLAT,
            padx=Config.PADDING_SMALL,
            pady=2,
            cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT)
        
        # Hover effect for add button
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg=self._darken_color(Config.COLORS['success'])))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=Config.COLORS['success']))
        
        # Scrollable activity list
        self._create_activity_list(activity_section)
        
    def _create_activity_list(self, parent: tk.Frame):
        """Create scrollable activity list container."""
        # Container for canvas and scrollbar
        list_container = tk.Frame(
            parent,
            bg=Config.COLORS['bg_secondary']
        )
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        self.activity_canvas = tk.Canvas(
            list_container,
            bg=Config.COLORS['bg_secondary'],
            highlightthickness=0,
            height=0  # Start with 0 height, will expand as activities are added
        )
        self.activity_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar (initially hidden)
        self.activity_scrollbar = tk.Scrollbar(
            list_container,
            orient=tk.VERTICAL,
            command=self.activity_canvas.yview
        )
        
        # Configure canvas
        self.activity_canvas.configure(yscrollcommand=self.activity_scrollbar.set)
        
        # Frame inside canvas for activity buttons
        self.activity_list_frame = tk.Frame(
            self.activity_canvas,
            bg=Config.COLORS['bg_secondary']
        )
        
        self.activity_canvas_window = self.activity_canvas.create_window(
            (0, 0),
            window=self.activity_list_frame,
            anchor="nw"
        )
        
        # Bind configuration
        self.activity_list_frame.bind('<Configure>', self._on_activity_list_configure)
        self.activity_canvas.bind('<Configure>', self._on_activity_canvas_configure)
        
        # Mouse wheel scrolling
        self.activity_canvas.bind('<MouseWheel>', self._on_activity_mousewheel)
        self.activity_canvas.bind('<Button-4>', self._on_activity_mousewheel)
        self.activity_canvas.bind('<Button-5>', self._on_activity_mousewheel)
        
        
    def _on_activity_list_configure(self, event=None):
        """Handle activity list frame configuration."""
        self.activity_canvas.configure(scrollregion=self.activity_canvas.bbox("all"))
        
        # Show/hide scrollbar based on content height
        canvas_height = self.activity_canvas.winfo_height()
        content_height = self.activity_list_frame.winfo_reqheight()
        
        if content_height > canvas_height and canvas_height > 0:
            self.activity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.activity_scrollbar.pack_forget()
        
        # Adjust canvas height based on content (max 200px)
        new_height = min(content_height, 200)
        if new_height != self.activity_canvas.winfo_height():
            self.activity_canvas.config(height=new_height)

    def _on_activity_canvas_configure(self, event):
        """Handle activity canvas configuration."""
        self.activity_canvas.itemconfig(self.activity_canvas_window, width=event.width)

    def _on_activity_mousewheel(self, event):
        """Handle mouse wheel scrolling in activity list."""
        if event.num == 4:
            self.activity_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.activity_canvas.yview_scroll(1, "units")
        else:
            self.activity_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
        
        
    # Activity Management Methods
    
    def add_activity(self):
        """Show dialog to add a new activity."""
        if not self.activity_tracker:
            return
        
        activity_name = simpledialog.askstring(
            "Add Process",
            "Masukkan nama proses:",
            parent=self.window
        )
        
        if activity_name and activity_name.strip():
            activity_name = activity_name.strip()
            success = self.activity_tracker.add_activity(activity_name)
            
            if success:
                self._create_activity_button(activity_name)
            else:
                # Activity already exists
                pass

    def _create_activity_button(self, activity_name: str):
        """Create a button for an activity."""
        # Button container
        btn_container = tk.Frame(
            self.activity_list_frame,
            bg=Config.COLORS['bg_secondary']
        )
        btn_container.pack(fill=tk.X, pady=2)
        
        # Activity button
        btn = tk.Button(
            btn_container,
            text="",  # Will be set by update method
            command=lambda: self.select_activity(activity_name),
            bg=Config.COLORS['bg_tertiary'],
            fg=Config.COLORS['text_secondary'],
            font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE),
            relief=tk.FLAT,
            padx=Config.PADDING_MEDIUM,
            pady=Config.PADDING_SMALL,
            cursor="hand2",
            anchor="w",
            justify=tk.LEFT
        )
        btn.pack(fill=tk.X)
        
        # Store button reference
        self.activity_buttons[activity_name] = btn
        
        # Hover effects
        def on_enter(e):
            if btn['bg'] != Config.COLORS['success']:
                btn.config(bg=Config.COLORS['bg_primary'])
        
        def on_leave(e):
            if btn['bg'] != Config.COLORS['success']:
                btn.config(bg=Config.COLORS['bg_tertiary'])
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        # Create tooltip for long text
        self._create_tooltip(btn, activity_name)
        
        # Update button text
        self._update_activity_button(activity_name)

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                relief=tk.SOLID,
                borderwidth=1,
                font=(Config.FONT_FAMILY, Config.BUTTON_FONT_SIZE - 1)
            )
            label.pack()
        
        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def select_activity(self, activity_name: str):
        """Select an activity as active."""
        if not self.activity_tracker:
            return
        
        success = self.activity_tracker.set_active_activity(activity_name)
        if success:
            self._update_all_activity_buttons()

    def _update_activity_button(self, activity_name: str):
        """Update a single activity button's appearance."""
        if activity_name not in self.activity_buttons:
            return
        
        btn = self.activity_buttons[activity_name]
        activity = self.activity_tracker.get_activity(activity_name)
        
        if not activity:
            return
        
        # Get duration
        duration = activity.get_formatted_duration()
        
        # Truncate long names for display
        display_name = activity_name
        max_length = 20
        if len(display_name) > max_length:
            display_name = display_name[:max_length-3] + "..."
        
        # Check if active
        is_active = self.activity_tracker.get_current_activity_name() == activity_name
        
        if is_active:
            # Active state
            btn.config(
                text=f"✓ {display_name}  {duration}",
                bg=Config.COLORS['success'],
                fg='white'
            )
        else:
            # Inactive state
            btn.config(
                text=f"  {display_name}  {duration}",
                bg=Config.COLORS['bg_tertiary'],
                fg=Config.COLORS['text_secondary']
            )

    def _update_all_activity_buttons(self):
        """Update all activity buttons."""
        if not self.activity_tracker:
            return
        
        for activity_name in self.activity_buttons.keys():
            self._update_activity_button(activity_name)

    def _schedule_activity_update(self):
        """Schedule periodic activity display updates."""
        if not self.window or not self.is_visible:
            return
        
        if not self.activity_update_scheduled:
            self.activity_update_scheduled = True
            self._update_all_activity_buttons()
            self.window.after(500, self._activity_update_loop)

    def _activity_update_loop(self):
        """Loop for updating activity displays."""
        if not self.window or not self.is_visible:
            self.activity_update_scheduled = False
            return
        
        self._update_all_activity_buttons()
        self.window.after(500, self._activity_update_loop)

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
        
        self.activity_update_scheduled = False  
        self._schedule_activity_update()

    def hide(self):
        """Hide the floating control window."""
        if self.window:
            self.window.withdraw()
        self.is_visible = False
        self.activity_update_scheduled = False

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
        
    def clear_activities(self):
        """Clear all activity buttons from the UI."""
        
        self.activity_update_scheduled = False
        
        # Destroy all activity button containers
        for widget in self.activity_list_frame.winfo_children():
            widget.destroy()
        
        # Clear button references
        self.activity_buttons.clear()
        
        # Reset canvas height
        if self.activity_canvas:
            self.activity_canvas.config(height=0)
        
