#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "[ MINT SCAN ] Fixing ownership..."
sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true
echo "[ MINT SCAN ] Pulling from GitHub..."
git pull origin main 2>&1 || echo "[ MINT SCAN ] Git unavailable — running local heal"
echo "[ MINT SCAN ] Running installer..."
bash install.sh
