#!/usr/bin/env bash
# ============================================================
# ONE-TIME server setup for CBR chatbot on Ubuntu droplet
# Run as: bash deploy/setup.sh
# ============================================================
set -euo pipefail

REPO_URL="https://github.com/gpad1234/Customer-Chatbot-CBR.git"
APP_DIR="/opt/cbr-chatbot"
PYTHON="python3.11"

echo "==> Updating packages..."
apt-get update -q
apt-get install -y -q python3.11 python3.11-venv python3-pip git nginx curl

echo "==> Cloning repository to $APP_DIR..."
if [ -d "$APP_DIR/.git" ]; then
    echo "    Repo already cloned, pulling latest..."
    git -C "$APP_DIR" pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi

echo "==> Creating Python virtual environment..."
$PYTHON -m venv "$APP_DIR/.venv"

echo "==> Installing Python dependencies..."
"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

echo "==> Downloading spaCy model (en_core_web_md)..."
"$APP_DIR/.venv/bin/python" -m spacy download en_core_web_md

echo "==> Creating data directory..."
mkdir -p "$APP_DIR/data"

echo "==> Installing systemd service..."
cp "$APP_DIR/deploy/cbr-chatbot.service" /etc/systemd/system/cbr-chatbot.service
systemctl daemon-reload
systemctl enable cbr-chatbot
systemctl start cbr-chatbot

echo "==> Configuring nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/cbr-chatbot
ln -sf /etc/nginx/sites-available/cbr-chatbot /etc/nginx/sites-enabled/cbr-chatbot
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo "======================================================"
echo " Setup complete!"
echo " App:   http://143.198.110.70"
echo " Logs:  journalctl -u cbr-chatbot -f"
echo ""
echo " IMPORTANT: Copy your .env file to $APP_DIR/.env"
echo "   e.g.:  scp -i ~/.ssh/fisheye_rsa .env root@143.198.110.70:$APP_DIR/.env"
echo "   Then:  systemctl restart cbr-chatbot"
echo "======================================================"
