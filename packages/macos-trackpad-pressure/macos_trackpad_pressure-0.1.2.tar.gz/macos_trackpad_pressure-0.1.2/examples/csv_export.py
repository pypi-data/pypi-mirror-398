"""
Collect pressure data and export to CSV for analysis in Excel, R, Python, etc.
"""

import time
import signal
import sys

try:
    import pandas as pd
except ImportError:
    print("Error: This example requires pandas.")
    print("Install with: pip install pandas")
    sys.exit(1)

from trackpad_pressure import PressureMonitor

# Data storage
data = []
start_time = time.time()

def collect_data(pressure, stage):
    """Collect pressure data with timestamp."""
    data.append({
        'timestamp': time.time() - start_time,
        'pressure': pressure,
        'stage': stage
    })

def save_and_exit(signum, frame):
    """Save data to CSV and exit."""
    print(f"\n\nSaving {len(data)} samples to CSV...")
    
    if data:
        df = pd.DataFrame(data)
        filename = f'pressure_data_{int(time.time())}.csv'
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        
        # Print basic statistics
        print("\nStatistics:")
        print(df['pressure'].describe())
    else:
        print("No data collected.")
    
    sys.exit(0)

if __name__ == "__main__":
    print("Collecting pressure data for CSV export...")
    print("Press on trackpad to generate data.")
    print("Press Ctrl+C to save and exit.\n")
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, save_and_exit)
    
    monitor = PressureMonitor(callback=collect_data)
    monitor.start()