#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediBot Secondary Pickup Scanner - Browser Downloads Migration

This script processes files downloaded via browser to source_folder (C:\MEDIANSI\MediCare),
ensuring primary route files (from local_storage_path) take precedence and browser-downloaded
files are migrated to appropriate locations.

Deduplication Logic:
- CSV files: Leave in source_folder (process_csvs.py handles them)
- DOCX files: Move to inputFilePath if no duplicate exists in local_storage_path
- If duplicate exists in local_storage_path: remove browser-downloaded file (primary takes precedence)

When --execute flag is used:
- Executes file operations directly (REMOVE, MOVE, KEEP)
- Updates downloaded_emails.txt for moved DOCX files
- Outputs statistics summary
- Use --silent flag to suppress non-error output

When --execute flag is NOT used (backward compatibility):
- Output Format: Lines in format: ACTION|FILEPATH
- Where ACTION is: REMOVE, KEEP, MOVE
- And FILEPATH is the full path to the file
"""

import os
import sys
import json
import argparse
import shutil

# Setup Python path to find MediCafe
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from MediCafe.core_utils import extract_medilink_config, get_shared_config_loader

# Try to import add_downloaded_email for DOCX file tracking
try:
    from MediLink.MediLink_Gmail import add_downloaded_email
    HAS_ADD_DOWNLOADED_EMAIL = True
except ImportError:
    HAS_ADD_DOWNLOADED_EMAIL = False

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
        # Resolve to absolute path to avoid issues with relative paths and spaces
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(config_path)
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print("ERROR|Failed to load config: {}".format(str(e)))
        sys.exit(1)

def get_medilink_config(config):
    """Extract MediLink_Config section"""
    try:
        medi_config = extract_medilink_config(config)
        return medi_config
    except Exception as e:
        print("ERROR|Failed to extract MediLink config: {}".format(str(e)))
        sys.exit(1)

def scan_files(source_folder):
    """Scan source_folder for .csv and .docx files"""
    files_to_process = []

    if not os.path.exists(source_folder):
        print("ERROR|Source folder does not exist: {}".format(source_folder), file=sys.stderr)
        print("ERROR|Absolute source folder path: {}".format(os.path.abspath(source_folder)), file=sys.stderr)
        sys.exit(1)

    try:
        for filename in os.listdir(source_folder):
            if filename.lower().endswith(('.csv', '.docx')):
                filepath = os.path.join(source_folder, filename)
                if os.path.isfile(filepath):
                    files_to_process.append((filename, filepath))
    except Exception as e:
        print("ERROR|Failed to scan source folder: {}".format(str(e)))
        sys.exit(1)

    return files_to_process

def analyze_file_actions(files, local_storage_path, input_file_path):
    """Analyze files and determine actions based on deduplication logic"""
    actions = []

    for filename, filepath in files:
        try:
            # Check if duplicate exists in local_storage_path
            duplicate_path = os.path.join(local_storage_path, filename)
            duplicate_exists = os.path.exists(duplicate_path)

            if duplicate_exists:
                # Primary route file takes precedence - remove browser download
                actions.append(("REMOVE", filepath))
            else:
                # No duplicate - process based on file type
                if filename.lower().endswith('.csv'):
                    # CSV files stay in source_folder for process_csvs.py
                    actions.append(("KEEP", filepath))
                elif filename.lower().endswith('.docx'):
                    # DOCX files move to local_storage_path for Bot pickup
                    if local_storage_path:
                        destination = os.path.join(local_storage_path, filename)
                        actions.append(("MOVE", filepath, destination))
                    else:
                        # No local_storage_path configured - keep in place
                        actions.append(("KEEP", filepath))

        except Exception as e:
            print("ERROR|Failed to analyze file {}: {}".format(filepath, str(e)))
            # On error, keep file in place
            actions.append(("KEEP", filepath))

    return actions

def output_actions(actions):
    """Output actions in format parseable by batch file"""
    for action in actions:
        if len(action) == 2:
            # REMOVE or KEEP actions
            action_type, filepath = action
            print("{}|{}".format(action_type, filepath))
        elif len(action) == 3:
            # MOVE action with destination
            action_type, source_path, dest_path = action
            print("{}|{}|{}".format(action_type, source_path, dest_path))


def execute_remove(filepath, silent=False):
    """
    Execute REMOVE action - delete the file.
    
    Args:
        filepath: Path to file to remove
        silent: If True, suppress output
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(filepath):
            if not silent:
                print("[WARNING] File does not exist, skipping removal: {}".format(filepath), file=sys.stderr)
            return False
        
        os.remove(filepath)
        if not silent:
            print("Removed: {}".format(filepath))
        return True
    except PermissionError as e:
        print("[WARNING] Permission denied removing file {}: {}".format(filepath, str(e)), file=sys.stderr)
        return False
    except Exception as e:
        print("[WARNING] Failed to remove file {}: {}".format(filepath, str(e)), file=sys.stderr)
        return False


