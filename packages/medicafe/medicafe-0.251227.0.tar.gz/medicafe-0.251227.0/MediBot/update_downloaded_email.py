#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Minimal CLI wrapper to update downloaded_emails.txt after manual file downloads.

This script reuses existing MediCafe utilities and the extracted add_downloaded_email()
function from MediLink_Gmail.py to maintain DRY principles.

Usage:
    python update_downloaded_email.py --config <config_path> --filename <filename> [--verify-path <path>]
"""

import os
import sys
import argparse

# Setup Python path to find MediCafe
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

# Use existing MediCafe utilities (same pattern as migrate_browser_downloads.py)
from MediCafe.core_utils import extract_medilink_config

# Import the extracted function from MediLink_Gmail
try:
    from MediLink.MediLink_Gmail import add_downloaded_email
except ImportError:
    # Fallback for direct import
    try:
        import MediLink.MediLink_Gmail as gmail_module
        add_downloaded_email = gmail_module.add_downloaded_email
    except ImportError:
        print("ERROR|Failed to import add_downloaded_email from MediLink_Gmail", file=sys.stderr)
        sys.exit(1)

def load_config(config_path):
    """Load configuration from JSON file (reusing pattern from migrate_browser_downloads.py)"""
    import json
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print("ERROR|Failed to load config: {}".format(str(e)), file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Update downloaded_emails.txt')
    parser.add_argument('--config', required=True, help='Path to config.json')
    parser.add_argument('--filename', required=True, help='Filename to add (just the name)')
    parser.add_argument('--verify-path', help='Optional: verify file exists at this path before updating')
    
    args = parser.parse_args()
    
    # Verify file exists at destination if verify-path provided
    if args.verify_path:
        if not os.path.exists(args.verify_path):
            print("WARNING|File does not exist at destination: {}".format(args.verify_path), file=sys.stderr)
            sys.exit(1)
    
    # Load config using existing pattern
    config = load_config(args.config)
    
    # Call the extracted function (reusing existing code)
    success = add_downloaded_email(args.filename, config=config, log_fn=None)
    
    if success:
        sys.exit(0)
    else:
        print("ERROR|Failed to update downloaded_emails.txt", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
