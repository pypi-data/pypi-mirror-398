"""
Basic usage with a callback function to process pressure data.
"""

from trackpad_pressure import PressureMonitor

def on_pressure_change(pressure, stage):
    print(f"Pressure: {pressure:.3f}, Stage: {stage}")
    
    # Example: Trigger actions based on pressure
    if pressure > 0.8:
        print("  → Heavy pressure detected!")
    elif pressure > 0.4:
        print("  → Medium pressure")
    elif pressure > 0.1:
        print("  → Light touch")

if __name__ == "__main__":
    print("Starting pressure monitor with callback...")
    print("Press on your trackpad with varying pressure.")
    print("Press Ctrl+C to exit.\n")
    
    monitor = PressureMonitor(callback=on_pressure_change)
    monitor.start()