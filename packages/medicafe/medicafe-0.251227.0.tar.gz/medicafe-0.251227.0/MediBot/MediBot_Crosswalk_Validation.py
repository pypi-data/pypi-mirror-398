#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediBot_Crosswalk_Validation.py - Validation functions for crosswalk health checking

This module contains validation functions for detecting contaminated payer names,
validating JSON structure, and checking crosswalk schema integrity.

Compatible with Python 3.4.4 and Windows XP environments.
"""

import json, os, sys

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
# CONTAMINATION DETECTION
# =============================================================================

def detect_contaminated_payer_names(crosswalk):
    """
    Detects payer names that appear to be contaminated with address data or other invalid content.
    
    Focuses on catching major corruption (like full addresses) without false positives.
    Checks for:
    - Multiple commas (>=2): Strong indicator of address format
    - Very long names (>50 chars): Addresses are typically long
    - Name matches payer_id: Suggests misassignment
    - Numeric-only names: Could be zip codes or misassigned IDs
    
    Args:
        crosswalk (dict): The crosswalk dictionary to check.
        
    Returns:
        tuple: (contaminated_payer_ids_list, contamination_details_dict)
            - contaminated_payer_ids_list: List of payer IDs with contaminated names
            - contamination_details_dict: Dict mapping payer ID to reason string
    """
    contaminated_payer_ids = []
    contamination_details = {}
    
    if 'payer_id' not in crosswalk or not crosswalk['payer_id']:
        return contaminated_payer_ids, contamination_details
    
    for payer_id, details in crosswalk['payer_id'].items():
        name = details.get('name', '')
        
        # Skip empty, non-string, or "Unknown" names (handled by regular health check)
        if not name or not isinstance(name, str) or name == 'Unknown':
            continue
        
        name_stripped = name.strip()
        reason = None
        
        # Check for multiple commas (very strong indicator of address format)
        comma_count = name_stripped.count(',')
        if comma_count >= 2:
            reason = "Contains multiple commas ({} commas) - typical of address format".format(comma_count)
        
        # Check if name is suspiciously long (addresses are typically long)
        if reason is None and len(name_stripped) > 50:
            reason = "Name is unusually long ({} chars) - may be address data".format(len(name_stripped))
        
        # Check if name exactly matches payer_id (strong indicator of misassignment)
        # This catches both numeric and alphanumeric misassignments
        if reason is None:
            # Remove commas and spaces for comparison
            name_for_comparison = name_stripped.replace(',', '').replace(' ', '')
            payer_id_clean = str(payer_id).strip()
            if name_for_comparison.upper() == payer_id_clean.upper():
                reason = "Name exactly matches payer ID '{}' (suggests misassignment)".format(payer_id)
        
        # Check for numeric-only names (could be zip codes or misassigned IDs)
        if reason is None:
            # Remove commas and spaces to check if it's purely numeric
            name_numeric_check = name_stripped.replace(',', '').replace(' ', '')
            if name_numeric_check.isdigit():
                if len(name_numeric_check) == 5:
                    # 5-digit numeric could be a zip code
                    reason = "Name is 5-digit numeric only (could be zip code: {})".format(name_numeric_check)
                elif 3 <= len(name_numeric_check) <= 10:
                    # Other numeric-only names in payer ID format range are suspicious
                    reason = "Name is numeric-only in payer ID format range ({} digits) - may be misassigned".format(len(name_numeric_check))
        
        # Add to results if we found a reason
        if reason:
            contaminated_payer_ids.append(payer_id)
            contamination_details[payer_id] = reason
    
    return contaminated_payer_ids, contamination_details

# =============================================================================
# JSON STRUCTURE VALIDATION
# =============================================================================

def validate_crosswalk_json_structure(crosswalk):
    """
    Validates that the crosswalk conforms to expected structure and schema.
    
    Checks:
    - Required top-level keys exist
    - Each payer entry has expected keys
    - Data types are correct
    - No unexpected keys in payer entries
    
    Args:
        crosswalk (dict): The crosswalk dictionary to validate.
        
    Returns:
        tuple: (is_valid, structure_errors_list)
            - is_valid: True if structure is valid
            - structure_errors_list: List of error message strings
    """
    errors = []
    
    # Check if crosswalk is a dict
    if not isinstance(crosswalk, dict):
        errors.append("Crosswalk is not a dictionary")
        return False, errors
    
    # Check for required top-level key: payer_id
    if 'payer_id' not in crosswalk:
        errors.append("Missing required top-level key: 'payer_id'")
        return False, errors

    # TODO(MediBot Crosswalk Health):
    # Several "healthy" crosswalk bundles produced during the MediBot flow omit helper
    # dictionaries such as `csv_replacements` (and its sibling helper map at the same
    # nesting level). When those helpers are missing, `validate_crosswalk_json_structure`
    # flags the entire crosswalk as invalid even though every payer record is well-formed.
    # Decide whether to loosen this validator so those helper keys are optional, or update
    # the crosswalk writer to auto-populate empty dict placeholders so the existing health
    # check no longer trips on valid data.
    
    payer_id_dict = crosswalk.get('payer_id', {})
    if not isinstance(payer_id_dict, dict):
        errors.append("'payer_id' must be a dictionary")
        return False, errors
    
    # Expected keys for each payer entry
    expected_keys = ['name', 'medisoft_id', 'medisoft_medicare_id', 'endpoint']
    
    # Validate each payer entry
    for payer_id, details in payer_id_dict.items():
        if not isinstance(details, dict):
            errors.append("Payer ID '{}': entry must be a dictionary".format(payer_id))
            continue
        
        # Check for expected keys
        for key in expected_keys:
            if key not in details:
                errors.append("Payer ID '{}': missing required key '{}'".format(payer_id, key))
        
        # Check data types
        if 'name' in details:
            if not isinstance(details['name'], str):
                errors.append("Payer ID '{}': 'name' must be a string".format(payer_id))
        
        if 'medisoft_id' in details:
            if not isinstance(details['medisoft_id'], list):
                errors.append("Payer ID '{}': 'medisoft_id' must be a list".format(payer_id))
        
        if 'medisoft_medicare_id' in details:
            if not isinstance(details['medisoft_medicare_id'], list):
                errors.append("Payer ID '{}': 'medisoft_medicare_id' must be a list".format(payer_id))
        
        if 'endpoint' in details:
            if details['endpoint'] is not None and not isinstance(details['endpoint'], str):
                errors.append("Payer ID '{}': 'endpoint' must be a string or None".format(payer_id))
        
        # Check for unexpected keys (optional - just warn)
        allowed_keys = expected_keys + ['crossover_endpoint']  # Allow optional keys
        for key in details:
            if key not in allowed_keys:
                errors.append("Payer ID '{}': unexpected key '{}' (allowed: {})".format(
                    payer_id, key, ', '.join(allowed_keys)))
    
    is_valid = len(errors) == 0
    return is_valid, errors

# =============================================================================
# JSON LOAD AND VALIDATION
# =============================================================================

def load_and_validate_crosswalk_json(config):
    """
    Loads crosswalk JSON file and validates both syntax and structure.
    
    Args:
        config (dict): Configuration settings containing crosswalk path.
        
    Returns:
        tuple: (crosswalk_dict, is_valid, errors_list)
            - crosswalk_dict: Loaded crosswalk dictionary (or None if load failed)
            - is_valid: True if JSON is valid and structure is correct
            - errors_list: List of error message strings
    """
    all_errors = []
    
    # Get crosswalk path from config using centralized utility
    try:
        from MediBot.MediBot_Crosswalk_File_Utils import get_crosswalk_path
        crosswalk_path, exists = get_crosswalk_path(config)
        if not exists:
            all_errors.append("Crosswalk file not found: {}".format(crosswalk_path))
            return None, False, all_errors
    except ImportError:
        # Fallback if helper module not available
        MediLink_ConfigLoader.log("Could not import get_crosswalk_path, using fallback", config, level="WARNING")
        try:
            if 'MediLink_Config' in config:
                crosswalk_path = config['MediLink_Config'].get('crosswalkPath', 'crosswalk.json')
            else:
                crosswalk_path = config.get('crosswalkPath', 'crosswalk.json')
        except (KeyError, AttributeError):
            crosswalk_path = 'crosswalk.json'
        if not os.path.exists(crosswalk_path):
            all_errors.append("Crosswalk file not found: {}".format(crosswalk_path))
            return None, False, all_errors
    
    # Try to load JSON file
    crosswalk = None
    try:
        with open(crosswalk_path, 'r') as f:
            crosswalk = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = "Invalid JSON syntax in crosswalk file: {}".format(str(e))
        all_errors.append(error_msg)
        MediLink_ConfigLoader.log(error_msg, config, level="ERROR")
        return None, False, all_errors
    except Exception as e:
        error_msg = "Error loading crosswalk file: {}".format(str(e))
        all_errors.append(error_msg)
        MediLink_ConfigLoader.log(error_msg, config, level="ERROR")
        return None, False, all_errors
    
    # Validate structure (only if crosswalk was successfully loaded)
    # Note: crosswalk should not be None here due to early returns above, but check defensively
    if crosswalk is not None:
        is_valid, structure_errors = validate_crosswalk_json_structure(crosswalk)
        all_errors.extend(structure_errors)
    else:
        # Crosswalk failed to load or was None, already reported in errors above
        is_valid = False
    
    return crosswalk, is_valid, all_errors

