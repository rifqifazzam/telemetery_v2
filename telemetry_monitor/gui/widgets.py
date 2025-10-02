"""
Custom GUI widgets for the Telemetry Monitor application.
"""

import tkinter as tk
from tkinter import ttk, Canvas, Frame
from typing import List, Tuple, Callable, Optional
from ..config.settings import Config


class ModernTable(ttk.Frame):
    """Modern scrollable table widget with mouse wheel support and resizable columns."""

    def __init__(self, parent, columns: List[Tuple[str, int]], height: int = 15, **kwargs):
        super().__init__(parent, **kwargs)
        self.columns = columns
        self.height = height
        self.row_height = 24
        self.header_height = 32
        self.pagination_height = 40  # Height for pagination controls
        self.data_rows = []
        self.offset = 0
        self.selected_row = None
        self.on_row_click_callback = None

        # Column resizing variables
        self.resizing = False
        self.resize_column_index = -1
        self.resize_start_x = 0
        self.resize_original_widths = []
        self.column_separator_tags = []

        # Pagination variables
        self.current_page = 1
        self.page_size = Config.TABLE_PAGE_SIZE
        self.total_pages = 1
        self.page_buttons = []

        self.setup_style()
        self.create_widgets()
        self.bind_mouse_wheel()

    def setup_style(self):
        """Setup modern styling for the table."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure canvas background
        self.configure(style='Modern.TFrame')
        style.configure('Modern.TFrame', background=Config.COLORS['bg_primary'])

    def create_widgets(self):
        """Create table widgets with modern styling and horizontal scrolling."""
        # Main container
        self.container = Frame(self, bg=Config.COLORS['bg_secondary'], relief=tk.RAISED, bd=1)
        self.container.pack(fill=tk.BOTH, expand=True,
                             padx=(Config.PADDING_MEDIUM, Config.PADDING_MEDIUM),
                             pady=(0, Config.PADDING_MEDIUM))

        # Header canvas with horizontal scrollbar
        self.header_frame = Frame(self.container, bg=Config.COLORS['bg_primary'])
        self.header_frame.pack(fill=tk.X)

        self.header_canvas = Canvas(
            self.header_frame,
            height=self.header_height,
            bg=Config.COLORS['bg_tertiary'],
            highlightthickness=0,
            width=sum(col[1] for col in self.columns)
        )

        # Horizontal scrollbar for header
        self.h_scrollbar = ttk.Scrollbar(
            self.header_frame,
            orient="horizontal",
            command=self.on_horizontal_scroll
        )

        self.header_canvas.configure(xscrollcommand=self.h_scrollbar.set)

        # Pack header and scrollbar
        self.header_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Data canvas with scrollbars
        self.data_frame = Frame(self.container, bg=Config.COLORS['bg_primary'])
        self.data_frame.pack(fill=tk.BOTH, expand=True)

        self.data_canvas = Canvas(
            self.data_frame,
            bg=Config.COLORS['bg_secondary'],
            highlightthickness=0,
            width=sum(col[1] for col in self.columns)
        )

        # Vertical scrollbar
        self.v_scrollbar = ttk.Scrollbar(
            self.data_frame,
            orient="vertical",
            command=self.data_canvas.yview
        )

        # Horizontal scrollbar for data
        self.data_h_scrollbar = ttk.Scrollbar(
            self.data_frame,
            orient="horizontal",
            command=self.on_horizontal_scroll
        )

        self.data_canvas.configure(yscrollcommand=self.v_scrollbar.set,
                                   xscrollcommand=self.data_h_scrollbar.set)

        # Grid layout
        self.data_canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.data_h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.data_frame.grid_rowconfigure(0, weight=1)
        self.data_frame.grid_columnconfigure(0, weight=1)

        # Create header
        self.create_header()

        # Create pagination controls
        self.create_pagination_controls()

        # Bind mouse events
        self.data_canvas.bind('<Configure>', self.on_canvas_configure)
        self.data_canvas.bind('<Motion>', self.on_mouse_motion)
        self.data_canvas.bind('<Button-1>', self.on_mouse_click)

    def create_header(self):
        """Create modern table header with resizable columns."""
        self.header_canvas.delete("all")
        self.column_separator_tags = []

        x_offset = 0
        for col_index, (col_name, col_width) in enumerate(self.columns):
            # Header background
            self.header_canvas.create_rectangle(
                x_offset, 0, x_offset + col_width, self.header_height,
                fill=Config.COLORS['bg_tertiary'],
                outline=Config.COLORS['border'],
                width=1,
                tags=f"header_bg_{col_index}"
            )

            # Header text
            self.header_canvas.create_text(
                x_offset + col_width // 2,
                self.header_height // 2,
                text=col_name,
                fill=Config.COLORS['text_primary'],
                font=(Config.FONT_FAMILY, Config.TABLE_HEADER_FONT_SIZE, "bold"),
                anchor="center"
            )

            # Column separator (resize handle)
            if x_offset + col_width < sum(col[1] for col in self.columns):
                separator_tag = f"separator_{col_index}"
                self.header_canvas.create_line(
                    x_offset + col_width, 4,
                    x_offset + col_width, self.header_height - 4,
                    fill=Config.COLORS['border'],
                    width=2,
                    tags=separator_tag
                )
                self.column_separator_tags.append(separator_tag)

                # Create invisible resize handle area for easier mouse interaction
                handle_tag = f"resize_handle_{col_index}"
                self.header_canvas.create_rectangle(
                    x_offset + col_width - 3, 0,
                    x_offset + col_width + 3, self.header_height,
                    fill="",
                    outline="",
                    tags=handle_tag
                )
                self.column_separator_tags.append(handle_tag)

            x_offset += col_width

        # Bind mouse events for column resizing
        self.bind_column_resize_events()

    def create_pagination_controls(self):
        """Create pagination controls at the bottom of the table."""
        # Pagination frame
        self.pagination_frame = Frame(
            self.container,
            bg=Config.COLORS['bg_secondary'],
            height=self.pagination_height
        )
        self.pagination_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.pagination_frame.pack_propagate(False)

        # Pagination content frame
        pagination_content = Frame(
            self.pagination_frame,
            bg=Config.COLORS['bg_secondary']
        )
        pagination_content.pack(fill=tk.BOTH, expand=True, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_SMALL)

        # Page info label
        self.page_info_label = tk.Label(
            pagination_content,
            text="Page 1 of 1",
            font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE),
            bg=Config.COLORS['bg_secondary'],
            fg=Config.COLORS['text_secondary']
        )
        self.page_info_label.pack(side=tk.LEFT)

        # Button container
        button_container = Frame(pagination_content, bg=Config.COLORS['bg_secondary'])
        button_container.pack(side=tk.RIGHT)

        # Previous button
        self.prev_button = tk.Button(
            button_container,
            text="◀",
            command=self.go_to_previous_page,
            font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE + 2),
            bg=Config.COLORS['bg_tertiary'],
            fg=Config.COLORS['text_primary'],
            relief=tk.FLAT,
            padx=Config.PADDING_SMALL,
            pady=2,
            state=tk.DISABLED
        )
        self.prev_button.pack(side=tk.LEFT, padx=2)

        # Page buttons container
        self.page_buttons_container = Frame(button_container, bg=Config.COLORS['bg_secondary'])
        self.page_buttons_container.pack(side=tk.LEFT, padx=2)

        # Next button
        self.next_button = tk.Button(
            button_container,
            text="▶",
            command=self.go_to_next_page,
            font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE + 2),
            bg=Config.COLORS['bg_tertiary'],
            fg=Config.COLORS['text_primary'],
            relief=tk.FLAT,
            padx=Config.PADDING_SMALL,
            pady=2,
            state=tk.DISABLED
        )
        self.next_button.pack(side=tk.LEFT, padx=2)

        # Rows per page selector
        rows_frame = Frame(pagination_content, bg=Config.COLORS['bg_secondary'])
        rows_frame.pack(side=tk.RIGHT, padx=Config.PADDING_MEDIUM)

        tk.Label(
            rows_frame,
            text="Rows:",
            font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE),
            bg=Config.COLORS['bg_secondary'],
            fg=Config.COLORS['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, Config.PADDING_SMALL))

        self.rows_per_page_var = tk.StringVar(value=str(self.page_size))
        self.rows_selector = ttk.Combobox(
            rows_frame,
            textvariable=self.rows_per_page_var,
            values=["10", "25", "50", "100"],
            state="readonly",
            width=6,
            font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE)
        )
        self.rows_selector.pack(side=tk.LEFT)
        self.rows_selector.bind('<<ComboboxSelected>>', self.on_rows_per_page_changed)

    def bind_column_resize_events(self):
        """Bind mouse events for column resizing functionality."""
        # Bind events to header canvas for resizing
        self.header_canvas.bind('<Motion>', self.on_header_motion)
        self.header_canvas.bind('<Button-1>', self.on_header_click)
        self.header_canvas.bind('<B1-Motion>', self.on_header_drag)
        self.header_canvas.bind('<ButtonRelease-1>', self.on_header_release)

    def bind_mouse_wheel(self):
        """Bind mouse wheel events for scrolling."""
        def on_mousewheel(event):
            # Windows mouse wheel
            if event.delta:
                scroll_amount = -1 if event.delta > 0 else 1
            else:
                # Linux/Mac mouse wheel
                scroll_amount = -1 if event.num == 4 else 1

            self.scroll_to(self.offset + scroll_amount * 3)
            return "break"

        self.data_canvas.bind('<MouseWheel>', on_mousewheel)
        self.data_canvas.bind('<Button-4>', on_mousewheel)
        self.data_canvas.bind('<Button-5>', on_mousewheel)

    def scroll_to(self, new_offset: int):
        """Scroll to specific row offset."""
        max_offset = max(0, len(self.data_rows) - self.height)
        self.offset = max(0, min(new_offset, max_offset))
        self.refresh_display()

    def on_canvas_configure(self, event):
        """Handle canvas resize."""
        self.refresh_display()

    def on_mouse_motion(self, event):
        """Handle mouse motion for hover effects."""
        row_index = self.get_row_from_y(event.y)
        if row_index != self.selected_row:
            self.selected_row = row_index
            self.refresh_display()

    def on_mouse_click(self, event):
        """Handle mouse click."""
        row_index = self.get_row_from_y(event.y)
        paginated_data = self.get_paginated_data()
        if 0 <= row_index < len(paginated_data):
            # Calculate actual index in the full dataset
            actual_index = (self.current_page - 1) * self.page_size + row_index
            self.on_row_clicked(actual_index)

    def get_row_from_y(self, y: int) -> int:
        """Get row index from y coordinate."""
        return y // self.row_height

    def on_row_clicked(self, row_index: int):
        """Handle row click event."""
        if self.on_row_click_callback:
            self.on_row_click_callback(row_index)

    def on_header_motion(self, event):
        """Handle mouse motion over header for resize cursor."""
        # Check if mouse is over a column separator
        overlapping = self.header_canvas.find_overlapping(
            event.x - 2, event.y - 2, event.x + 2, event.y + 2
        )

        resize_handle_found = False
        for item in overlapping:
            tags = self.header_canvas.gettags(item)
            for tag in tags:
                if tag.startswith('resize_handle_'):
                    resize_handle_found = True
                    break

        # Change cursor to resize cursor when over separator
        if resize_handle_found and not self.resizing:
            self.header_canvas.config(cursor="sb_h_double_arrow")
        elif not self.resizing:
            self.header_canvas.config(cursor="")

    def on_header_click(self, event):
        """Handle mouse click on header."""
        # Check if click is on a resize handle
        overlapping = self.header_canvas.find_overlapping(
            event.x - 3, event.y - 3, event.x + 3, event.y + 3
        )

        for item in overlapping:
            tags = self.header_canvas.gettags(item)
            for tag in tags:
                if tag.startswith('resize_handle_'):
                    # Start resizing
                    self.resizing = True
                    self.resize_column_index = int(tag.split('_')[-1])
                    self.resize_start_x = event.x
                    self.resize_original_widths = [col[1] for col in self.columns]

                    # Change cursor to indicate resizing
                    self.header_canvas.config(cursor="sb_h_double_arrow")
                    return

    def on_header_drag(self, event):
        """Handle mouse drag for column resizing."""
        if self.resizing and self.resize_column_index >= 0:
            # Calculate the width change
            delta_x = event.x - self.resize_start_x

            # Calculate new column widths
            new_widths = self.resize_original_widths.copy()

            # Update the width of the column being resized and the next column
            if self.resize_column_index < len(new_widths) - 1:
                # Resize current column
                new_widths[self.resize_column_index] = max(
                    50,  # Minimum width
                    self.resize_original_widths[self.resize_column_index] + delta_x
                )

                # Update the columns list
                updated_columns = []
                for i, (col_name, _) in enumerate(self.columns):
                    updated_columns.append((col_name, new_widths[i]))

                self.columns = updated_columns

                # Redraw header with new widths
                self.create_header()

                # Refresh the display to apply new column widths
                self.refresh_display()

                # Update canvas width to accommodate new column widths
                new_total_width = sum(col[1] for col in self.columns)
                self.data_canvas.config(width=new_total_width)
                self.header_canvas.config(width=new_total_width)

                # Update scroll region
                self.update_scroll_region()

    def on_header_release(self, event):
        """Handle mouse release after column resizing."""
        if self.resizing:
            self.resizing = False
            self.resize_column_index = -1
            self.resize_start_x = 0
            self.resize_original_widths = []

            # Reset cursor
            self.header_canvas.config(cursor="")

    def on_horizontal_scroll(self, *args):
        """Handle horizontal scrolling for both header and data canvas."""
        # Sync horizontal scrolling between header and data
        self.header_canvas.xview(*args)
        self.data_canvas.xview(*args)

    def update_scroll_region(self):
        """Update the scroll region for both canvases."""
        total_width = sum(col[1] for col in self.columns)
        total_height = len(self.data_rows) * self.row_height

        # Update header canvas scroll region
        self.header_canvas.configure(scrollregion=(0, 0, total_width, self.header_height))

        # Update data canvas scroll region
        self.data_canvas.configure(scrollregion=(0, 0, total_width, total_height))

    def update_pagination_info(self):
        """Update pagination information and controls."""
        if not self.data_rows:
            self.total_pages = 1
            self.current_page = 1
        else:
            self.total_pages = max(1, (len(self.data_rows) + self.page_size - 1) // self.page_size)
            # Ensure current page is within bounds
            self.current_page = max(1, min(self.current_page, self.total_pages))

        # Update page info label
        self.page_info_label.config(text=f"Page {self.current_page} of {self.total_pages}")

        # Update navigation buttons
        self.prev_button.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_page < self.total_pages else tk.DISABLED)

        # Update page buttons
        self.update_page_buttons()

    def update_page_buttons(self):
        """Update page number buttons."""
        # Clear existing buttons
        for widget in self.page_buttons_container.winfo_children():
            widget.destroy()

        # Determine which page buttons to show
        max_buttons = 5
        start_page = max(1, self.current_page - max_buttons // 2)
        end_page = min(self.total_pages + 1, start_page + max_buttons)

        if end_page - start_page < max_buttons:
            start_page = max(1, end_page - max_buttons)

        # Create page buttons
        for page_num in range(start_page, end_page):
            if page_num > self.total_pages:
                break

            btn = tk.Button(
                self.page_buttons_container,
                text=str(page_num),
                command=lambda p=page_num: self.go_to_page(p),
                font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE),
                bg=Config.COLORS['primary_start'] if page_num == self.current_page else Config.COLORS['bg_tertiary'],
                fg='white' if page_num == self.current_page else Config.COLORS['text_primary'],
                relief=tk.FLAT,
                padx=Config.PADDING_SMALL,
                pady=2
            )
            btn.pack(side=tk.LEFT, padx=1)

    def go_to_page(self, page_num):
        """Navigate to a specific page."""
        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num
            self.refresh_display()

    def go_to_previous_page(self):
        """Navigate to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_display()

    def go_to_next_page(self):
        """Navigate to the next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_display()

    def on_rows_per_page_changed(self, event):
        """Handle rows per page selection change."""
        new_page_size = int(self.rows_per_page_var.get())
        if new_page_size != self.page_size:
            self.page_size = new_page_size
            # Go to first page when changing page size
            self.current_page = 1
            self.refresh_display()

    def get_paginated_data(self):
        """Get data for the current page."""
        if not self.data_rows:
            return []

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.data_rows))

        return self.data_rows[start_idx:end_idx]

    def set_on_row_click(self, callback: Callable[[int], None]):
        """Set callback for row click events."""
        self.on_row_click_callback = callback

    def update_data(self, data_rows: List[List]):
        """Update table data with smooth animation."""
        self.data_rows = data_rows
        self.offset = 0
        self.current_page = 1  # Reset to first page when new data is loaded
        self.refresh_display()

    def refresh_display(self):
        """Refresh the table display."""
        self.data_canvas.delete("all")

        if not self.data_rows:
            self.show_empty_state()
            # Still update pagination info for empty state
            self.update_pagination_info()
            return

        # Get paginated data for current page
        paginated_data = self.get_paginated_data()

        # Update pagination info
        self.update_pagination_info()

        # Draw rows for current page
        y_offset = 0
        for i, row_data in enumerate(paginated_data):
            is_even = i % 2 == 0
            is_hovered = i == self.selected_row

            self.draw_row(row_data, y_offset, is_even, is_hovered)
            y_offset += self.row_height

        # Update scroll region
        self.update_scroll_region()

    def draw_row(self, row_data: List, y_offset: int, is_even: bool, is_hovered: bool):
        """Draw a single row."""
        bg_color = Config.COLORS['bg_secondary'] if is_even else Config.COLORS['bg_primary']
        if is_hovered:
            bg_color = Config.COLORS['bg_tertiary']

        # Row background
        self.data_canvas.create_rectangle(
            0, y_offset, sum(col[1] for col in self.columns), y_offset + self.row_height,
            fill=bg_color,
            outline="",
            tags=f"row_{y_offset}"
        )

        # Row data
        x_offset = 0
        for i, (value, (col_name, col_width)) in enumerate(zip(row_data, self.columns)):
            text_color = Config.COLORS['text_secondary'] if i > 2 else Config.COLORS['text_primary']

            self.data_canvas.create_text(
                x_offset + col_width // 2,
                y_offset + self.row_height // 2,
                text=str(value),
                fill=text_color,
                font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE),
                anchor="center"
            )

            # Column separator
            if i < len(self.columns) - 1:
                self.data_canvas.create_line(
                    x_offset + col_width, y_offset + 2,
                    x_offset + col_width, y_offset + self.row_height - 2,
                    fill=Config.COLORS['border'],
                    width=1
                )

            x_offset += col_width

    def show_empty_state(self):
        """Show empty state message."""
        canvas_width = sum(col[1] for col in self.columns)
        self.data_canvas.create_text(
            canvas_width // 2,
            self.height * self.row_height // 2,
            text="No data available",
            fill=Config.COLORS['text_muted'],
            font=(Config.FONT_FAMILY, Config.TABLE_DATA_FONT_SIZE),
            anchor="center"
        )


class MetricCard(Frame):
    """Modern metric card with gradient styling."""

    def __init__(self, parent, title: str, initial_value: str, color_scheme: str, icon: str, **kwargs):
        super().__init__(parent, bg=Config.COLORS['bg_secondary'], **kwargs)

        self.title = title
        self.icon = icon
        self.value_label = None

        # Get gradient colors
        if color_scheme in Config.COLORS:
            colors = Config.COLORS[color_scheme] if isinstance(Config.COLORS[color_scheme], list) else [Config.COLORS[color_scheme], Config.COLORS[color_scheme]]
        else:
            colors = Config.COLORS['primary_gradient']

        self.colors = colors

        self.create_widgets()

    def create_widgets(self):
        """Create metric card widgets."""
        # Create border
        self.config(relief=tk.RAISED, bd=1)

        # Card content
        card_content = Frame(self, bg=Config.COLORS['bg_secondary'])
        card_content.pack(fill=tk.BOTH, expand=True, padx=Config.PADDING_MEDIUM, pady=Config.PADDING_MEDIUM)

        # Header with icon and title
        header_frame = Frame(card_content, bg=Config.COLORS['bg_secondary'])
        header_frame.pack(fill=tk.X, pady=(0, Config.PADDING_SMALL))

        # Icon
        icon_label = tk.Label(
            header_frame,
            text=self.icon,
            font=(Config.FONT_FAMILY, Config.METRIC_VALUE_FONT_SIZE - 4),
            bg=Config.COLORS['bg_secondary'],
            fg=self.colors[0]
        )
        icon_label.pack(side=tk.LEFT)

        # Title
        title_label = tk.Label(
            header_frame,
            text=self.title,
            font=(Config.FONT_FAMILY, Config.METRIC_TITLE_FONT_SIZE, "bold"),
            bg=Config.COLORS['bg_secondary'],
            fg=Config.COLORS['text_secondary']
        )
        title_label.pack(side=tk.LEFT, padx=(Config.PADDING_SMALL, 0))

        # Value
        self.value_label = tk.Label(
            card_content,
            text="0",
            font=(Config.FONT_FAMILY, Config.METRIC_VALUE_FONT_SIZE, "bold"),
            bg=Config.COLORS['bg_secondary'],
            fg=self.colors[0]
        )
        self.value_label.pack(pady=Config.PADDING_SMALL)

    def update_value(self, value: str):
        """Update the metric value."""
        if self.value_label:
            self.value_label.config(text=value)

    def update_color(self, color_scheme: str):
        """Update the color scheme."""
        if color_scheme in Config.COLORS:
            colors = Config.COLORS[color_scheme] if isinstance(Config.COLORS[color_scheme], list) else [Config.COLORS[color_scheme], Config.COLORS[color_scheme]]
        else:
            colors = Config.COLORS['primary_gradient']

        self.colors = colors
        if self.value_label:
            self.value_label.config(fg=self.colors[0])


class StatusIndicator(Frame):
    """Status indicator with customizable color."""

    def __init__(self, parent, size: int = 12, initial_color: str = 'success', **kwargs):
        super().__init__(parent, **kwargs)

        self.size = size
        self.canvas = Canvas(
            self,
            width=size,
            height=size,
            bg=Config.COLORS['bg_secondary'],
            highlightthickness=0
        )
        self.canvas.pack()

        self.set_color(initial_color)

    def set_color(self, color_name: str):
        """Set the indicator color."""
        color = Config.COLORS.get(color_name, Config.COLORS['success'])
        self.canvas.delete("all")
        self.canvas.create_oval(
            0, 0, self.size, self.size,
            fill=color,
            outline=""
        )
   