#!/bin/bash
# Mint Scan v6 — Installer
# github.com/mintpro004/mint-scan-linux

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║        MINT SCAN v6  INSTALLER           ║"
echo "║    Advanced Linux Security Auditor       ║"
echo "║    github.com/mintpro004                 ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}[1/4] Installing system packages...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-tk python3-dev python3-venv \
    net-tools wireless-tools iw network-manager \
    nmap curl git dbus libnotify-bin sqlite3 \
    2>/dev/null || true

echo -e "${YELLOW}[2/4] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[3/4] Installing Python packages...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${YELLOW}[4/4] Creating desktop shortcut...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/mint-scan.desktop << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Mint Scan
Comment=Security Auditor by Mint Projects
Exec=bash $SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/icon.png
Terminal=false
Categories=Security;Network;System;
DESKTOP

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║       INSTALLATION COMPLETE!             ║"
echo "║  Run:   bash run.sh                      ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
