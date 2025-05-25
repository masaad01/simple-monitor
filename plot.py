#!/usr/bin/env python3

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

# 3. Create a 2×2 grid of subplots, sharing the x-axis
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(15, 12), sharex=True)
axes_flat = axes.flatten()

# Define (cols, title, y-label, legend title)
plot_defs = [
    (["cpu_pct", "mem_pct", "disk_pct"], "System Metrics", "Usage (%)", "Metric"),
    (["load1", "load5", "load15"], "Load Averages", "Load Avg", "Interval"),
    (["net_sent_kbps", "net_recv_kbps"], "Network Throughput (KB/s)", "KB/s", "Direction"),
    (["month_sent_mb", "month_recv_mb"], "Monthly Cumulative Net (MB)", "MB", "Direction"),
]

for ax, (cols, title, ylabel, legend_title) in zip(axes_flat, plot_defs):
    df[cols].plot(ax=ax, linewidth=2)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.legend(title=legend_title)

# Only label the bottom row with “Time”
for ax in axes_flat[2:]:
    ax.set_xlabel("Time")

# Tidy up
fig.autofmt_xdate(rotation=30, ha="right")
fig.tight_layout(h_pad=3, w_pad=2)

plt.show()
