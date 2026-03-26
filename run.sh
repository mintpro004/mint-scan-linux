#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║     MINT SCAN v7 — RUN SCRIPT                               ║
# ╚══════════════════════════════════════════════════════════════╝
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Basic health check: if venv is missing, run installer
if [ ! -d "venv" ]; then
    echo "[ MINT SCAN ] Virtual environment not found. Running installer..."
    bash install.sh
fi

# Activate venv and launch
source venv/bin/activate
exec python3 main.py
