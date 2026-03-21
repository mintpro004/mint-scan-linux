#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Self-heal: if widgets broken, reinstall first
if ! python3 -m py_compile widgets.py 2>/dev/null || \
   ! grep -q "class Btn" widgets.py 2>/dev/null || \
   grep -q "def __str__" widgets.py 2>/dev/null; then
    echo "[ MINT SCAN ] Detected broken widgets.py — self-healing..."
    sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true
    bash install.sh
fi

[ ! -d "venv" ] && bash install.sh
source venv/bin/activate
exec python3 main.py
