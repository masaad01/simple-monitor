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
df[["cpu_pct", "memory_pct", "disk_pct"]].plot(
    ax=plt.gca(), title="System Metrics Over Time", linewidth=2
)
plt.xlabel("Time")
plt.ylabel("Usage (%)")
plt.grid(True)
plt.legend(title="Metric")
plt.tight_layout()
plt.gcf().autofmt_xdate()
plt.show()

# 4. Plot Load Averages over time
plt.figure(figsize=(12, 6))
df[["load1", "load5", "load15"]].plot(ax=plt.gca(), title="Load Averages Over Time", linewidth=2)
plt.xlabel("Time")
plt.ylabel("Load Average")
plt.grid(True)
plt.legend(title="Load Interval")
plt.tight_layout()
plt.gcf().autofmt_xdate()
plt.show()

# 5. Plot Instantaneous Network Throughput over time
plt.figure(figsize=(12, 6))
df[["net_sent_kbps", "net_recv_kbps"]].plot(
    ax=plt.gca(), title="Network Throughput (KB/s) Over Time", linewidth=2
)
plt.xlabel("Time")
plt.ylabel("KB/s")
plt.grid(True)
plt.legend(title="Direction")
plt.tight_layout()
plt.gcf().autofmt_xdate()
plt.show()

# 6. Plot Monthly Cumulative Network Usage over time
plt.figure(figsize=(12, 6))
df[["month_sent_mb", "month_recv_mb"]].plot(
    ax=plt.gca(), title="Monthly Cumulative Network Usage (MB)", linewidth=2
)
plt.xlabel("Time")
plt.ylabel("MB")
plt.grid(True)
plt.legend(title="Month To Date")
plt.tight_layout()
plt.gcf().autofmt_xdate()
plt.show()
