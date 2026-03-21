#!/bin/bash
# Mint Scan v7 — Launcher with self-healing check
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Quick self-heal: if widgets.py is broken, fix ownership and reinstall
if [ ! -f "venv/bin/activate" ] || ! python3 -m py_compile widgets.py 2>/dev/null || ! grep -q "class Btn" widgets.py; then
    echo "[ MINT SCAN ] Detecting issue — running self-heal..."
    sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true
    bash install.sh
    exit $?
fi

source venv/bin/activate
exec python3 main.py
