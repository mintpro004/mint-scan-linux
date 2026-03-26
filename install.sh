#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║     MINT SCAN v7 — INSTALLER                                ║
# ║     github.com/mintpro004/mint-scan-linux                   ║
# ╚══════════════════════════════════════════════════════════════╝
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     MINT SCAN v7 — INSTALLER                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}[1/7] Fixing ownership...${NC}"
sudo chown -R "$USER:$USER" "$SCRIPT_DIR"
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[2/7] Installing system packages...${NC}"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip python3-tk python3-dev python3-venv \
    net-tools wireless-tools iw network-manager \
    nmap adb curl git dbus libnotify-bin sqlite3 xclip \
    tcpdump clamav clamav-daemon rkhunter ufw \
    auditd tshark usbguard || { echo -e "${RED}Failed to install system packages.${NC}"; exit 1; }
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[3/7] Setting up Python environment...${NC}"
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || { echo -e "${RED}Failed to install Python dependencies.${NC}"; exit 1; }
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[4/7] Configuring system permissions...${NC}"
# Add user to groups for network capture
sudo usermod -aG wireshark "$USER" 2>/dev/null || true
sudo usermod -aG pcap "$USER" 2>/dev/null || true

# Android udev rules
echo -e "${YELLOW}  Configuring Android USB rules...${NC}"
sudo wget -O /etc/udev/rules.d/51-android.rules https://raw.githubusercontent.com/M0Rf30/android-udev-rules/master/51-android.rules 2>/dev/null || \
sudo bash -c 'cat > /etc/udev/rules.d/51-android.rules << EOF
SUBSYSTEM=="usb", ATTR{idVendor}=="0502", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0b05", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="413c", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0489", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="091e", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0bb4", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="12d1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0ea0", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="054c", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0fce", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0411", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="201e", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="19d2", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0482", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="1004", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="22b8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04da", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="05c6", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="1ed9", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0471", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2340", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0955", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0x1199", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0x2a70", MODE="0666", GROUP="plugdev"
EOF'
sudo chmod a+r /etc/udev/rules.d/51-android.rules
sudo udevadm control --reload-rules
sudo usermod -aG plugdev "$USER" 2>/dev/null || true

# Set capabilities for tshark/dumpcap to allow non-root capture
if [ -f /usr/bin/dumpcap ]; then
    sudo setcap cap_net_raw,cap_net_admin+eip /usr/bin/dumpcap 2>/dev/null || true
fi

# ClamAV setup
sudo systemctl stop clamav-freshclam 2>/dev/null || true
sudo freshclam || echo -e "${YELLOW}  ! freshclam update failed, will retry later${NC}"
sudo systemctl start clamav-daemon 2>/dev/null || true
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[5/7] Verifying Python files...${NC}"
errors=0
for pyfile in *.py; do
    result=$(python3 -m py_compile "$pyfile" 2>&1)
    if [ -z "$result" ]; then
        echo -e "    ${GREEN}✓${NC} $pyfile"
    else
        echo -e "    ${RED}✗${NC} $pyfile — $result"
        errors=$((errors+1))
    fi
done
[ $errors -gt 0 ] && echo -e "  ${RED}WARNING: $errors file(s) have errors${NC}"

echo -e "${YELLOW}[6/7] Creating desktop shortcut...${NC}"
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/mint-scan.desktop << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Mint Scan
Comment=Advanced Security Auditor v7 — Mint Projects
Exec=bash $SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/icon.png
Terminal=false
Categories=Security;Network;System;
DESKTOP
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[7/7] Finalizing...${NC}"
chmod +x run.sh
echo -e "${GREEN}  ✓ Done${NC}"

echo ""
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   INSTALLATION COMPLETE                                     ║"
echo "║   Run:  bash run.sh                                         ║"
echo "║   Note: You may need to log out and back in for group       ║"
echo "║         changes (wireshark group) to take effect.           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
