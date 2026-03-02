#!/usr/bin/env bash
# ============================================================
# Run this locally to push changes and trigger a remote deploy.
# Usage: bash deploy/push_and_deploy.sh
# ============================================================
set -euo pipefail

SSH_KEY="${SSH_KEY:-$HOME/.ssh/fisheye_rsa}"
DROPLET="root@143.198.110.70"
APP_DIR="/opt/cbr-chatbot"

echo "==> Pushing to GitHub..."
git push

echo "==> Deploying to droplet..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$DROPLET" \
    "bash $APP_DIR/deploy/deploy.sh"

echo "==> Deployed! Visit: http://143.198.110.70"
