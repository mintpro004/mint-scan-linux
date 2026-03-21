#!/usr/bin/env python3
"""
Mint Scan v6 — Linux Desktop Security Auditor
by Mint Projects, Pretoria
github.com/mintpro004
"""
import sys
import os

# Add current directory to path so all modules resolve flat
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from app import MintScanApp

if __name__ == '__main__':
    app = MintScanApp()
    app.run()
