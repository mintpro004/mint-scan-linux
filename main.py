#!/usr/bin/env python3
"""
Mint Scan v7 — Entry Point
Loads saved theme before window opens, then launches app.
"""
import sys, os

# Add this directory to path first
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# Apply saved theme BEFORE importing ctk or creating window
def _load_and_apply_theme():
    import json
    settings_file = os.path.expanduser('~/.mint_scan_settings.json')
    theme = 'dark'
    try:
        with open(settings_file) as f:
            d = json.load(f)
            theme = d.get('theme', 'dark')
    except Exception:
        pass
    # Apply to widgets module colour dict
    try:
        import widgets as _w
        _w.apply_theme(theme)
    except Exception:
        pass

_load_and_apply_theme()

from app import MintScanApp

if __name__ == '__main__':
    app = MintScanApp()
    app.run()
