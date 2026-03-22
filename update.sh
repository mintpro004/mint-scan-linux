#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\033[0;36m[ MINT SCAN ]\033[0m Fixing ownership..."
sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true

echo -e "\033[0;36m[ MINT SCAN ]\033[0m Pulling updates from GitHub..."

# Check if we are in a git repo
if [ -d ".git" ]; then
    # Stash local changes (like our fixes) so pull can proceed
    STASHED=false
    if [[ $(git status --porcelain) ]]; then
        echo -e "\033[0;33m[ MINT SCAN ]\033[0m Saving local fixes..."
        git stash -u > /dev/null
        STASHED=true
    fi

    if git pull origin main; then
        echo -e "\033[0;32m[ MINT SCAN ]\033[0m Pull successful."
    else
        echo -e "\033[0;31m[ MINT SCAN ]\033[0m Pull failed. Checking connectivity..."
    fi

    # Bring back our fixes
    if [ "$STASHED" = true ]; then
        echo -e "\033[0;33m[ MINT SCAN ]\033[0m Re-applying local fixes..."
        git stash pop > /dev/null || echo -e "\033[0;31m[ MINT SCAN ]\033[0m Note: Conflicts occurred during re-application."
    fi
else
    echo -e "\033[0;31m[ MINT SCAN ]\033[0m Not a git repository. Skipping pull."
fi

echo -e "\033[0;36m[ MINT SCAN ]\033[0m Running self-healing installer..."
bash install.sh
