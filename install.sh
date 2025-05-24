#!/usr/bin/env bash
set -euo pipefail

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="/opt/simple-monitor"
SERVICE_FILE="simple-monitor.service"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_FILE}"

echo "➡️  Installing Simple Monitor to ${DEST_DIR}"

# 1. Create destination directory
mkdir -p "${DEST_DIR}"
chown root:root "${DEST_DIR}"
chmod 755 "${DEST_DIR}"

# 2. Copy files
echo "   • Copying monitor.py and .env and creating metrics.csv"
cp "${SCRIPT_DIR}/monitor.py" "${DEST_DIR}/"
cp "${SCRIPT_DIR}/.env" "${DEST_DIR}/"
echo "timestamp,cpu,memory,disk,status" >"${DEST_DIR}/metrics.csv"

chmod 666 "${DEST_DIR}/metrics.csv"
chmod 755 "${DEST_DIR}/monitor.py"
chmod 644 "${DEST_DIR}/.env"

echo "   • Copying systemd unit"
cp "${SCRIPT_DIR}/${SERVICE_FILE}" "${SYSTEMD_PATH}"
chmod 644 "${SYSTEMD_PATH}"

# 3. Create and populate virtual environment
echo "   • Setting up Python venv"
python3 -m venv "${DEST_DIR}/venv"
# shellcheck disable=SC1091
source "${DEST_DIR}/venv/bin/activate"
pip install --upgrade pip
pip install psutil python-dotenv
deactivate

# 4. Reload & enable systemd service
echo "➡️  Enabling and starting systemd service"
systemctl daemon-reload
systemctl enable simple-monitor.service
systemctl restart simple-monitor.service

echo "✅ Installation complete!"
echo "   • Logs: journalctl -u simple-monitor.service -f"
