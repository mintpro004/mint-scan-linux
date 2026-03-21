#!/bin/bash
# Mint Scan v6 — Linux Installer
# GitHub: https://github.com/mintpro004/mint-scan-linux
# by Mint Projects, Pretoria

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║        MINT SCAN v6  INSTALLER           ║"
echo "║    Advanced Linux Security Auditor       ║"
echo "║    github.com/mintpro004                 ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}[1/5] Updating package list...${NC}"
sudo apt-get update -qq

echo -e "${YELLOW}[2/5] Installing system dependencies...${NC}"
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-tk \
    python3-dev \
    python3-venv \
    net-tools \
    wireless-tools \
    iw \
    network-manager \
    nmap \
    curl \
    git \
    dbus \
    libdbus-1-dev \
    libnotify-bin \
    sqlite3 \
    2>/dev/null || true

echo -e "${YELLOW}[3/5] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[4/5] Installing Python packages...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${YELLOW}[5/5] Setting up launcher and desktop entry...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

chmod +x run.sh

# Desktop shortcut
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/mint-scan.desktop << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Mint Scan
Comment=Advanced Security Auditor by Mint Projects
Exec=$SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
Categories=Security;Network;System;
Keywords=security;network;wifi;scan;ports;
StartupWMClass=mint-scan
DESKTOP

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║         INSTALLATION COMPLETE!           ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║  Launch:    ./run.sh                     ║"
echo "║  Or find 'Mint Scan' in your app menu    ║"
echo "║                                          ║"
echo "║  GitHub: github.com/mintpro004            ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
