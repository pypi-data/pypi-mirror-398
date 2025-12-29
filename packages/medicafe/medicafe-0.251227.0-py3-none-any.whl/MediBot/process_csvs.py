#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediBot CSV Processor

This script processes CSV files from the download folder, moves them to the target folder
with timestamp renaming, updates the config file, and builds the deductible cache.

Operations:
- Moves CSV files from local_storage_path to source_folder
- Finds most recent CSV file in source_folder
- Validates/compares with config file's current CSV path
- Moves CSV to target folder with timestamp rename (SX_CSV_<timestamp>.csv)
- Updates config JSON with new CSV path
- Updates downloaded_emails.txt with original filename
- Builds deductible cache

Use --silent flag to suppress non-error output.
"""

import os
import sys
import json
import argparse
import shutil
import glob
from datetime import datetime

# Setup Python path to find MediCafe
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from MediCafe.core_utils import get_shared_config_loader

# Import required functions directly (no subprocess calls needed)
try:
    from MediBot.update_json import get_current_csv_path, update_csv_path
    HAS_UPDATE_JSON = True
except ImportError:
    HAS_UPDATE_JSON = False

try:
    from MediLink.MediLink_Gmail import add_downloaded_email
    HAS_ADD_DOWNLOADED_EMAIL = True
except ImportError:
    HAS_ADD_DOWNLOADED_EMAIL = False

try:
    from MediBot.build_deductible_cache import build_deductible_cache
    HAS_BUILD_CACHE = True
except ImportError:
    HAS_BUILD_CACHE = False

# Setup logging
try:
    LOGGER = get_shared_config_loader()
except Exception:
    LOGGER = None

def _log(message, level="INFO"):
    """Log message using shared config loader if available."""
    try:
        if LOGGER and hasattr(LOGGER, "log"):
            LOGGER.log(message, level=level)
    except Exception:
        pass

def load_config(config_path):
    """Load configuration from JSON file"""
    try:
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(config_path)
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print("ERROR|Failed to load config: {}".format(str(e)), file=sys.stderr)
        _log("Failed to load config: {}".format(str(e)), level="ERROR")
        sys.exit(1)

def validate_paths(source_folder, target_folder, config_file, local_storage_path=None):
    """Validate all required paths exist."""
    errors = []
    
    if not os.path.exists(source_folder):
        errors.append("Source folder does not exist: {}".format(source_folder))
    
    if not os.path.exists(target_folder):
        errors.append("Target folder does not exist: {}".format(target_folder))
    
    if not os.path.exists(config_file):
        errors.append("Config file does not exist: {}".format(config_file))
    
    if local_storage_path and not os.path.exists(local_storage_path):
        # Local storage path is optional - just warn
        print("[WARNING] Local storage path does not exist: {}".format(local_storage_path), file=sys.stderr)
        _log("Local storage path does not exist: {}".format(local_storage_path), level="WARNING")
    
    if errors:
        for error in errors:
            print("ERROR|{}".format(error), file=sys.stderr)
            _log(error, level="ERROR")
        sys.exit(1)

def move_csvs_from_storage(local_storage_path, source_folder, silent=False):
    """Move CSV files from local_storage_path to source_folder."""
    if not local_storage_path or not os.path.exists(local_storage_path):
        _log("Local storage path {} does not exist - skipping initial scan".format(local_storage_path), level="DEBUG")
        return 0
    
    # Scan for both CSV and DOCX files to provide better visibility in logs
    csv_pattern = os.path.join(local_storage_path, "*.csv")
    docx_pattern = os.path.join(local_storage_path, "*.docx")
    
    csv_files = glob.glob(csv_pattern)
    docx_files = glob.glob(docx_pattern)
    
    total_detected = len(csv_files) + len(docx_files)
    
    if not silent:
        print("Scanning local storage: {}".format(local_storage_path))
    
    _log("Local storage scan: Found {} file(s) ({} CSV, {} DOCX) in {}".format(
        total_detected, len(csv_files), len(docx_files), local_storage_path), level="INFO")
    
    if not csv_files:
        _log("No CSV files found in local storage to move", level="DEBUG")
        return 0
    
    if not silent:
        print("Moving {} new CSV file(s) to source folder...".format(len(csv_files)))
    
    moved_count = 0
    for csv_file in csv_files:
        try:
            filename = os.path.basename(csv_file)
            dest_path = os.path.join(source_folder, filename)
            
            if not silent:
                print("  -> Moving {} ...".format(filename))
            
            shutil.move(csv_file, dest_path)
            moved_count += 1
            _log("Moved CSV from local storage to source: {}".format(filename), level="DEBUG")
        except Exception as e:
            print("[WARNING] Failed to move CSV file {}: {}".format(csv_file, str(e)), file=sys.stderr)
            _log("Failed to move CSV file {}: {}".format(csv_file, str(e)), level="WARNING")
    
    _log("Successfully moved {} CSV file(s) from local storage to {}".format(moved_count, source_folder), level="INFO")
    return moved_count

def find_latest_csv(source_folder):
    """Find most recent CSV file by modification time. Returns (filename, filepath) or (None, None)."""
    csv_pattern = os.path.join(source_folder, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        return (None, None)
    
    # Find most recent by modification time
    latest_file = max(csv_files, key=os.path.getmtime)
    filename = os.path.basename(latest_file)
    
    return (filename, latest_file)

def compare_csv_with_config(latest_csv_path, config_file, target_folder, silent=False):
    """Compare latest CSV with config. Prompt to update if different (non-silent)."""
    if not HAS_UPDATE_JSON:
        return False
    
    try:
        current_csv_path = get_current_csv_path(config_file)
        if not current_csv_path:
            # No CSV path in config yet
            return False
        
        # Compare filenames only (not full paths)
        current_csv_name = os.path.basename(current_csv_path)
        latest_csv_name = os.path.basename(latest_csv_path)
        
        if current_csv_name == latest_csv_name:
            return False  # Same file, no update needed
        
        # Different CSV - prompt user (non-silent mode only)
        if not silent:
            print("Current CSV: {}".format(current_csv_name))
            print("Latest CSV: {}".format(latest_csv_name))
            
            while True:
                update_choice = input("Update config to latest CSV? (Y/N): ").strip().upper()
                if update_choice in ('Y', 'N'):
                    break
                print("Please enter Y or N")
            
            if update_choice == 'Y':
                # Update config with path to latest CSV in target folder (before rename)
                latest_csv_in_target = os.path.join(target_folder, latest_csv_name)
                update_csv_path(config_file, latest_csv_in_target)
                _log("Updated config to latest CSV: {}".format(latest_csv_name), level="INFO")
                return True
        
        return False
    except Exception as e:
        print("[WARNING] Failed to compare CSV with config: {}".format(str(e)), file=sys.stderr)
        _log("Failed to compare CSV with config: {}".format(str(e)), level="WARNING")
        return False

def move_and_rename_csv(source_path, target_folder, timestamp=None):
    """Move CSV to target folder with timestamp rename. Returns (new_path, original_filename)."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    original_filename = os.path.basename(source_path)
    new_filename = "SX_CSV_{}.csv".format(timestamp)
    new_path = os.path.join(target_folder, new_filename)
    
    shutil.move(source_path, new_path)
    
    return (new_path, original_filename)

