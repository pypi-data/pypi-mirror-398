#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediBot_Crosswalk_File_Utils.py - File operations for crosswalk editing

This module contains functions for opening crosswalk files for manual editing
and getting crosswalk file paths from configuration.

Compatible with Python 3.4.4 and Windows XP environments.
"""

import os, sys, subprocess

# Set the project directory to the parent directory of the current file
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path: 
    sys.path.append(project_dir)

# Use core utilities for standardized imports
from MediCafe.core_utils import (
    get_config_loader_with_fallback
)

# Initialize configuration loader with fallback
MediLink_ConfigLoader = get_config_loader_with_fallback()

# =============================================================================
# FILE PATH UTILITIES
# =============================================================================

def get_crosswalk_path(config):
    """
    Gets the crosswalk file path from configuration.
    
    Args:
        config (dict): Configuration settings containing crosswalk path.
        
    Returns:
        tuple: (crosswalk_path, exists)
            - crosswalk_path: Path to crosswalk file
            - exists: True if file exists, False otherwise
    """
    try:
        if 'MediLink_Config' in config:
            crosswalk_path = config['MediLink_Config'].get('crosswalkPath', 'crosswalk.json')
        else:
            crosswalk_path = config.get('crosswalkPath', 'crosswalk.json')
    except (KeyError, AttributeError):
        crosswalk_path = 'crosswalk.json'
    
    # Convert relative path to absolute if needed
    if not os.path.isabs(crosswalk_path):
        # Try to resolve relative to project directory
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        potential_path = os.path.join(project_dir, crosswalk_path)
        if os.path.exists(potential_path):
            crosswalk_path = potential_path
        else:
            # Try relative to current working directory
            if os.path.exists(crosswalk_path):
                crosswalk_path = os.path.abspath(crosswalk_path)
    
    exists = os.path.exists(crosswalk_path)
    return crosswalk_path, exists

# =============================================================================
# FILE OPENING UTILITIES
# =============================================================================

def open_crosswalk_file_for_editing(config):
    """
    Opens the crosswalk JSON file in the default editor for manual editing.
    Windows XP compatible implementation.
    
    Args:
        config (dict): Configuration settings containing crosswalk path.
        
    Returns:
        tuple: (success, file_path, error_message)
            - success: True if file was opened successfully
            - file_path: Path to the crosswalk file
            - error_message: Error message if opening failed (None on success)
    """
    crosswalk_path, exists = get_crosswalk_path(config)
    
    if not exists:
        error_msg = "Crosswalk file not found: {}".format(crosswalk_path)
        print("ERROR: {}".format(error_msg))
        MediLink_ConfigLoader.log(error_msg, config, level="ERROR")
        return False, crosswalk_path, error_msg
    
    # Windows XP compatible file opening
    try:
        if os.name == 'nt':  # Windows
            # Try os.startfile first (Windows XP compatible)
            try:
                os.startfile(crosswalk_path)
                print("Opened crosswalk file: {}".format(crosswalk_path))
                MediLink_ConfigLoader.log("Opened crosswalk file for editing: {}".format(crosswalk_path), config, level="INFO")
                return True, crosswalk_path, None
            except (AttributeError, OSError):
                # Fallback to os.system if startfile not available
                try:
                    # Use start command with empty title (Windows XP compatible)
                    os.system('start "" "{}"'.format(crosswalk_path))
                    print("Opened crosswalk file: {}".format(crosswalk_path))
                    MediLink_ConfigLoader.log("Opened crosswalk file for editing (fallback method): {}".format(crosswalk_path), config, level="INFO")
                    return True, crosswalk_path, None
                except Exception as e:
                    # Last resort: try notepad
                    # Note: Using Popen without wait() is intentional - fire-and-forget for opening files
                    try:
                        subprocess.Popen(['notepad.exe', crosswalk_path])
                        print("Opened crosswalk file in Notepad: {}".format(crosswalk_path))
                        MediLink_ConfigLoader.log("Opened crosswalk file in Notepad: {}".format(crosswalk_path), config, level="INFO")
                        return True, crosswalk_path, None
                    except Exception as e2:
                        error_msg = "Failed to open crosswalk file: {}".format(str(e2))
                        print("ERROR: {}".format(error_msg))
                        MediLink_ConfigLoader.log(error_msg, config, level="ERROR")
                        return False, crosswalk_path, error_msg
        else:
            # Non-Windows platform
            try:
                # Try xdg-open for Linux
                # Note: Using Popen without wait() is intentional - fire-and-forget for opening files
                subprocess.Popen(['xdg-open', crosswalk_path])
                print("Opened crosswalk file: {}".format(crosswalk_path))
                MediLink_ConfigLoader.log("Opened crosswalk file for editing: {}".format(crosswalk_path), config, level="INFO")
                return True, crosswalk_path, None
            except Exception as e:
                error_msg = "Cannot open file on this platform. File path: {}".format(crosswalk_path)
                print("WARNING: {}".format(error_msg))
                print("Please manually open: {}".format(crosswalk_path))
                MediLink_ConfigLoader.log("{} - Error: {}".format(error_msg, e), config, level="WARNING")
                return False, crosswalk_path, error_msg
    except Exception as e:
        error_msg = "Unexpected error opening crosswalk file: {}".format(str(e))
        print("ERROR: {}".format(error_msg))
        MediLink_ConfigLoader.log(error_msg, config, level="ERROR")
        return False, crosswalk_path, error_msg

