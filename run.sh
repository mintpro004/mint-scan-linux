#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║   MINT SCAN v8 — LAUNCHER                                   ║
# ╚══════════════════════════════════════════════════════════════╝
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

# Self-heal check: widgets broken or venv missing
HEAL=false
[ ! -d "venv" ] && HEAL=true
python3 -m py_compile widgets.py 2>/dev/null || HEAL=true
grep -q "class Btn" widgets.py 2>/dev/null || HEAL=true
grep -q "def __str__" widgets.py 2>/dev/null && HEAL=true

if [ "$HEAL" = true ]; then
    echo -e "${CYAN}[ MINT SCAN ]${NC} Self-healing — running installer..."
    sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true
    bash install.sh
fi

# Activate venv
source venv/bin/activate 2>/dev/null || {
    echo -e "${RED}[ MINT SCAN ]${NC} venv broken — reinstalling..."
    bash install.sh
    source venv/bin/activate
}

echo -e "${GREEN}[ MINT SCAN ]${NC} Launching v7..."
exec python3 main.py
