"""
macOS Trackpad Pressure Monitor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A Python library for monitoring Force Touch trackpad pressure on macOS.

Basic usage:

    >>> from trackpad_pressure import PressureMonitor
    >>> 
    >>> def on_pressure(pressure, stage):
    ...     print(f"Pressure: {pressure:.3f}, Stage: {stage}")
    >>> 
    >>> monitor = PressureMonitor(callback=on_pressure)
    >>> monitor.start()  # Opens GUI and starts monitoring

For GUI-only usage:

    >>> from trackpad_pressure import start_gui_monitor
    >>> start_gui_monitor()
"""

from .monitor import PressureMonitor, PressureCallback
from .gui import start_gui_monitor

__version__ = "0.1.2"
__all__ = ["PressureMonitor", "PressureCallback", "start_gui_monitor"]