def build_cache(config, silent=False):
    """Build deductible cache from config."""
    if not HAS_BUILD_CACHE:
        if not silent:
            print("[WARNING] Deductible cache builder not available")
        _log("Deductible cache builder not available", level="WARNING")
        return 0
    
    if not silent:
        print("Building deductible cache (silent)...")
    _log("Building deductible cache", level="INFO")
    
    try:
        # Call build_deductible_cache directly
        # verbose=False to suppress output (silent mode)
        result = build_deductible_cache(config=config, verbose=False, skip_internet_check=False, submit_error_report=True)
        if result == 0:
            _log("Deductible cache build completed successfully", level="INFO")
        else:
            _log("Deductible cache builder reported an error (see logs for details)", level="WARNING")
        return result
    except Exception as e:
        print("[WARNING] Deductible cache builder error: {}".format(str(e)), file=sys.stderr)
        _log("Deductible cache builder error: {}".format(str(e)), level="WARNING")
        return 1

def process_csv(source_folder, target_folder, config_file, local_storage_path=None, python_script=None, silent=False):
    """Main processing function - orchestrates all CSV operations."""
    _log("Starting CSV processing workflow", level="INFO")
    _log("Configuration: Source={}, Target={}, Config={}".format(source_folder, target_folder, config_file), level="DEBUG")
    
    # Validate paths
    validate_paths(source_folder, target_folder, config_file, local_storage_path)
    
    # Move CSVs from local storage to source folder
    if local_storage_path:
        _log("Checking for new files in local storage: {}".format(local_storage_path), level="DEBUG")
        moved_count = move_csvs_from_storage(local_storage_path, source_folder, silent=silent)
        if moved_count > 0:
            _log("Discovered and moved {} new CSV file(s) for processing".format(moved_count), level="INFO")
    
    # Load config for later use
    config = load_config(config_file)
    
    # Find most recent CSV file
    latest_csv_name, latest_csv_path = find_latest_csv(source_folder)
    
    if not latest_csv_name:
        # No CSV files found - skip processing but build cache
        if not silent:
            print("No CSV files found in {}. This is normal when only DOCX files were received from the email download.".format(source_folder))
            print("Skipping CSV processing, but will build deductible cache using latest known CSV from config.")
        _log("No CSV files found in source folder {} - skipping CSV specific redistribution".format(source_folder), level="INFO")
        
        # Build cache anyway (using latest known CSV from config)
        _log("Triggering deductible cache build using existing config CSV path", level="DEBUG")
        build_cache(config, silent=silent)
        return 0
    
    _log("Identified latest CSV for processing: {}".format(latest_csv_name), level="INFO")
    
    if not silent:
        print("Validating latest CSV with config file...")
    
    # Compare with config and prompt if different (non-silent mode)
    compare_csv_with_config(latest_csv_path, config_file, target_folder, silent=silent)
    
    # Store original filename before timestamp rename
    original_csv_filename = latest_csv_name
    
    # Move and rename CSV with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    new_csv_path, _ = move_and_rename_csv(latest_csv_path, target_folder, timestamp=timestamp)
    new_filename = os.path.basename(new_csv_path)
    
    if not silent:
        print("Processing CSV...")
    
    _log("Moved and renamed CSV: {} -> {} (in target folder)".format(original_csv_filename, new_filename), level="INFO")
    
    # Update config with new CSV path
    if HAS_UPDATE_JSON:
        try:
            update_csv_path(config_file, new_csv_path)
            _log("Successfully updated config.json with new CSV path: {}".format(new_csv_path), level="INFO")
        except Exception as e:
            print("[WARNING] Failed to update config with new CSV path: {}".format(str(e)), file=sys.stderr)
            _log("Failed to update config with new CSV path: {}".format(str(e)), level="WARNING")
    
    # Update downloaded_emails.txt with original filename (before timestamp rename)
    if HAS_ADD_DOWNLOADED_EMAIL:
        # Verify file exists at destination before updating
        if os.path.exists(new_csv_path):
            try:
                _log("Adding original filename to processed tracker: {}".format(original_csv_filename), level="DEBUG")
                success = add_downloaded_email(original_csv_filename, config=config, log_fn=None)
                if success:
                    _log("Updated downloaded_emails.txt successfully for: {}".format(original_csv_filename), level="INFO")
                else:
                    if not silent:
                        print("[WARNING] Failed to update downloaded_emails.txt for {}".format(original_csv_filename), file=sys.stderr)
                    _log("Failed to update downloaded_emails.txt for {}".format(original_csv_filename), level="WARNING")
            except Exception as e:
                if not silent:
                    print("[WARNING] Error updating downloaded_emails.txt for {}: {}".format(original_csv_filename, str(e)), file=sys.stderr)
                _log("Error updating downloaded_emails.txt for {}: {}".format(original_csv_filename, str(e)), level="WARNING")
    
    # Build deductible cache
    _log("Initiating final deductible cache build step", level="DEBUG")
    build_cache(config, silent=silent)
    
    # Check for straggler files in source folder (should be empty now)
    _log_stragglers(source_folder)
    
    if not silent:
        print("CSV Processor Complete.")
    
    _log("CSV processing workflow completed successfully", level="INFO")
    return 0

