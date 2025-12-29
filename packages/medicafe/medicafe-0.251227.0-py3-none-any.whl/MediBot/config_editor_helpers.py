#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Config Editor Helper Functions
Provides JSON loading, validation, backup, and atomic write utilities for the config editor.
Compatible with Python 3.4.4 and Windows XP.
"""

import os
import json
import time
import tempfile
import shutil
import platform
from collections import OrderedDict

# Sensitive keys that should trigger extra confirmation
SENSITIVE_KEYS = ['password', 'token', 'secret', 'key', 'auth', 'credential', 'api_key', 'client_secret']

def resolve_config_path(default_path):
    """
    Resolve the config file path using the same logic as MediLink_ConfigLoader.
    This ensures the editor finds the config file in the same location as the main application.
    
    Args:
        default_path: The default path to try first
        
    Returns:
        str: The resolved config file path
    """
    # If the default path exists, use it
    if os.path.exists(default_path):
        return default_path
    
    # Try platform-specific fallbacks (same logic as MediLink_ConfigLoader)
    if platform.system() == 'Windows' and platform.release() == 'XP':
        # Use F: paths for Windows XP
        xp_path = "F:\\Medibot\\json\\config.json"
        if os.path.exists(xp_path):
            return xp_path
    elif platform.system() == 'Windows':
        # Use current working directory for other versions of Windows
        cwd_path = os.path.join(os.getcwd(), 'json', 'config.json')
        if os.path.exists(cwd_path):
            return cwd_path
    
    # If no fallback paths exist, return the original default path
    # (the editor will handle the missing file gracefully)
    return default_path

def load_config_safe(config_path):
    """
    Safely load config.json with fallback to empty structure.
    Returns (config_dict, error_message)
    """
    try:
        if not os.path.exists(config_path):
            return {}, "Config file not found: {}".format(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f, object_pairs_hook=OrderedDict)
        
        if not isinstance(config, dict):
            return {}, "Config file does not contain a valid JSON object"
        
        return config, None
        
    except json.JSONDecodeError as e:
        return {}, "Invalid JSON in config file: {}".format(str(e))
    except Exception as e:
        return {}, "Error loading config file: {}".format(str(e))

def create_backup(config_path):
    """
    Create a timestamped backup of the config file.
    Returns backup_path or None if failed.
    """
    try:
        if not os.path.exists(config_path):
            return None
        
        # Create timestamp in format YYYYMMDD_HHMMSS
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = "{}.bak.{}".format(config_path, timestamp)
        
        shutil.copy2(config_path, backup_path)
        return backup_path
        
    except Exception as e:
        print("Warning: Could not create backup: {}".format(str(e)))
        return None

def save_config_atomic(config_path, config_dict):
    """
    Save config dictionary to file using atomic write (temp file + rename).
    Compatible with Windows XP.
    Returns (success, error_message)
    """
    try:
        # Create temp file in same directory as target
        temp_dir = os.path.dirname(config_path)
        temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', dir=temp_dir)
        
        try:
            # Write to temp file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=4, separators=(',', ': '))
            
            # Atomic rename (works on Windows XP)
            if os.name == 'nt':  # Windows
                if os.path.exists(config_path):
                    os.remove(config_path)
                os.rename(temp_path, config_path)
            else:  # Unix-like
                os.rename(temp_path, config_path)
            
            return True, None
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.close(temp_fd)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            raise e
            
    except Exception as e:
        return False, "Error saving config: {}".format(str(e))

def validate_json_structure(data):
    """
    Validate that data can be serialized to valid JSON.
    Returns (is_valid, error_message)
    """
    try:
        json.dumps(data, ensure_ascii=False)
        return True, None
    except Exception as e:
        return False, "Invalid JSON structure: {}".format(str(e))

def is_sensitive_key(key_name):
    """
    Check if a key name appears to be sensitive.
    """
    key_lower = key_name.lower()
    return any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)

def get_value_type(value):
    """
    Determine the type of a JSON value for display purposes.
    """
    if isinstance(value, str):
        return "string"
    elif isinstance(value, (int, float)):
        return "number"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return "unknown"

def format_value_for_display(value, max_length=50):
    """
    Format a value for display in the editor, truncating if too long.
    """
    if isinstance(value, str):
        if len(value) > max_length:
            return '"{}..."'.format(value[:max_length-3])
        else:
            return '"{}"'.format(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, list):
        return "[{} items]".format(len(value))
    elif isinstance(value, dict):
        return "{{{} keys}}".format(len(value))
    else:
        return str(value)

def clear_config_cache():
    """
    Clear the MediLink_ConfigLoader cache after config changes.
    """
    try:
        # Import here to avoid issues if MediCafe not available
        import sys
        import os
        
        # Add parent directory to path to find MediCafe
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        from MediCafe.MediLink_ConfigLoader import clear_config_cache as clear_loader_cache
        
        # Use the loader's own cache clearing function
        clear_loader_cache()
        
        return True, None
        
    except Exception as e:
        return False, "Warning: Could not clear config cache: {}".format(str(e))

def get_nested_value(config, path_list):
    """
    Get a value from nested dictionary using path list.
    Returns (value, found) where found is boolean.
    """
    current = config
    try:
        for key in path_list:
            current = current[key]
        return current, True
    except (KeyError, TypeError):
        return None, False

def set_nested_value(config, path_list, value):
    """
    Set a value in nested dictionary using path list.
    Creates intermediate dictionaries if needed.
    """
    current = config
    for key in path_list[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = OrderedDict()
        current = current[key]
    current[path_list[-1]] = value

def get_path_string(path_list):
    """
    Convert path list to breadcrumb string.
    """
    if not path_list:
        return "config"
    return "config > " + " > ".join(path_list)

def validate_key_name(key_name, existing_keys):
    """
    Validate a new key name.
    Returns (is_valid, error_message)
    """
    if not key_name:
        return False, "Key name cannot be empty"
    
    if key_name in existing_keys:
        return False, "Key '{}' already exists".format(key_name)
    
    # Check for invalid characters that might break JSON
    invalid_chars = ['"', '\\', '/', '\n', '\r', '\t']
    for char in invalid_chars:
        if char in key_name:
            return False, "Key name contains invalid character: '{}'".format(char)
    
    return True, None

def parse_value_input(value_str, value_type):
    """
    Parse user input string into appropriate Python type.
    Returns (parsed_value, error_message)
    """
    try:
        if value_type == "string":
            # Remove surrounding quotes if present
            if value_str.startswith('"') and value_str.endswith('"'):
                value_str = value_str[1:-1]
            return value_str, None
            
        elif value_type == "number":
            # Try int first, then float
            if '.' in value_str:
                return float(value_str), None
            else:
                return int(value_str), None
                
        elif value_type == "boolean":
            value_lower = value_str.lower()
            if value_lower in ['true', 't', 'yes', 'y', '1']:
                return True, None
            elif value_lower in ['false', 'f', 'no', 'n', '0']:
                return False, None
            else:
                return None, "Invalid boolean value. Use true/false, yes/no, or 1/0"
                
        elif value_type == "array":
            # Simple array parsing - comma separated values
            if not value_str.strip():
                return [], None
            
            # Split by comma and strip whitespace
            items = [item.strip() for item in value_str.split(',')]
            return items, None
            
        elif value_type == "object":
            # For now, return empty object - user can add keys later
            return OrderedDict(), None
            
        else:
            return None, "Unknown value type: {}".format(value_type)
            
    except ValueError as e:
        return None, "Invalid value format: {}".format(str(e))
    except Exception as e:
        return None, "Error parsing value: {}".format(str(e))
