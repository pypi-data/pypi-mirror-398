"""Command-line entry point."""

import sys
from .gui import start_gui_monitor

def main():
    """Run the GUI pressure monitor."""
    print("Starting trackpad pressure monitor...")
    start_gui_monitor()

if __name__ == "__main__":
    main()