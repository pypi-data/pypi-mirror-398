#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediBot_Crosswalk_Cleaning.py - Cleaning functions for crosswalk contamination

This module contains functions for cleaning contaminated crosswalk data,
including preview of cleaning actions and user-confirmed cleaning operations.

Compatible with Python 3.4.4 and Windows XP environments.
"""

import sys, os

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

# Import save_crosswalk from utils with fallback
try:
    from MediBot.MediBot_Crosswalk_Utils import save_crosswalk
except ImportError:
    save_crosswalk = None

# =============================================================================
# CONSTANTS
# =============================================================================

# Truncation limits for display and cleaning
MAX_NAME_DISPLAY_LENGTH = 50  # Standard display truncation
MAX_NAME_DISPLAY_LENGTH_LONG = 60  # Longer display truncation
MAX_CLEANED_NAME_LENGTH = 40  # Maximum length for cleaned names

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _clean_contaminated_name(name, max_length=MAX_CLEANED_NAME_LENGTH):
    """
    Cleans a contaminated payer name by removing address portions.
    
    Attempts to extract a valid name from contaminated data by:
    - Splitting on comma and taking the first part (removes address components)
    - Truncating to reasonable length
    
    Args:
        name (str): The contaminated name to clean
        max_length (int): Maximum length for cleaned name (default: MAX_CLEANED_NAME_LENGTH)
        
    Returns:
        str: Cleaned name, or empty string if no valid name could be extracted
    """
    if not name:
        return ''
    
    # Try to extract first part before comma (removes address portions)
    cleaned_name = name.split(',')[0].strip() if ',' in name else name.strip()
    
    # Truncate to reasonable length
    if len(cleaned_name) > max_length:
        cleaned_name = cleaned_name[:max_length]
    
    return cleaned_name

# =============================================================================
# CLEANING ACTION PREVIEW
# =============================================================================

def preview_cleaning_actions(crosswalk, contaminated_payer_ids):
    """
    Generates a preview of what cleaning actions would do for contaminated payer IDs.
    
    Args:
        crosswalk (dict): The crosswalk dictionary.
        contaminated_payer_ids (list): List of payer IDs with contaminated names.
        
    Returns:
        tuple: (action_list, details_dict)
            - action_list: List of (payer_id, action_type, description) tuples
            - details_dict: Dict mapping payer_id to details dict
    """
    action_list = []
    details_dict = {}
    
    for payer_id in contaminated_payer_ids:
        if payer_id not in crosswalk.get('payer_id', {}):
            continue
        
        details = crosswalk['payer_id'][payer_id]
        current_name = details.get('name', '')
        
        # Generate preview actions
        actions_for_payer = []
        
        # Truncate current name for display
        display_name = current_name[:MAX_NAME_DISPLAY_LENGTH] + "..." if len(current_name) > MAX_NAME_DISPLAY_LENGTH else current_name
        
        # Action 1: Remove payer entry
        actions_for_payer.append({
            'action': 'remove',
            'description': "Remove payer entry '{}' (current name: '{}')".format(payer_id, display_name)
        })
        
        # Action 2: Set name to "Unknown"
        actions_for_payer.append({
            'action': 'set_unknown',
            'description': "Set name to 'Unknown' for payer '{}' (current: '{}')".format(payer_id, display_name)
        })
        
        # Action 3: Attempt to fix (remove address portions)
        cleaned_name = _clean_contaminated_name(current_name)
        
        if cleaned_name and cleaned_name != current_name:
            actions_for_payer.append({
                'action': 'fix',
                'description': "Fix name for payer '{}': '{}' -> '{}'".format(
                    payer_id, display_name, cleaned_name)
            })
        else:
            actions_for_payer.append({
                'action': 'fix',
                'description': "Fix name for payer '{}' (no fix available, would set to 'Unknown')".format(payer_id)
            })
        
        details_dict[payer_id] = {
            'current_name': current_name,
            'actions': actions_for_payer
        }
        
        # Add to action list
        for action_info in actions_for_payer:
            action_list.append((payer_id, action_info['action'], action_info['description']))
    
    return action_list, details_dict

# =============================================================================
# CLEANING OPERATIONS
# =============================================================================

def clean_contaminated_crosswalk(crosswalk, contaminated_payer_ids, config, client=None):
    """
    Cleans contaminated crosswalk entries with user confirmation for each action.
    
    For each contaminated payer, prompts user to choose:
    - Remove the payer entry
    - Set name to "Unknown"
    - Attempt to fix by removing address portions
    
    Args:
        crosswalk (dict): The crosswalk dictionary to clean (modified in place).
        contaminated_payer_ids (list): List of payer IDs with contaminated names.
        config (dict): Configuration settings for logging.
        client (APIClient, optional): API client for save operations. If None, will attempt to create one.
        
    Returns:
        bool: True if cleaning was successful (or skipped), False on error.
        
    Note:
        This function modifies the crosswalk dictionary in place and saves it to disk
        after all cleaning operations are complete.
    """
    if not contaminated_payer_ids:
        return True
    
    # Import save function if available
    if save_crosswalk is None:
        print("ERROR: Cannot save crosswalk - save_crosswalk function not available")
        MediLink_ConfigLoader.log("Cannot save crosswalk - save_crosswalk function not available", config, level="ERROR")
        return False
    
    print("\nCleaning contaminated payer entries:")
    print("=" * 60)
    
    for payer_id in contaminated_payer_ids:
        if payer_id not in crosswalk.get('payer_id', {}):
            continue
        
        details = crosswalk['payer_id'][payer_id]
        current_name = details.get('name', '')
        
        # Display current state (use longer truncation for interactive display)
        display_name = current_name[:MAX_NAME_DISPLAY_LENGTH_LONG] + "..." if len(current_name) > MAX_NAME_DISPLAY_LENGTH_LONG else current_name
        print("\nPayer ID: {}".format(payer_id))
        print("Current name: '{}'".format(display_name))
        print("\nChoose cleaning action:")
        print("  1. Remove this payer entry")
        print("  2. Set name to 'Unknown'")
        print("  3. Attempt to fix name (remove address portions)")
        print("  4. Skip this payer")
        
        while True:
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                # Remove payer entry
                confirm = input("Are you sure you want to remove payer '{}'? (yes/no): ".format(payer_id)).strip().lower()
                if confirm in ('yes', 'y'):
                    del crosswalk['payer_id'][payer_id]
                    print("Removed payer '{}'".format(payer_id))
                    MediLink_ConfigLoader.log("Removed contaminated payer '{}' from crosswalk".format(payer_id), config, level="INFO")
                    break
                else:
                    print("Cancelled removal")
                    break
            
            elif choice == '2':
                # Set name to Unknown
                crosswalk['payer_id'][payer_id]['name'] = 'Unknown'
                print("Set name to 'Unknown' for payer '{}'".format(payer_id))
                MediLink_ConfigLoader.log("Set name to 'Unknown' for contaminated payer '{}'".format(payer_id), config, level="INFO")
                break
            
            elif choice == '3':
                # Attempt to fix using centralized cleaning function
                cleaned_name = _clean_contaminated_name(current_name)
                
                if cleaned_name and cleaned_name != current_name:
                    crosswalk['payer_id'][payer_id]['name'] = cleaned_name
                    print("Fixed name for payer '{}': '{}'".format(payer_id, cleaned_name))
                    MediLink_ConfigLoader.log("Fixed name for contaminated payer '{}': '{}'".format(payer_id, cleaned_name), config, level="INFO")
                else:
                    # Fallback to Unknown if fix didn't work
                    crosswalk['payer_id'][payer_id]['name'] = 'Unknown'
                    print("Could not fix name for payer '{}', set to 'Unknown'".format(payer_id))
                    MediLink_ConfigLoader.log("Could not fix name for contaminated payer '{}', set to 'Unknown'".format(payer_id), config, level="INFO")
                break
            
            elif choice == '4':
                # Skip
                print("Skipped payer '{}'".format(payer_id))
                break
            
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    # Save the cleaned crosswalk
    try:
        if save_crosswalk:
            # Use provided client or create one if needed
            if client is None:
                try:
                    from MediCafe.api_core import APIClient
                    client = APIClient()
                except Exception as e:
                    # Log failure but continue (client may not be needed if skip_api_operations=True)
                    MediLink_ConfigLoader.log("Could not create APIClient: {}".format(e), config, level="DEBUG")
                    client = None
            
            # Try to save with skip_api_operations=True if supported
            try:
                success = save_crosswalk(client, config, crosswalk, skip_api_operations=True)
            except TypeError:
                # Fallback if skip_api_operations not supported
                success = save_crosswalk(client, config, crosswalk)
            
            if success:
                print("\nCleaned crosswalk saved successfully")
                MediLink_ConfigLoader.log("Cleaned crosswalk saved successfully", config, level="INFO")
                return True
            else:
                print("\nWARNING: Failed to save cleaned crosswalk")
                MediLink_ConfigLoader.log("Failed to save cleaned crosswalk", config, level="WARNING")
                return False
        else:
            print("\nWARNING: Cannot save crosswalk - save function not available")
            return False
    except Exception as e:
        print("\nERROR: Failed to save cleaned crosswalk: {}".format(e))
        MediLink_ConfigLoader.log("Error saving cleaned crosswalk: {}".format(e), config, level="ERROR")
        return False

