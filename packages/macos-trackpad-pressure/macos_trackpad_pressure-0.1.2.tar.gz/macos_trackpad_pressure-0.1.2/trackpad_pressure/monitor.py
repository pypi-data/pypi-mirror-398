"""Core pressure monitoring functionality."""

import sys
from typing import Callable, Optional
from Cocoa import NSEvent

PressureCallback = Callable[[float, int], None]

class PressureMonitor:
    """
    Monitor trackpad pressure events.
    
    Args:
        callback: Function called when pressure changes. 
                 Receives (pressure: float, stage: int)
        
    Example:
        >>> def handle_pressure(pressure, stage):
        ...     print(f"Pressure: {pressure}")
        >>> 
        >>> monitor = PressureMonitor(callback=handle_pressure)
        >>> monitor.start()
    """
    
    def __init__(self, callback: Optional[PressureCallback] = None):
        self.callback = callback
        self._pressure = 0.0
        self._stage = 0
        
    @property
    def current_pressure(self) -> float:
        """Get the current pressure value (0.0 - 1.0)."""
        return self._pressure
        
    @property
    def current_stage(self) -> int:
        """Get the current Force Touch stage (0, 1, or 2)."""
        return self._stage
    
    def handle_pressure_event(self, event: NSEvent) -> None:
        """
        Process a pressure event from the system.
        
        Args:
            event: NSEvent containing pressure data
        """
        try:
            pressure = event.pressure()
            # Don't call stage() - it causes assertion failures on many event types
            # Stage is not reliably available for all trackpad events
            stage = 0
            
            self._pressure = pressure
            self._stage = stage
            
            if self.callback:
                self.callback(pressure, stage)
                
        except Exception as e:
            print(f"Error processing pressure event: {e}", file=sys.stderr)
    
    def start(self, gui: bool = True) -> None:
        """
        Start monitoring pressure.
        
        Args:
            gui: If True, opens GUI window. If False, you must handle
                 events yourself (advanced usage).
        """
        if gui:
            from .gui import start_gui_monitor
            start_gui_monitor(self)
        else:
            raise NotImplementedError(
                "Non-GUI monitoring requires custom event loop setup. "
                "Use gui=True or implement your own event handling."
            )