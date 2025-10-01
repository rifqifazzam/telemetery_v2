"""
Main entry point for the Telemetry Monitor application.
"""

import tkinter as tk
from telemetry_monitor import TelemetryMonitor

def main():
    """Main entry point"""
    root = tk.Tk()
    app = TelemetryMonitor(root)

    # Add monitor reference to root for GUI access
    root.monitor = app

    # Don't start monitoring automatically - let user control it
    # app.start_monitoring()

    # Initialize GUI with stopped state
    app.gui.set_initial_button_state()

    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()