def _log_stragglers(source_folder):
    """Scan source folder for any remaining CSV or DOCX files and log a WARNING."""
    csv_stragglers = glob.glob(os.path.join(source_folder, "*.csv"))
    docx_stragglers = glob.glob(os.path.join(source_folder, "*.docx"))
    
    total = len(csv_stragglers) + len(docx_stragglers)
    if total > 0:
        msg = "STRAGGLERS DETECTED in working folder {}: Found {} file(s) ({} CSV, {} DOCX) that were not processed or moved.".format(
            source_folder, total, len(csv_stragglers), len(docx_stragglers))
        _log(msg, level="WARNING")
        
        # Log individual stragglers for easier cleanup
        for f in csv_stragglers + docx_stragglers:
            _log("Straggler file: {}".format(os.path.basename(f)), level="DEBUG")

def main():
    parser = argparse.ArgumentParser(description='MediBot CSV Processor')
    parser.add_argument('--config', required=True, help='Path to config.json')
    parser.add_argument('--source-folder', required=True, help='Source folder to scan for CSV files')
    parser.add_argument('--target-folder', required=True, help='Target folder for processed CSV files')
    parser.add_argument('--local-storage-path', help='Local storage path for CSV files (optional)')
    parser.add_argument('--python-script', help='Path to update_json.py (optional, for backward compat - not used)')
    parser.add_argument('--silent', action='store_true', help='Suppress non-error output')
    
    args = parser.parse_args()
    
    # Resolve paths to absolute
    config_file = os.path.abspath(os.path.expanduser(args.config))
    source_folder = os.path.abspath(os.path.expanduser(args.source_folder))
    target_folder = os.path.abspath(os.path.expanduser(args.target_folder))
    local_storage_path = None
    if args.local_storage_path:
        local_storage_path = os.path.abspath(os.path.expanduser(args.local_storage_path))
    
    # Run processing
    try:
        return process_csv(
            source_folder=source_folder,
            target_folder=target_folder,
            config_file=config_file,
            local_storage_path=local_storage_path,
            python_script=args.python_script,  # Not used in Python version, but kept for compat
            silent=args.silent
        )
    except KeyboardInterrupt:
        print("\n[INFO] CSV processing interrupted by user", file=sys.stderr)
        _log("CSV processing interrupted by user", level="INFO")
        return 1
    except Exception as e:
        print("ERROR|CSV processing failed: {}".format(str(e)), file=sys.stderr)
        _log("CSV processing failed: {}".format(str(e)), level="ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
