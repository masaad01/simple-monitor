import sys

import matplotlib.pyplot as plt
import pandas as pd

# 0. Check if filename is provided
if len(sys.argv) < 2:
    print("Usage: python plot.py <filename>")
    sys.exit(1)

# 1. Read the filename from CLI
filename = sys.argv[1]

# 2. Read the data
df = pd.read_csv(filename, parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)

# 3. Plot CPU, Memory, Disk over time
plt.figure(figsize=(12, 6))
df[["cpu", "memory", "disk"]].plot(ax=plt.gca(), title="System Metrics Over Time", linewidth=2)
plt.xlabel("Time")
plt.ylabel("Usage (%)")
plt.grid(True)
plt.legend(title="Metric")
plt.tight_layout()

# Optional: format date on x-axis for clarity
plt.gcf().autofmt_xdate()

plt.show()
