#!/usr/bin/env python3
import csv
import json
import os
import signal
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import psutil
from dotenv import load_dotenv

# ─── Configuration ────────────────────────────────────────────────────────────

load_dotenv()
PORT = int(os.getenv("PORT", 5000))
BIND_IPS = os.getenv("BIND_IPS", "127.0.0.1,172.17.0.1").split(",")
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 85))
MEM_THRESHOLD = float(os.getenv("MEM_THRESHOLD", 90))
DISK_THRESHOLD = float(os.getenv("DISK_THRESHOLD", 90))
NET_IFACE = os.getenv("NET_IFACE", "eth0")
STATE_FILE = os.getenv("NET_STATE_FILE", "net_state.json")
TOKEN = os.getenv("MONITOR_TOKEN") or exit("Error: MONITOR_TOKEN not set in .env")
CSV_FILE = os.getenv("CSV_FILE", "metrics.csv")

# ─── CSV Header Setup ─────────────────────────────────────────────────────────

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "cpu_pct",
                "mem_pct",
                "disk_pct",
                "load1",
                "load5",
                "load15",
                "net_sent_kbps",
                "net_recv_kbps",
                "month_sent_mb",
                "month_recv_mb",
                "status",
            ]
        )

# ─── Monthly Network State Helpers ────────────────────────────────────────────


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    ctrs = psutil.net_io_counters(pernic=True).get(NET_IFACE)
    if ctrs is None:
        raise ValueError(f"Interface '{NET_IFACE}' not found")
    month = datetime.utcnow().strftime("%Y-%m")
    return {
        "month": month,
        "last_sent": ctrs.bytes_sent,
        "last_recv": ctrs.bytes_recv,
        "accum_sent": 0,
        "accum_recv": 0,
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_monthly_net():
    """
    Returns:
      sent_delta_bytes, recv_delta_bytes,
      accum_sent_bytes, accum_recv_bytes
    and updates STATE_FILE to roll over on month boundary.
    """
    state = load_state()
    now = datetime.utcnow()
    cur_month = now.strftime("%Y-%m")

    # Reset on new month
    if state["month"] != cur_month:
        state = {
            "month": cur_month,
            "last_sent": 0,
            "last_recv": 0,
            "accum_sent": 0,
            "accum_recv": 0,
        }

    ctrs = psutil.net_io_counters(pernic=True).get(NET_IFACE)
    if ctrs is None:
        raise ValueError(f"Interface '{NET_IFACE}' not found")

    # Use previous reading if nonzero, else bootstrap
    last_s = state["last_sent"] or ctrs.bytes_sent
    last_r = state["last_recv"] or ctrs.bytes_recv

    sent_delta = ctrs.bytes_sent - last_s
    recv_delta = ctrs.bytes_recv - last_r

    if sent_delta > 0:
        state["accum_sent"] += sent_delta
    if recv_delta > 0:
        state["accum_recv"] += recv_delta

    state["last_sent"] = ctrs.bytes_sent
    state["last_recv"] = ctrs.bytes_recv

    save_state(state)
    return sent_delta, recv_delta, state["accum_sent"], state["accum_recv"]


# ─── Metrics Gathering ────────────────────────────────────────────────────────


def get_metrics():
    # 1) Instant net I/O KB/s over 1 s interval
    net_before = psutil.net_io_counters(pernic=True).get(NET_IFACE)
    if net_before is None:
        raise ValueError(f"Interface '{NET_IFACE}' not found")

    cpu = psutil.cpu_percent(interval=1)

    net_after = psutil.net_io_counters(pernic=True)[NET_IFACE]
    sent_kbps = (net_after.bytes_sent - net_before.bytes_sent) / 1024.0
    recv_kbps = (net_after.bytes_recv - net_before.bytes_recv) / 1024.0

    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    load1, load5, load15 = os.getloadavg()

    # 2) Monthly deltas & accumulators
    sent_delta, recv_delta, accum_sent, accum_recv = get_monthly_net()

    # Convert accumulators to MB
    month_sent_mb = accum_sent / (1024**2)
    month_recv_mb = accum_recv / (1024**2)

    return {
        "cpu_pct": round(cpu, 1),
        "memory_pct": round(mem, 1),
        "disk_pct": round(disk, 1),
        "load_avg": {
            "1m": round(load1, 2),
            "5m": round(load5, 2),
            "15m": round(load15, 2),
        },
        "net_kbps": {
            "sent": round(sent_kbps, 1),
            "recv": round(recv_kbps, 1),
        },
        "net_monthly_mb": {
            "sent": round(month_sent_mb, 2),
            "recv": round(month_recv_mb, 2),
        },
    }


def log_csv_row(metrics, status):
    ts = datetime.utcnow().isoformat()
    row = [
        ts,
        metrics["cpu_pct"],
        metrics["memory_pct"],
        metrics["disk_pct"],
        metrics["load_avg"]["1m"],
        metrics["load_avg"]["5m"],
        metrics["load_avg"]["15m"],
        metrics["net_kbps"]["sent"],
        metrics["net_kbps"]["recv"],
        metrics["net_monthly_mb"]["sent"],
        metrics["net_monthly_mb"]["recv"],
        status,
    ]
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


# ─── HTTP Server Handler ──────────────────────────────────────────────────────

servers = []


class MonitorHandler(BaseHTTPRequestHandler):
    def authenticate(self):
        token = (
            self.headers.get("X-Auth-Token")
            or parse_qs(urlparse(self.path).query).get("token", [None])[0]
        )
        return token == TOKEN

    def send_json(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.authenticate():
            return self.send_json({"error": "unauthorized"}, code=401)

        if urlparse(self.path).path != "/health":
            self.send_response(404)
            return self.end_headers()

        try:
            metrics = get_metrics()
        except Exception as e:
            return self.send_json({"error": str(e)}, code=500)

        unhealthy = (
            metrics["cpu_pct"] > CPU_THRESHOLD
            or metrics["memory_pct"] > MEM_THRESHOLD
            or metrics["disk_pct"] > DISK_THRESHOLD
        )
        status = "unhealthy" if unhealthy else "healthy"

        log_csv_row(metrics, status)
        return self.send_json({**metrics, "status": status}, code=(500 if unhealthy else 200))


# ─── Server Bootstrap & Shutdown ──────────────────────────────────────────────


def run_server(host: str):
    httpd = HTTPServer((host, PORT), MonitorHandler)
    servers.append(httpd)
    print(f"[monitor] Listening on http://{host}:{PORT}")
    httpd.serve_forever()


def shutdown(sig, frame):
    print("[monitor] Shutting down...")
    for srv in servers:
        srv.shutdown()
    exit(0)


if __name__ == "__main__":
    # Handle Ctrl+C and termination signals
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start servers on configured interfaces
    for ip in BIND_IPS:
        t = threading.Thread(target=run_server, args=(ip,), daemon=True)
        t.start()

    # Block until signals
    signal.pause()