def execute_move(source_path, dest_path, config, silent=False):
    """
    Execute MOVE action - move file to destination and update downloaded_emails.txt for DOCX files.
    
    Args:
        source_path: Source file path
        dest_path: Destination file path
        config: Configuration dict
        silent: If True, suppress output
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(source_path):
            if not silent:
                print("[WARNING] Source file does not exist: {}".format(source_path), file=sys.stderr)
            return False
        
        # Ensure destination directory exists
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        
        # Extract filename for downloaded_emails.txt update
        filename = os.path.basename(source_path)
        is_docx = filename.lower().endswith('.docx')
        
        # Move the file
        shutil.move(source_path, dest_path)
        
        if not silent:
            label = "Face Sheet" if is_docx else "CSV"
            print("Moved {}: {} -> {}".format(label, source_path, dest_path))
        
        # Update downloaded_emails.txt for DOCX files
        if is_docx and HAS_ADD_DOWNLOADED_EMAIL:
            # Verify file exists at destination before updating
            if os.path.exists(dest_path):
                try:
                    success = add_downloaded_email(filename, config=config, log_fn=None)
                    if not success and not silent:
                        print("[WARNING] Failed to update downloaded_emails.txt for {}".format(filename), file=sys.stderr)
                except Exception as e:
                    if not silent:
                        print("[WARNING] Error updating downloaded_emails.txt for {}: {}".format(filename, str(e)), file=sys.stderr)
        
        return True
    except PermissionError as e:
        print("[WARNING] Permission denied moving file {} to {}: {}".format(source_path, dest_path, str(e)), file=sys.stderr)
        return False
    except Exception as e:
        print("[WARNING] Failed to move file {} to {}: {}".format(source_path, dest_path, str(e)), file=sys.stderr)
        return False


def execute_keep(filepath, silent=False):
    """
    Execute KEEP action - no operation, just count.
    
    Args:
        filepath: Path to file (kept in place)
        silent: If True, suppress output
    
    Returns:
        bool: Always True (no-op)
    """
    if not silent:
        print("Keeping: {}".format(filepath))
    return True


def execute_actions(actions, config, silent=False):
    """
    Execute file operations based on actions.
    
    Args:
        actions: List of (action_type, source_path, [dest_path]) tuples
        config: Configuration dict
        silent: If True, suppress non-error output
    
    Returns:
        dict: Statistics {'processed': int, 'removed': int, 'moved': int, 'kept': int}
    """
    stats = {
        'processed': 0,
        'removed': 0,
        'moved': 0,
        'kept': 0
    }
    
    for action in actions:
        try:
            if len(action) == 2:
                action_type, filepath = action
                
                if action_type == "REMOVE":
                    if execute_remove(filepath, silent=silent):
                        stats['removed'] += 1
                elif action_type == "KEEP":
                    if execute_keep(filepath, silent=silent):
                        stats['kept'] += 1
                elif action_type == "ERROR":
                    print("[ERROR] {}".format(filepath), file=sys.stderr)
                    # Continue processing other files
                
            elif len(action) == 3:
                action_type, source_path, dest_path = action
                
                if action_type == "MOVE":
                    if execute_move(source_path, dest_path, config, silent=silent):
                        stats['moved'] += 1
            
            stats['processed'] += 1
            
        except Exception as e:
            print("[ERROR] Failed to execute action {}: {}".format(action, str(e)), file=sys.stderr)
            stats['processed'] += 1
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='MediBot Browser Downloads Migration')
    parser.add_argument('--config', required=True, help='Path to config.json')
    parser.add_argument('--source-folder', required=True, help='Source folder to scan')
    parser.add_argument('--execute', action='store_true', help='Execute file operations (default: analyze only)')
    parser.add_argument('--silent', action='store_true', help='Suppress non-error output (only used with --execute)')

    args = parser.parse_args()

    # Resolve paths to absolute
    config_path = os.path.abspath(os.path.expanduser(args.config))
    source_folder = os.path.abspath(os.path.expanduser(args.source_folder))

    # Load configuration
    config = load_config(config_path)
    medi_config = get_medilink_config(config)

    # Extract required paths from config (should already be absolute paths)
    # Only normalize to clean up any path separators, don't resolve relative paths
    # as config paths may span multiple drives (C: and F:)
    # Exception: if path is '.' (default), resolve it relative to config file's directory
    local_storage_path = medi_config.get('local_storage_path', '.')
    if local_storage_path:
        if local_storage_path == '.':
            # Default '.' should be resolved relative to config file location
            config_dir = os.path.dirname(os.path.abspath(config_path))
            local_storage_path = os.path.abspath(os.path.join(config_dir, local_storage_path))
        else:
            local_storage_path = os.path.normpath(local_storage_path)
    
    input_file_path = medi_config.get('inputFilePath')
    if input_file_path:
        if input_file_path == '.':
            # Default '.' should be resolved relative to config file location
            config_dir = os.path.dirname(os.path.abspath(config_path))
            input_file_path = os.path.abspath(os.path.join(config_dir, input_file_path))
        else:
            input_file_path = os.path.normpath(input_file_path)

    # Validate paths exist
    if not os.path.exists(local_storage_path):
        print("ERROR|Local storage path does not exist: {}".format(local_storage_path), file=sys.stderr)
        print("ERROR|Resolved local_storage_path: {}".format(local_storage_path), file=sys.stderr)
        print("ERROR|Config file location: {}".format(os.path.dirname(os.path.abspath(config_path))), file=sys.stderr)
        sys.exit(1)

    if input_file_path and not os.path.exists(input_file_path):
        if not args.execute:
            # In analyze mode, warn but continue
            print("WARNING|Input file path does not exist: {}".format(input_file_path), file=sys.stderr)
            print("WARNING|Resolved input_file_path: {}".format(input_file_path), file=sys.stderr)
        # In execute mode, directory will be created during move operation

    # Scan for files
    files = scan_files(source_folder)

    if not files:
        # No files to process
        if args.execute and not args.silent:
            print("No files found in {} to process.".format(source_folder))
        return 0

    # Analyze and determine actions
    actions = analyze_file_actions(files, local_storage_path, input_file_path)

    if args.execute:
        # Execute mode: perform file operations and output summary
        _log("Starting browser downloads migration", level="INFO")
        _log("Source folder: {}".format(source_folder), level="INFO")
        _log("Config file: {}".format(config_path), level="INFO")
        
        if not args.silent:
            print("Scanning {} for browser downloads...".format(source_folder))
        
        # Execute all actions
        stats = execute_actions(actions, config, silent=args.silent)
        
        # Log results
        _log("Migration completed: {} processed, {} removed, {} moved, {} kept".format(
            stats['processed'], stats['removed'], stats['moved'], stats['kept']), level="INFO")
        
        # Output summary
        if not args.silent:
            print("")
            print("Migration Summary:")
            print("  Files processed: {}".format(stats['processed']))
            print("  Files removed (duplicates): {}".format(stats['removed']))
            print("  Files moved: {}".format(stats['moved']))
            print("  Files kept: {}".format(stats['kept']))
            print("")
            print("Browser downloads migration complete.")
        elif stats['processed'] > 0:
            # Silent mode - only show summary if files were processed
            summary_line = "[INFO] Browser downloads: {} removed, {} moved, {} kept".format(
                stats['removed'], stats['moved'], stats['kept'])
            print(summary_line)
        
        return 0
    else:
        # Analyze mode (backward compatibility): output actions for batch script parsing
        output_actions(actions)
        return 0

if __name__ == '__main__':
    sys.exit(main())