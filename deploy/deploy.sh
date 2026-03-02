#!/usr/bin/env bash
# ============================================================
# Re-deploy script — runs ON the droplet to update the app.
# Usage: bash /opt/cbr-chatbot/deploy/deploy.sh
# ============================================================
set -euo pipefail

APP_DIR="/opt/cbr-chatbot"

echo "==> Pulling latest code..."
git -C "$APP_DIR" pull

echo "==> Installing/updating Python dependencies..."
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

echo "==> Restarting service..."
systemctl restart cbr-chatbot
systemctl status cbr-chatbot --no-pager

echo "==> Done. App is live at http://143.198.110.70"
