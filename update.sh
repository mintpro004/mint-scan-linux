#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
git pull origin main
source venv/bin/activate 2>/dev/null || true
pip install -q -r requirements.txt
echo "✓ Updated — run: bash run.sh"
