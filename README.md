# Simple Server Resource Monitor

A lightweight Python-based HTTP health-check service that reports CPU, memory, and disk usage. Also logs metrics to a CSV file for historical analysis and visualization. Designed for integration with [Uptime Kuma](https://github.com/louislam/uptime-kuma) (via HTTP JSON Query) and managed as a systemd service.

---

## 📂 Project Structure

```
/opt/simple-monitor/
├── monitor.py               # Main Python script
├── .env                     # Environment configuration
├── venv/                    # Python virtual environment
├── simple-monitor.service   # systemd unit file
├── install.sh               # Automated installer
├── metrics.csv              # CSV log of resource metrics
└── README.md                # This file
```

---

## ⚙️ Prerequisites

- **Linux server** with `systemd`
- **Python 3.6+** and `python3-venv`
- `pip + venv` (for dependency installation)
- `sudo` or **root** privileges

---

## 🛠️ Installation

1. **Clone or copy** all files to a local directory on your server.
2. **Make the installer executable**:

   ```bash
   chmod +x install.sh
   ```

3. **Run the installer** as root (or via `sudo`):

   ```bash
   sudo ./install.sh
   ```

   This will:

   - Create `/opt/simple-monitor/`
   - Copy over `monitor.py`, `.env`, and the service file
   - Create a Python virtual environment and install `psutil` & `python-dotenv`
   - Enable and start the `simple-monitor` systemd service

4. **Verify** that the service is running:

   ```bash
   sudo systemctl status simple-monitor.service
   journalctl -u simple-monitor.service -f
   ```

---

## 🔧 Configuration

Edit `/opt/simple-monitor/.env` to set your preferred values:

```ini
# /opt/simple-monitor/.env

# Authentication token (required)
MONITOR_TOKEN=your-strong-token

# Listening port
MONITOR_PORT=5000

# Comma-separated IPs to bind (e.g. localhost and Docker bridge)
MONITOR_BIND_IPS=127.0.0.1,172.17.0.1

# Thresholds (percentages)
CPU_THRESHOLD=85
MEM_THRESHOLD=90
DISK_THRESHOLD=90

# CSV log file path (optional)
CSV_FILE=metrics.csv
```

After changing `.env`, reload the service:

```bash
sudo systemctl restart simple-monitor.service
```

---

## 🚪 API Endpoints

All endpoints require authentication via either:

- **Header**: `X-Auth-Token: <MONITOR_TOKEN>`
- **Query**: `?token=<MONITOR_TOKEN>`

### `/health`

- **Success (200)**

  ```json
  {
    "status": "healthy",
    "cpu": 27.3,
    "memory": 41.2,
    "disk": 67.9
  }
  ```

- **Failure (500)** when any metric exceeds its threshold:

  ```json
  {
    "status": "unhealthy",
    "cpu": 92.1,
    "memory": 88.0,
    "disk": 67.9
  }
  ```

Example:

```bash
curl -H "X-Auth-Token: your-strong-token" http://127.0.0.1:5000/health
```

---

## 📈 Logging and Visualization

Metrics are logged to a CSV file (`metrics.csv` by default).

To visualize the data:

1. **Spreadsheet Visualization**
   Open the CSV file (e.g., `metrics.csv`) in Google Sheets, Excel, or any spreadsheet software. You can easily create line charts or graphs using the data.

2. **Python Visualization**
   Use the provided `plot.py` script to generate a visualization of system metrics:

   - First, make sure you have the required Python libraries installed:

     ```bash
     pip install pandas matplotlib
     ```

   - Then, run the script with the CSV filename as an argument:

     ```bash
     python3 plot.py metrics.csv
     ```

3. **Example Output**

   _Here’s an example output chart:_

---

## 📈 Integrating with Uptime Kuma

- In Uptime Kuma, **Add New Monitor**

  - **Type**: HTTP(s)
  - **URL**: `http://172.17.0.1:5000/health`
  - **Headers**:

    ```
    X-Auth-Token: your-strong-token
    ```

---

## 🔄 Updates & Uninstallation

- To **update** the script or service file, replace the files in `/opt/simple-monitor/` and then:

  ```bash
  sudo systemctl daemon-reload
  sudo systemctl restart simple-monitor.service
  ```

- To **uninstall**:

  ```bash
  sudo systemctl stop simple-monitor.service
  sudo systemctl disable simple-monitor.service
  sudo rm /etc/systemd/system/simple-monitor.service
  sudo rm -rf /opt/simple-monitor
  sudo systemctl daemon-reload
  ```

---

## 🛡️ Security Tips

- Use a **strong**, unguessable `MONITOR_TOKEN`.
- Bind only to necessary interfaces (e.g. localhost or Docker bridge).

---
