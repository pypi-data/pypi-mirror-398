"""
Collect pressure data for analysis or research.
Records timestamp, pressure, and stage for each event.
"""

import time
from trackpad_pressure import PressureMonitor

# Storage for collected data
data_points = []
start_time = time.time()

def collect_pressure_data(pressure, stage):
    """Store pressure data with timestamp."""
    timestamp = time.time() - start_time
    data_points.append({
        'timestamp': timestamp,
        'pressure': pressure,
        'stage': stage
    })
    
    # Print every 10th sample to avoid spam
    if len(data_points) % 10 == 0:
        print(f"Collected {len(data_points)} samples...")

if __name__ == "__main__":
    print("Collecting pressure data...")
    print("Press on trackpad to generate data.")
    print("Press Ctrl+C when done.\n")
    
    monitor = PressureMonitor(callback=collect_pressure_data)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print(f"\n\nCollection complete! Collected {len(data_points)} samples.")
        print("\nFirst 5 samples:")
        for sample in data_points[:5]:
            print(f"  t={sample['timestamp']:.2f}s: "
                  f"pressure={sample['pressure']:.3f}, "
                  f"stage={sample['stage']}")