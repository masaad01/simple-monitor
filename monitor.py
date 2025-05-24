#!/usr/bin/env python3
import json
import os
import signal
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import psutil
from dotenv import load_dotenv

# Load configuration from .env
load_dotenv()
PORT = int(os.getenv("PORT", 5000))
BIND_IPS = os.getenv("BIND_IPS", "127.0.0.1,172.17.0.1").split(",")
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 85))
MEM_THRESHOLD = float(os.getenv("MEM_THRESHOLD", 90))
DISK_THRESHOLD = float(os.getenv("DISK_THRESHOLD", 90))
TOKEN = os.getenv("MONITOR_TOKEN") or exit("Error: MONITOR_TOKEN not set in .env")

servers = []  # Will hold HTTPServer instances


def get_metrics():
    """Return current CPU, memory, and disk usage percentages."""
    return (
        psutil.cpu_percent(interval=1),
        psutil.virtual_memory().percent,
        psutil.disk_usage("/").percent,
    )


class MonitorHandler(BaseHTTPRequestHandler):
    def authenticate(self):
        token = (
            self.headers.get("X-Auth-Token")
            or parse_qs(urlparse(self.path).query).get("token", [None])[0]
        )
        return token == TOKEN

    def send_json(self, payload: dict, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        if not self.authenticate():
            return self.send_json({"error": "unauthorized"}, status_code=401)

        cpu, mem, disk = get_metrics()
        path = urlparse(self.path).path

        if path == "/health":
            payload = {"cpu": cpu, "memory": mem, "disk": disk}
            unhealthy = cpu > CPU_THRESHOLD or mem > MEM_THRESHOLD or disk > DISK_THRESHOLD
            payload["status"] = "unhealthy" if unhealthy else "healthy"
            return self.send_json(payload, status_code=500 if unhealthy else 200)

        self.send_response(404)
        self.end_headers()


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
