#!/usr/bin/env python3
"""
Mint Scan v6 — Linux Desktop Security Auditor
by Mint Projects, Pretoria
"""
import sys
import os

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import MintScanApp

if __name__ == '__main__':
    app = MintScanApp()
    app.run()
