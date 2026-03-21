#!/bin/bash
# Mint Scan v6 — Updater
# Pulls latest version from github.com/mintpro004/mint-scan-linux

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}[ MINT SCAN UPDATER ]${NC}"
echo -e "${YELLOW}Pulling latest from GitHub...${NC}"

git pull origin main

if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Updating Python packages...${NC}"
    source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Update complete. Run: ./run.sh${NC}"
else
    echo -e "\033[0;31m✗ Update failed. Check your internet connection.${NC}"
fi
