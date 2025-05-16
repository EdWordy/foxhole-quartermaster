# main.py
"""
Main entry point for the Foxhole Quartermaster application.
"""

import os
import sys
from pathlib import Path

from core.quartermaster import QuartermasterApp
from ui.main_window import MainWindow


def setup_environment():
    """Set up the application environment."""
    # Create necessary directories
    os.makedirs('Reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)


def main():
    """Main entry point for the application."""
    # Set up environment
    setup_environment()
    
    # Initialize application
    app = QuartermasterApp()
    
    # Create and run UI
    window = MainWindow(app)
    window.mainloop()


if __name__ == "__main__":
    main()
