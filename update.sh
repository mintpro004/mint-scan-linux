#!/bin/bash
# Mint Scan v7 — Updater with self-healing
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[ MINT SCAN ] Fixing ownership..."
sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true

echo "[ MINT SCAN ] Pulling latest from GitHub..."
if git pull origin main 2>&1; then
    echo "[ MINT SCAN ] Updated from GitHub"
else
    echo "[ MINT SCAN ] GitHub unreachable — running local self-heal"
fi

echo "[ MINT SCAN ] Running installer to apply all fixes..."
bash install.sh
