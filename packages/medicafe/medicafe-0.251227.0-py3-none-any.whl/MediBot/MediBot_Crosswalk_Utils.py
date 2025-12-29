#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MediBot_Crosswalk_Utils.py - Helper utilities for crosswalk operations

This module contains utility functions extracted from MediBot_Crosswalk_Library.py
to improve code organization and maintainability.

Compatible with Python 3.4.4 and Windows XP environments.
"""

import json, os, sys

# Set the project directory to the parent directory of the current file
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path: 
    sys.path.append(project_dir)

# Use core utilities for standardized imports
from MediCafe.core_utils import (
    import_medibot_module,
    get_config_loader_with_fallback
)

# Initialize configuration loader with fallback
MediLink_ConfigLoader = get_config_loader_with_fallback()

# Import MediBot modules using centralized import functions
MediBot_Preprocessor_lib = import_medibot_module('MediBot_Preprocessor_lib')

# Module-level cache for config and crosswalk to prevent redundant reloads
_cached_config = None
_cached_crosswalk = None

# =============================================================================
# CROSSWALK HEALTH CHECKING AND USER INTERACTION
# =============================================================================
# Functions for assessing crosswalk health and providing user prompts to skip
# unnecessary API calls when the crosswalk appears healthy.

def check_crosswalk_health(crosswalk):
    """
    Comprehensive health check for crosswalk - checks if payers have names, at least one medisoft ID,
    and detects contaminated payer names (address data in name fields).

    Args:
        crosswalk (dict): The crosswalk dictionary to check.

    Returns:
        tuple: (is_healthy, missing_names_count, missing_medisoft_ids_count, missing_names_list, missing_medisoft_ids_list, contaminated_names_list, contamination_details_dict)
            - is_healthy: True if crosswalk is healthy
            - missing_names_count: Count of payers missing names
            - missing_medisoft_ids_count: Count of payers missing medisoft IDs
            - missing_names_list: List of payer IDs missing names
            - missing_medisoft_ids_list: List of payer IDs missing medisoft IDs
            - contaminated_names_list: List of payer IDs with contaminated names
            - contamination_details_dict: Dict mapping payer ID to contamination reason
    """
    if 'payer_id' not in crosswalk or not crosswalk['payer_id']:
        return False, 0, 0, [], [], [], {}

    missing_names = 0
    missing_medisoft_ids = 0
    missing_names_list = []
    missing_medisoft_ids_list = []
    
    # Detect contaminated payer names using helper module
    contaminated_names_list = []
    contamination_details_dict = {}
    try:
        from MediBot.MediBot_Crosswalk_Validation import detect_contaminated_payer_names
        contaminated_names_list, contamination_details_dict = detect_contaminated_payer_names(crosswalk)
    except ImportError as e:
        # Fallback if helper module not available - skip contamination detection
        MediLink_ConfigLoader.log("Could not import contamination detection: {}".format(e), config=None, level="DEBUG")
    except Exception as e:
        # Fallback on any error - skip contamination detection
        MediLink_ConfigLoader.log("Error during contamination detection: {}".format(e), config=None, level="DEBUG")
    
    for payer_id, details in crosswalk['payer_id'].items():
        # Check if name is missing or "Unknown"
        name = details.get('name', '')
        if not name or name == 'Unknown':
            missing_names += 1
            missing_names_list.append(payer_id)

        # Check if at least one medisoft ID exists in either field
        medisoft_id = details.get('medisoft_id', [])
        medisoft_medicare_id = details.get('medisoft_medicare_id', [])

        # Convert to list if it's a set (for compatibility)
        if isinstance(medisoft_id, set):
            medisoft_id = list(medisoft_id)
        if isinstance(medisoft_medicare_id, set):
            medisoft_medicare_id = list(medisoft_medicare_id)

        # If both are empty, count as missing; if either has at least one, it's healthy
        if not medisoft_id and not medisoft_medicare_id:
            missing_medisoft_ids += 1
            missing_medisoft_ids_list.append(payer_id)

    # Consider healthy if no missing names, no missing medisoft IDs, and no contamination
    is_healthy = (missing_names == 0 and missing_medisoft_ids == 0 and len(contaminated_names_list) == 0)
    # Return contamination_details_dict as 7th element for use by caller (avoids re-detection)
    return is_healthy, missing_names, missing_medisoft_ids, missing_names_list, missing_medisoft_ids_list, contaminated_names_list, contamination_details_dict

def prompt_user_for_api_calls(crosswalk, config):
    """
    Prompt user with a short timeout to optionally run API validation when the crosswalk looks healthy.

    Implementation notes and rationale
    ----------------------------------
    A previous implementation attempted to capture a quick ENTER press using a background thread that
    called ``input()`` and then ``join(timeout=...)``. When the timeout elapsed, the thread often
    remained blocked inside ``input()``. That stray, still-waiting ``input()`` subsequently consumed
    the next ENTER the user typed at a later prompt (e.g., the Medicare question), producing a blank,
    unlabeled input step before the real prompt. This manifested as “press Enter once to get the next
    prompt,” which is undesirable and confusing.

    To avoid leaving a pending console read, this implementation uses Windows' non-blocking console
    polling (``msvcrt.kbhit()/getwch()``) for up to ~2 seconds to detect an ENTER press without ever
    invoking ``input()``. Non-ENTER keys are discarded to avoid leaking keystrokes into subsequent
    prompts. If ENTER is not pressed during the window, we skip API validation with no lingering input
    state.

    If threading must be used in future
    -----------------------------------
    Do not call ``input()`` in a background thread and leave it running after a timeout. Instead:
    - Use a worker thread that performs non-blocking polling (e.g., ``msvcrt.kbhit()/getwch()``) and
      sets a threading.Event when ENTER is detected.
    - The main thread waits on the Event with a timeout. On timeout, signal the worker to stop.
    - Before returning, drain any buffered keystrokes with a short loop while ``msvcrt.kbhit()`` to
      ensure no characters (including ENTER) carry over to the next prompt.
    - This avoids dangling reads and preserves a clean console state.

    Compatibility
    -------------
    - Targets Python 3.4.4 / Windows XP constraints; avoids ``selectors``/``select`` on stdin and
      avoids advanced console APIs. Falls back to a non-interactive skip on non-Windows platforms.

    Args:
        crosswalk (dict): The crosswalk dictionary to check.
        config (dict): Configuration settings for logging.

    Returns:
        bool: True to proceed with API calls; False to skip
    """
    
    is_healthy, missing_names, missing_medisoft_ids, missing_names_list, missing_medisoft_ids_list, contaminated_names_list, contamination_details_dict = check_crosswalk_health(crosswalk)
    total_payers = len(crosswalk.get('payer_id', {}))
    
    if is_healthy:
        print("\nCrosswalk appears healthy:")
        print("  - {} payers found".format(total_payers))
        print("  - All payers have names")
        print("  - All payers have medisoft IDs")
        print("  - No contaminated payer names detected")
        print("\nPress ENTER to run API validation, or wait 2 seconds to skip...")

        # Windows-safe, non-blocking ENTER detection without leaving a stray input() pending
        try:
            import os, time
            msvcrt = None
            if os.name == 'nt':
                try:
                    import msvcrt  # Windows-only
                except ImportError:
                    msvcrt = None

            if msvcrt is not None:
                start_time = time.time()
                pressed_enter = False
                # Consume keys for up to 2 seconds, act only if ENTER is hit
                while time.time() - start_time < 2.0:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch in ('\r', '\n'):
                            pressed_enter = True
                            break
                        # Discard any other keys so they don't leak into later prompts
                    time.sleep(0.01)

                if pressed_enter:
                    print("Running API validation calls...")
                    MediLink_ConfigLoader.log("User pressed ENTER - proceeding with API calls", config, level="INFO")
                    return True
                else:
                    print("Timed out - skipping API calls")
                    MediLink_ConfigLoader.log("Timeout - skipping API calls", config, level="INFO")
                    return False
            else:
                # Fallback for non-Windows: avoid interactive wait to prevent stdin conflicts
                print("(Skipping interactive API validation prompt on this platform)")
                MediLink_ConfigLoader.log("Skipped interactive API validation prompt (unsupported platform)", config, level="INFO")
                return False
        except Exception:
            # On any error, default to skipping to avoid dangling input states
            print("(Error during prompt; skipping API validation)")
            MediLink_ConfigLoader.log("Error during API validation prompt; skipping", config, level="WARNING")
            return False
    else:
        print("\nCrosswalk needs attention:")
        print("  - {} payers found".format(total_payers))
        
        # Import helper modules for comprehensive health check and cleaning
        try:
            from MediBot.MediBot_Crosswalk_Validation import (
                validate_crosswalk_json_structure,
                load_and_validate_crosswalk_json,
                detect_contaminated_payer_names
            )
            from MediBot.MediBot_Crosswalk_Cleaning import (
                preview_cleaning_actions,
                clean_contaminated_crosswalk
            )
            from MediBot.MediBot_Crosswalk_File_Utils import (
                open_crosswalk_file_for_editing
            )
            helpers_available = True
        except ImportError as e:
            helpers_available = False
            MediLink_ConfigLoader.log("Helper modules not available: {}".format(e), config, level="WARNING")
        
        # Show detailed information about contaminated names (use cached details from health check)
        if contaminated_names_list:
            print("  - {} payers with contaminated names (address data detected): {}".format(
                len(contaminated_names_list), ", ".join(contaminated_names_list)))
            # Display contamination details using cached dict from health check
            # Import constant for name truncation length
            try:
                from MediBot.MediBot_Crosswalk_Cleaning import MAX_NAME_DISPLAY_LENGTH
            except ImportError:
                MAX_NAME_DISPLAY_LENGTH = 50  # Fallback constant
            
            for payer_id in contaminated_names_list:
                if payer_id in contamination_details_dict:
                    reason = contamination_details_dict[payer_id]
                    name = crosswalk['payer_id'][payer_id].get('name', '')
                    display_name = name[:MAX_NAME_DISPLAY_LENGTH] + "..." if len(name) > MAX_NAME_DISPLAY_LENGTH else name
                    print("    {}: {} (reason: {})".format(payer_id, display_name, reason))
        
        # Show detailed information about missing names
        if missing_names > 0:
            print("  - {} payers missing names: {}".format(missing_names, ", ".join(missing_names_list)))
        
        # Show detailed information about missing medisoft IDs
        if missing_medisoft_ids > 0:
            print("  - {} payers missing medisoft IDs: {}".format(missing_medisoft_ids, ", ".join(missing_medisoft_ids_list)))
            # API validation CANNOT resolve missing medisoft IDs
            print("    TODO: Need user interface to manually input medisoft IDs for these payers")
        
        # Validate JSON structure if helpers available
        structure_errors = []
        if helpers_available:
            try:
                is_valid, structure_errors = validate_crosswalk_json_structure(crosswalk)
                if not is_valid:
                    print("  - JSON structure errors found: {} issue(s)".format(len(structure_errors)))
                    # Show first few errors
                    for error in structure_errors[:3]:
                        print("    - {}".format(error))
                    if len(structure_errors) > 3:
                        print("    ... and {} more error(s)".format(len(structure_errors) - 3))
            except Exception as e:
                # Log exception but continue (validation is non-critical for operation)
                MediLink_ConfigLoader.log("Error during JSON structure validation: {}".format(e), config, level="DEBUG")
        
        # Present interactive menu if issues found and helpers available
        if helpers_available and (contaminated_names_list or structure_errors):
            print("\nOptions to fix issues:")
            print("  1. Automatic cleaning (preview actions first)")
            print("  2. Open crosswalk file for manual editing")
            print("  3. Skip and continue (may cause issues)")
            
            while True:
                choice = input("\nEnter choice (1-3): ").strip()
                
                if choice == '1':
                    # Automatic cleaning
                    if contaminated_names_list:
                        # Preview cleaning actions
                        action_list, details_dict = preview_cleaning_actions(crosswalk, contaminated_names_list)
                        print("\nPreview of cleaning actions:")
                        for payer_id, action_type, description in action_list:
                            print("  - {}".format(description))
                        
                        confirm = input("\nProceed with automatic cleaning? (yes/no): ").strip().lower()
                        if confirm in ('yes', 'y'):
                            # Clean contaminated entries
                            client = None
                            try:
                                from MediCafe.api_core import APIClient
                                client = APIClient()
                            except Exception as e:
                                # Log failure but continue (client may not be needed)
                                MediLink_ConfigLoader.log("Could not create APIClient: {}".format(e), config, level="DEBUG")
                            
                            success = clean_contaminated_crosswalk(crosswalk, contaminated_names_list, config, client)
                            if success:
                                print("\nCleaning completed. Re-running health check...")
                                # Reload crosswalk from file and re-check
                                crosswalk_reloaded, is_valid, errors = load_and_validate_crosswalk_json(config)
                                if is_valid and crosswalk_reloaded:
                                    crosswalk = crosswalk_reloaded
                                    # Re-run health check
                                    return prompt_user_for_api_calls(crosswalk, config)
                                else:
                                    print("WARNING: Could not reload crosswalk after cleaning. Please verify manually.")
                                    MediLink_ConfigLoader.log("Could not reload crosswalk after cleaning", config, level="WARNING")
                        break
                    else:
                        print("No contaminated entries to clean.")
                        break
                
                elif choice == '2':
                    # Open file for manual editing
                    success, file_path, error_msg = open_crosswalk_file_for_editing(config)
                    if success:
                        print("\nCrosswalk file opened for editing: {}".format(file_path))
                        print("Please make your changes and save the file.")
                        input("\nPress ENTER after you have saved the file...")
                        
                        # Reload and validate crosswalk
                        print("\nReloading and validating crosswalk...")
                        crosswalk_reloaded, is_valid, errors = load_and_validate_crosswalk_json(config)
                        
                        if not is_valid:
                            print("\nERROR: Crosswalk file has issues after editing:")
                            for error in errors[:10]:  # Show first 10 errors
                                print("  - {}".format(error))
                            if len(errors) > 10:
                                print("  ... and {} more error(s)".format(len(errors) - 10))
                            
                            retry = input("\nFile has errors. Try editing again? (yes/no): ").strip().lower()
                            if retry in ('yes', 'y'):
                                continue  # Loop back to menu
                            else:
                                print("Continuing with potentially invalid crosswalk...")
                                break
                        else:
                            if crosswalk_reloaded:
                                crosswalk = crosswalk_reloaded
                                print("Crosswalk reloaded successfully. Re-running health check...")
                                # Re-run health check
                                return prompt_user_for_api_calls(crosswalk, config)
                            else:
                                print("WARNING: Could not reload crosswalk. Please verify file exists.")
                                break
                    else:
                        print("ERROR: Could not open crosswalk file: {}".format(error_msg))
                        break
                
                elif choice == '3':
                    # Skip
                    print("Skipping cleanup. Continuing with existing crosswalk...")
                    break
                
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
        
        # Only proceed with API calls if there are missing names (API can help with those)
        if missing_names > 0:
            print("\nProceeding with API validation calls to resolve missing names...")
            MediLink_ConfigLoader.log("Crosswalk has missing names - proceeding with API calls", config, level="INFO")
            return True
        else:
            print("\nNo missing names to resolve via API. Skipping API validation calls.")
            if missing_medisoft_ids > 0:
                print("TODO: Manual intervention needed for missing medisoft IDs")
            MediLink_ConfigLoader.log("Crosswalk has missing medisoft IDs but no missing names - skipping API calls", config, level="INFO")
            return False

# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================
# Functions for managing configuration settings, endpoint selection, and ensuring
# proper configuration loading across the crosswalk system.

def select_endpoint(config, current_endpoint=None):
    """
    Prompts the user to select an endpoint from the available options or returns the default endpoint.
    Validates the current endpoint against the available options.

    Args:
        config (dict): Configuration settings for logging. Can be either the full config or config['MediLink_Config'].
        current_endpoint (str, optional): The current endpoint to validate.

    Returns:
        str: The selected endpoint key.

    Raises:
        ValueError: If the config does not contain valid endpoint information.
    """
    # Determine the effective MediLink_Config
    if 'MediLink_Config' in config:
        medi_link_config = config['MediLink_Config']
        MediLink_ConfigLoader.log("Using 'MediLink_Config' from the provided configuration.", config, level="DEBUG")
    else:
        medi_link_config = config
        MediLink_ConfigLoader.log("Using the provided configuration directly as 'MediLink_Config'.", config, level="DEBUG")

    # Attempt to retrieve endpoint options
    try:
        endpoint_options = list(medi_link_config['endpoints'].keys())
        MediLink_ConfigLoader.log("Successfully retrieved endpoint options.", config, level="DEBUG")
    except KeyError:
        MediLink_ConfigLoader.log("Failed to retrieve endpoint options due to KeyError.", config, level="ERROR")
        raise ValueError("Invalid configuration: 'endpoints' not found in config.")
        

    # Ensure there are available endpoints
    if not endpoint_options:
        MediLink_ConfigLoader.log("No endpoints available in the configuration.", config, level="ERROR")
        raise ValueError("No endpoints available in the configuration.")
    else:
        MediLink_ConfigLoader.log("Available endpoints found in the configuration.", config, level="DEBUG")

    print("Available endpoints:")
    for idx, key in enumerate(endpoint_options):
        # Safely retrieve the endpoint name
        endpoint_name = medi_link_config['endpoints'].get(key, {}).get('name', key)
        print("{0}: {1}".format(idx + 1, endpoint_name))

    # Validate the current endpoint if provided
    if current_endpoint and current_endpoint not in endpoint_options:
        print("WARNING: The current endpoint '{}' is not valid.".format(current_endpoint))
        MediLink_ConfigLoader.log("Current endpoint '{}' is not valid. Prompting for selection.".format(current_endpoint), config, level="WARNING")

    user_choice = input("Select an endpoint by number (or press Enter to use the default): ").strip()

    if user_choice.isdigit() and 1 <= int(user_choice) <= len(endpoint_options):
        selected_endpoint = endpoint_options[int(user_choice) - 1]  # Use the key instead of the name
    else:
        selected_endpoint = endpoint_options[0]  # Default to the first key
        MediLink_ConfigLoader.log("User opted for default endpoint: " + selected_endpoint, config, level="INFO")

    return selected_endpoint

def ensure_full_config_loaded(config=None, crosswalk=None):
    """
    Ensures that the full base configuration and crosswalk are loaded.
    If the base config is not valid or the crosswalk is None, reloads them.
    
    Uses module-level caching to prevent redundant reloads and warnings.

    Args:
        config (dict, optional): The current configuration.
        crosswalk (dict, optional): The current crosswalk.

    Returns:
        tuple: The loaded base configuration and crosswalk.
    """
    global _cached_config, _cached_crosswalk
    
    MediLink_ConfigLoader.log("Ensuring full configuration and crosswalk are loaded.", level="DEBUG")

    # Reload configuration if necessary
    if config is None or 'MediLink_Config' not in config:
        # Check cache first
        if _cached_config is not None and 'MediLink_Config' in _cached_config:
            MediLink_ConfigLoader.log("Using cached configuration.", level="DEBUG")
            config = _cached_config
            # If crosswalk is also None, use cached crosswalk if available
            if crosswalk is None and _cached_crosswalk is not None:
                MediLink_ConfigLoader.log("Using cached crosswalk.", level="DEBUG")
                crosswalk = _cached_crosswalk
        else:
            MediLink_ConfigLoader.log("Base config is missing or invalid. Reloading configuration.", level="WARNING")
            config, loaded_crosswalk = MediLink_ConfigLoader.load_configuration()
            _cached_config = config
            # If crosswalk was None, use the loaded crosswalk
            if crosswalk is None:
                crosswalk = loaded_crosswalk
                _cached_crosswalk = crosswalk
            MediLink_ConfigLoader.log("Base configuration and crosswalk reloaded.", level="INFO")
    else:
        MediLink_ConfigLoader.log("Base config was correctly passed.", level="DEBUG")
        # Update cache with valid config
        _cached_config = config

    # Reload crosswalk if necessary (only if not already loaded above)
    if crosswalk is None:
        # Check MediCafe centralized cache first (Option C: leverage centralized cache)
        try:
            import MediCafe.MediLink_ConfigLoader as config_loader_module
            centralized_crosswalk = getattr(config_loader_module, '_CROSSWALK_CACHE', None)
            if centralized_crosswalk is not None:
                MediLink_ConfigLoader.log("Using MediCafe centralized crosswalk cache.", level="DEBUG")
                crosswalk = centralized_crosswalk
                _cached_crosswalk = crosswalk  # Update module cache for consistency
            else:
                # Check module-level cache second (Option A: reduce warning severity)
                if _cached_crosswalk is not None:
                    MediLink_ConfigLoader.log("Using module-level cached crosswalk.", level="DEBUG")
                    crosswalk = _cached_crosswalk
                else:
                    # Only log warning if we're actually reloading from disk (not using cache)
                    MediLink_ConfigLoader.log("Crosswalk is None. Reloading crosswalk from disk.", level="WARNING")
                    _, crosswalk = MediLink_ConfigLoader.load_configuration()  # Reloading to get the crosswalk
                    _cached_crosswalk = crosswalk
                    MediLink_ConfigLoader.log("Crosswalk reloaded from disk.", level="INFO")
        except (ImportError, AttributeError):
            # Fallback to module-level cache if centralized cache is not accessible
            if _cached_crosswalk is not None:
                MediLink_ConfigLoader.log("Using module-level cached crosswalk (centralized cache not available).", level="DEBUG")
                crosswalk = _cached_crosswalk
            else:
                # Only log warning if we're actually reloading from disk (not using cache)
                MediLink_ConfigLoader.log("Crosswalk is None. Reloading crosswalk from disk.", level="WARNING")
                _, crosswalk = MediLink_ConfigLoader.load_configuration()  # Reloading to get the crosswalk
                _cached_crosswalk = crosswalk
                MediLink_ConfigLoader.log("Crosswalk reloaded from disk.", level="INFO")
    else:
        # Update cache with valid crosswalk (Option B: pass crosswalk when available)
        _cached_crosswalk = crosswalk

    return config, crosswalk

# =============================================================================
# CROSSWALK PERSISTENCE AND STORAGE
# =============================================================================
# Functions for saving and managing crosswalk data persistence, including
# validation of crosswalk structure and proper JSON serialization.

def save_crosswalk(client, config, crosswalk, skip_api_operations=False, api_cache=None):
    """
    Saves the crosswalk to a JSON file. Ensures that all necessary keys are present and logs the outcome.
    
    Args:
        client (APIClient): API client for fetching payer names (ignored if skip_api_operations=True).
        config (dict): Configuration settings for logging.
        crosswalk (dict): The crosswalk dictionary to save.
        skip_api_operations (bool): If True, skips API calls and user prompts for faster saves.
        api_cache (dict, optional): Cache to prevent redundant API calls.
    
    Returns:
        bool: True if the crosswalk was saved successfully, False otherwise.
    """
    try:
        # Determine the path to save the crosswalk
        crosswalk_path = config['MediLink_Config']['crosswalkPath']
        MediLink_ConfigLoader.log("Determined crosswalk path: {}.".format(crosswalk_path), config, level="DEBUG")
    except KeyError:
        crosswalk_path = config.get('crosswalkPath', 'crosswalk.json')
        MediLink_ConfigLoader.log("Using default crosswalk path: {}.".format(crosswalk_path), config, level="DEBUG")
    
    # Validate endpoints for each payer ID in the crosswalk
    for payer_id, details in crosswalk.get('payer_id', {}).items():
        current_endpoint = details.get('endpoint', None)
        if current_endpoint and current_endpoint not in config['MediLink_Config']['endpoints']:
            if skip_api_operations:
                # Log warning but don't prompt user during API-bypass mode
                MediLink_ConfigLoader.log("WARNING: Invalid endpoint '{}' for payer ID '{}' - skipping correction due to API bypass mode".format(current_endpoint, payer_id), config, level="WARNING")
            else:
                print("WARNING: The current endpoint '{}' for payer ID '{}' is not valid.".format(current_endpoint, payer_id))
                MediLink_ConfigLoader.log("Current endpoint '{}' for payer ID '{}' is not valid. Prompting for selection.".format(current_endpoint, payer_id), config, level="WARNING")
                selected_endpoint = select_endpoint(config, current_endpoint)  # Prompt user to select a valid endpoint
                crosswalk['payer_id'][payer_id]['endpoint'] = selected_endpoint  # Update the endpoint in the crosswalk
                MediLink_ConfigLoader.log("Updated payer ID {} with new endpoint '{}'.".format(payer_id, selected_endpoint), config, level="INFO")
    
    try:
        # Log API bypass mode if enabled
        if skip_api_operations:
            MediLink_ConfigLoader.log("save_crosswalk running in API bypass mode - skipping API calls and user prompts", config, level="INFO")
        
        # Initialize the 'payer_id' key if it doesn't exist
        if 'payer_id' not in crosswalk: 
            print("save_crosswalk is initializing 'payer_id' key...")
            crosswalk['payer_id'] = {}
            MediLink_ConfigLoader.log("Initialized 'payer_id' key in crosswalk.", config, level="INFO")
        
        # Ensure all payer IDs have a name and initialize medisoft_id and medisoft_medicare_id as empty lists if they do not exist
        for payer_id in crosswalk['payer_id']:
            if 'name' not in crosswalk['payer_id'][payer_id]: 
                if skip_api_operations:
                    # Set placeholder name and log for MediBot to handle later
                    crosswalk['payer_id'][payer_id]['name'] = 'Unknown'
                    MediLink_ConfigLoader.log("Set placeholder name for payer ID {} - will be resolved by MediBot health check".format(payer_id), config, level="INFO")
                else:
                    # Note: fetch_and_store_payer_name is in the main library to avoid circular imports
                    # This function will be called from the main library's crosswalk_update process
                    MediLink_ConfigLoader.log("Payer ID {} will be processed by main library's fetch_and_store_payer_name function.".format(payer_id), config, level="DEBUG")
            
            # Check for the endpoint key
            if 'endpoint' not in crosswalk['payer_id'][payer_id]:
                if skip_api_operations:
                    # Set default endpoint and log
                    crosswalk['payer_id'][payer_id]['endpoint'] = 'AVAILITY'
                    MediLink_ConfigLoader.log("Set default endpoint for payer ID {} - can be adjusted via MediBot if needed".format(payer_id), config, level="INFO")
                else:
                    crosswalk['payer_id'][payer_id]['endpoint'] = select_endpoint(config)  # Use the helper function to set the endpoint
                    MediLink_ConfigLoader.log("Initialized 'endpoint' for payer ID {}.".format(payer_id), config, level="DEBUG")

        # Initialize medisoft_id and medisoft_medicare_id as empty lists if they do not exist
        crosswalk['payer_id'][payer_id].setdefault('medisoft_id', [])
        crosswalk['payer_id'][payer_id].setdefault('medisoft_medicare_id', []) # does this work in 3.4.4?
        MediLink_ConfigLoader.log("Ensured 'medisoft_id' and 'medisoft_medicare_id' for payer ID {} are initialized.".format(payer_id), config, level="DEBUG")
        # STRATEGIC NOTE (Crosswalk Validation): Medicare ID structure is ready for implementation
        # To enforce Medicare-specific handling, implement:
        # medicare_payer_ids = config.get('MediLink_Config', {}).get('cob_settings', {}).get('medicare_payer_ids', ['00850'])
        # if payer_id in medicare_payer_ids:
        #     # Enforce distinctness and add crossover_endpoint
        #     crosswalk['payer_id'][payer_id]['crossover_endpoint'] = 'MEDICARE_CROSSOVER'
        #     # Validate medisoft_medicare_id is distinct from medisoft_id
        #
        # IMPLEMENTATION QUESTIONS:
        # 1. Should Medicare ID validation be enforced strictly or with warnings?
        # 2. How should crossover endpoints be configured (per-payer or global)?
        # 3. Should distinctness between commercial and Medicare IDs be required or optional?
        
        # Convert sets to sorted lists for JSON serialization
        for payer_id, details in crosswalk.get('payer_id', {}).items():
            if isinstance(details.get('medisoft_id'), set): 
                crosswalk['payer_id'][payer_id]['medisoft_id'] = sorted(list(details['medisoft_id']))
                MediLink_ConfigLoader.log("Converted medisoft_id for payer ID {} to sorted list.".format(payer_id), config, level="DEBUG")
            if isinstance(details.get('medisoft_medicare_id'), set): 
                crosswalk['payer_id'][payer_id]['medisoft_medicare_id'] = sorted(list(details['medisoft_medicare_id']))
                MediLink_ConfigLoader.log("Converted medisoft_medicare_id for payer ID {} to sorted list.".format(payer_id), config, level="DEBUG")
        
        # Write the crosswalk to the specified file
        with open(crosswalk_path, 'w') as file:
            json.dump(crosswalk, file, indent=4)
        
        MediLink_ConfigLoader.log(
            "Crosswalk saved successfully to {}.".format(crosswalk_path),
            config,
            level="INFO"
        )
        print("Crosswalk saved successfully to {}.".format(crosswalk_path))
        return True
    except KeyError as e:
        print("Key Error: A required key is missing in the crosswalk data - {}.".format(e))
        MediLink_ConfigLoader.log("Key Error while saving crosswalk: {}.".format(e), config, level="ERROR")
        return False
    except TypeError as e:
        print("Type Error: There was a type issue with the data being saved in the crosswalk - {}.".format(e))
        MediLink_ConfigLoader.log("Type Error while saving crosswalk: {}.".format(e), config, level="ERROR")
        return False
    except IOError as e:
        print("I/O Error: An error occurred while writing to the crosswalk file - {}.".format(e))
        MediLink_ConfigLoader.log("I/O Error while saving crosswalk: {}.".format(e), config, level="ERROR")
        return False
    except Exception as e:
        print("Unexpected crosswalk error: {}.".format(e))
        MediLink_ConfigLoader.log("Unexpected error while saving crosswalk: {}.".format(e), config, level="ERROR")
        return False

# =============================================================================
# CROSSWALK UPDATE OPERATIONS
# =============================================================================
# Functions for updating crosswalk data with new or corrected payer information,
# including handling of payer ID corrections and new payer additions.

def update_crosswalk_with_corrected_payer_id(client, old_payer_id, corrected_payer_id, config=None, crosswalk=None, api_cache=None): 
    """
    Updates the crosswalk by replacing an old payer ID with a corrected payer ID.
    
    Args:
        old_payer_id (str): The old payer ID to be replaced.
        corrected_payer_id (str): The new payer ID to replace the old one.
        config (dict, optional): Configuration settings for logging.
        crosswalk (dict, optional): The crosswalk dictionary to update.
        api_cache (dict, optional): Cache to prevent redundant API calls.
    
    Returns:
        bool: True if the crosswalk was updated successfully, False otherwise.
    """
    # Ensure full configuration and crosswalk are loaded
    config, crosswalk = ensure_full_config_loaded(config, crosswalk)
        
    # Convert to a regular dict if crosswalk['payer_id'] is an OrderedDict
    if isinstance(crosswalk['payer_id'], dict) and hasattr(crosswalk['payer_id'], 'items'):
        crosswalk['payer_id'] = dict(crosswalk['payer_id'])
    
    MediLink_ConfigLoader.log("Checking if old Payer ID {} exists in crosswalk.".format(old_payer_id), config, level="DEBUG")
    
    MediLink_ConfigLoader.log("Attempting to replace old Payer ID {} with corrected Payer ID {}.".format(old_payer_id, corrected_payer_id), config, level="DEBUG")
        
    # Check if the old payer ID exists before attempting to replace
    if old_payer_id in crosswalk['payer_id']:
        MediLink_ConfigLoader.log("Old Payer ID {} found. Proceeding with replacement.".format(old_payer_id), config, level="DEBUG")
            
        # Store the details of the old payer ID
        old_payer_details = crosswalk['payer_id'][old_payer_id]
        MediLink_ConfigLoader.log("Storing details of old Payer ID {}: {}".format(old_payer_id, old_payer_details), config, level="DEBUG")
        
        # Replace the old payer ID with the corrected one
        crosswalk['payer_id'][corrected_payer_id] = old_payer_details
        MediLink_ConfigLoader.log("Replaced old Payer ID {} with corrected Payer ID {}.".format(old_payer_id, corrected_payer_id), config, level="INFO")
        
        # Remove the old payer ID from the crosswalk
        del crosswalk['payer_id'][old_payer_id]
        MediLink_ConfigLoader.log("Removed old Payer ID {} from crosswalk.".format(old_payer_id), config, level="DEBUG")
    
        # Note: fetch_and_store_payer_name is in the main library to avoid circular imports
        # The payer name will be fetched during the next crosswalk update process
        MediLink_ConfigLoader.log("Corrected Payer ID {} added to crosswalk - name will be fetched during next update.".format(corrected_payer_id), config, level="INFO")
        
        # Update csv_replacements
        crosswalk.setdefault('csv_replacements', {})[old_payer_id] = corrected_payer_id
        MediLink_ConfigLoader.log("Updated csv_replacements: {} -> {}.".format(old_payer_id, corrected_payer_id), config, level="INFO")
        print("csv_replacements updated: '{}' -> '{}'.".format(old_payer_id, corrected_payer_id))
        
        return save_crosswalk(client, config, crosswalk, api_cache=api_cache)
    else:
        MediLink_ConfigLoader.log("Failed to update crosswalk: old Payer ID {} not found.".format(old_payer_id), config, level="ERROR")
        print("Failed to update crosswalk: could not find old Payer ID '{}'.".format(old_payer_id))
        return False

def update_crosswalk_with_new_payer_id(client, insurance_name, payer_id, config, crosswalk, api_cache=None): 
    """
    Updates the crosswalk with a new payer ID for a given insurance name.
    
    Args:
        insurance_name (str): The name of the insurance to associate with the new payer ID.
        payer_id (str): The new payer ID to be added.
        config (dict): Configuration settings for logging.
        crosswalk (dict): The crosswalk dictionary to update.
        api_cache (dict, optional): Cache to prevent redundant API calls.
    """
    # Ensure full configuration and crosswalk are loaded
    config, crosswalk = ensure_full_config_loaded(config, crosswalk)
    
    try:
        # Check if 'payer_id' is present in the crosswalk
        if 'payer_id' not in crosswalk or not crosswalk['payer_id']:
            # Reload the crosswalk if 'payer_id' is missing or empty
            _, crosswalk = MediLink_ConfigLoader.load_configuration(None, config.get('crosswalkPath', 'crosswalk.json'))
            MediLink_ConfigLoader.log("Reloaded crosswalk configuration from {}.".format(config.get('crosswalkPath', 'crosswalk.json')), config, level="DEBUG")
    except KeyError as e:  # Handle KeyError for crosswalk
        MediLink_ConfigLoader.log("KeyError while checking or reloading crosswalk: {}".format(e), config, level="ERROR")
        print("KeyError while checking or reloading crosswalk in update_crosswalk_with_new_payer_id: {}".format(e))
        return False
    except Exception as e:
        MediLink_ConfigLoader.log("Error while checking or reloading crosswalk: {}".format(e), config, level="ERROR")
        print("Error while checking or reloading crosswalk in update_crosswalk_with_new_payer_id: {}".format(e))
        return False
    
    # Load the Medisoft ID for the given insurance name
    # XP/Python34 Compatibility: Enhanced error handling with verbose output
    try:
        # Note: MediBot_Preprocessor_lib is imported at module level
        if MediBot_Preprocessor_lib and hasattr(MediBot_Preprocessor_lib, 'load_insurance_data_from_mains'):
            insurance_data = MediBot_Preprocessor_lib.load_insurance_data_from_mains(config)
            medisoft_id = insurance_data.get(insurance_name) if insurance_data else None
            MediLink_ConfigLoader.log("Successfully retrieved insurance data for {}".format(insurance_name), config, level="DEBUG")
        else:
            error_msg = "MediBot_Preprocessor_lib or load_insurance_data_from_mains not available"
            MediLink_ConfigLoader.log(error_msg, config, level="WARNING")
            print("Warning: {}".format(error_msg))
            medisoft_id = None
    except AttributeError as e:
        error_msg = "AttributeError accessing load_insurance_data_from_mains: {}".format(str(e))
        MediLink_ConfigLoader.log(error_msg, config, level="WARNING")
        print("Warning: {}".format(error_msg))
        medisoft_id = None
    except KeyError as e:  # Handle KeyError for config
        MediLink_ConfigLoader.log("KeyError while loading Medisoft ID: {}".format(e), config, level="ERROR")
        print("KeyError while loading Medisoft ID for insurance name {}: {}".format(insurance_name, e))
        return False
    except Exception as e:
        error_msg = "Unexpected error loading insurance data: {}".format(str(e))
        MediLink_ConfigLoader.log(error_msg, config, level="ERROR")
        print("Error: {}".format(error_msg))
        medisoft_id = None

    MediLink_ConfigLoader.log("Retrieved Medisoft ID for insurance name {}: {}.".format(insurance_name, medisoft_id), config, level="DEBUG")
    
    if medisoft_id:
        medisoft_id_str = str(medisoft_id)
        MediLink_ConfigLoader.log("Processing to update crosswalk with new payer ID: {} for insurance name: {}.".format(payer_id, insurance_name), config, level="DEBUG")
        
        # Validate payer ID format before adding to crosswalk
        try:
            from MediLink.MediLink_837p_utilities import is_valid_payer_id_format
            # Check for test mode to avoid interactive prompts in non-interactive contexts
            is_test_mode = False
            try:
                from MediLink.MediLink_837p_encoder_library import _is_test_mode
                is_test_mode = _is_test_mode(config)
            except (ImportError, AttributeError):
                pass
            
            if not is_valid_payer_id_format(payer_id):
                warning_msg = "WARNING: Payer ID '{}' does not match expected format (should be 3-10 alphanumeric characters) for insurance '{}'.".format(payer_id, insurance_name)
                print(warning_msg)
                MediLink_ConfigLoader.log(warning_msg, config, level="WARNING")
                # In test mode, automatically proceed with warning (no user input)
                if is_test_mode:
                    MediLink_ConfigLoader.log("[TEST MODE] Proceeding with invalid format payer ID '{}' (non-interactive mode)".format(payer_id), config, level="WARNING")
                    print("TEST MODE: Proceeding with invalid format payer ID '{}' (non-interactive mode)".format(payer_id))
                else:
                    # Warn user but allow them to proceed (similar to prompt_user_for_payer_id behavior)
                    proceed = input("Do you want to proceed with adding this payer ID to the crosswalk anyway? (yes/no): ").strip().lower()
                    if proceed not in ('yes', 'y'):
                        print("Cancelled adding payer ID '{}' to crosswalk.".format(payer_id))
                        MediLink_ConfigLoader.log("User cancelled adding invalid format payer ID '{}' to crosswalk.".format(payer_id), config, level="INFO")
                        return False
        except ImportError:
            # If import fails, skip validation but log warning
            MediLink_ConfigLoader.log("Could not import is_valid_payer_id_format - skipping format validation for payer ID '{}'.".format(payer_id), config, level="WARNING")
        
        # Initialize the payer ID entry if it doesn't exist
        if payer_id not in crosswalk['payer_id']:
            selected_endpoint = select_endpoint(config)  # Use the helper function to select the endpoint

            # Ensure the 'payer_id' key exists in the crosswalk
            crosswalk['payer_id'][payer_id] = {
                'endpoint': selected_endpoint,
                'medisoft_id': [],  # PERFORMANCE FIX: Use list instead of set to avoid conversions
                'medisoft_medicare_id': []
            }
            MediLink_ConfigLoader.log("Initialized payer ID {} in crosswalk with endpoint '{}'.".format(payer_id, selected_endpoint), config, level="DEBUG")
        else:
            # Check if the existing endpoint is valid
            current_endpoint = crosswalk['payer_id'][payer_id].get('endpoint', None)
            if current_endpoint and current_endpoint not in config['MediLink_Config']['endpoints']:
                print("WARNING: The current endpoint '{}' for payer ID '{}' is not valid.".format(current_endpoint, payer_id))
                MediLink_ConfigLoader.log("Current endpoint '{}' for payer ID '{}' is not valid. Prompting for selection.".format(current_endpoint, payer_id), config, level="WARNING")
                selected_endpoint = select_endpoint(config, current_endpoint)  # Prompt user to select a valid endpoint
                crosswalk['payer_id'][payer_id]['endpoint'] = selected_endpoint  # Update the endpoint in the crosswalk
                MediLink_ConfigLoader.log("Updated payer ID {} with new endpoint '{}'.".format(payer_id, selected_endpoint), config, level="INFO")
            else:
                selected_endpoint = current_endpoint  # Use the existing valid endpoint

        # Add the insurance ID to the payer ID entry - with error handling for the .add() operation
        try:
            if not isinstance(crosswalk['payer_id'][payer_id]['medisoft_id'], set):
                # Convert to set if it's not already one
                crosswalk['payer_id'][payer_id]['medisoft_id'] = set(crosswalk['payer_id'][payer_id]['medisoft_id'])
                MediLink_ConfigLoader.log("Converted medisoft_id to set for payer ID {}.".format(payer_id), config, level="DEBUG")
            
            crosswalk['payer_id'][payer_id]['medisoft_id'].add(str(medisoft_id_str)) # Ensure IDs are strings
            MediLink_ConfigLoader.log(
                "Added new insurance ID {} to payer ID {}.".format(medisoft_id_str, payer_id),
                config,
                level="INFO"
            )
        except AttributeError as e:
            MediLink_ConfigLoader.log("AttributeError while adding medisoft_id: {}".format(e), config, level="ERROR")
            print("Error adding medisoft_id for payer ID {}: {}".format(payer_id, e))
            return False
        
        # Note: fetch_and_store_payer_name is in the main library to avoid circular imports
        # The payer name will be fetched during the next crosswalk update process
        MediLink_ConfigLoader.log("Added new payer ID {} for insurance name {} - name will be fetched during next update.".format(payer_id, insurance_name), config, level="INFO")
        
        # Save the updated crosswalk
        save_crosswalk(client, config, crosswalk, api_cache=api_cache)
        MediLink_ConfigLoader.log("Crosswalk saved successfully after updating payer ID {}.".format(payer_id), config, level="DEBUG")
    else:
        message = "Failed to update crosswalk: Medisoft ID not found for insurance name {}.".format(insurance_name)
        print(message)
        MediLink_ConfigLoader.log(message, config, level="ERROR")

# =============================================================================
# DATA PARSING AND PROCESSING
# =============================================================================
# Functions for parsing and processing external data sources, including
# Z data files and other data formats used by the crosswalk system.

def load_and_parse_z_data(config):
    """
    Loads and parses Z data for patient to insurance name mappings from the specified directory.
    
    Args:
        config (dict): Configuration settings for logging.
    
    Returns:
        tuple: (dict, str) - A tuple containing:
            - dict: A mapping of patient IDs to insurance names
            - str: Status indicating the result type:
                - "success_with_data": Successfully parsed with data
                - "success_no_new_files": Successfully processed but no new files found
                - "success_empty_files": Successfully processed but files contained no valid data
                - "error": An error occurred during processing
    """
    patient_id_to_insurance_name = {}
    files_processed = 0
    files_with_data = 0
    
    try:
        z_dat_path = config['MediLink_Config']['Z_DAT_PATH']
        MediLink_ConfigLoader.log("Z_DAT_PATH is set to: {}".format(z_dat_path), config, level="DEBUG")
        
        # Get the directory of the Z_DAT_PATH
        directory = os.path.dirname(z_dat_path)
        MediLink_ConfigLoader.log("Looking for .DAT files in directory: {}".format(directory), config, level="DEBUG")
        
        # List all .DAT files in the directory, case insensitive
        dat_files = [f for f in os.listdir(directory) if f.lower().endswith('.dat')]
        MediLink_ConfigLoader.log("Found {} .DAT files in the directory.".format(len(dat_files)), config, level="DEBUG")
        
        # Load processed files tracking
        processed_files_path = os.path.join(directory, 'processed_files.txt')
        if os.path.exists(processed_files_path):
            with open(processed_files_path, 'r') as f:
                processed_files = set(line.strip() for line in f)
            MediLink_ConfigLoader.log("Loaded processed files: {}.".format(processed_files), config, level="DEBUG")
        else:
            processed_files = set()
            MediLink_ConfigLoader.log("No processed files found, starting fresh.", config, level="DEBUG")

        # Filter for new .DAT files that haven't been processed yet, but always include Z.DAT and ZM.DAT
        new_dat_files = [f for f in dat_files if f not in processed_files or f.lower() in ['z.dat', 'zm.dat']]
        MediLink_ConfigLoader.log("Identified {} new .DAT files to process.".format(len(new_dat_files)), config, level="INFO")

        if not new_dat_files:
            MediLink_ConfigLoader.log("No new .DAT files to process.", config, level="INFO")
            return {}, "success_no_new_files"

        for dat_file in new_dat_files:
            file_path = os.path.join(directory, dat_file)
            MediLink_ConfigLoader.log("Parsing .DAT file: {}".format(file_path), config, level="DEBUG")
            
            # Parse each .DAT file and accumulate results
            # Note: MediBot_Preprocessor_lib is imported at module level
            insurance_name_mapping = MediBot_Preprocessor_lib.parse_z_dat(file_path, config['MediLink_Config'])
            files_processed += 1
            
            if insurance_name_mapping:  # Ensure insurance_name_mapping is not empty
                patient_id_to_insurance_name.update(insurance_name_mapping)
                files_with_data += 1
                MediLink_ConfigLoader.log("File {} contained {} mappings.".format(dat_file, len(insurance_name_mapping)), config, level="DEBUG")

            # Mark this file as processed
            with open(processed_files_path, 'a') as f:
                f.write(dat_file + '\n')
            MediLink_ConfigLoader.log("Marked file as processed: {}".format(dat_file), config, level="DEBUG")

        # Determine the result status
        if patient_id_to_insurance_name:
            MediLink_ConfigLoader.log("Successfully parsed Z data with {} mappings found from {} files.".format(
                len(patient_id_to_insurance_name), files_with_data), config, level="INFO")
            return patient_id_to_insurance_name, "success_with_data"
        elif files_processed > 0:
            MediLink_ConfigLoader.log("Processed {} files but found no valid data mappings.".format(files_processed), config, level="INFO")
            return {}, "success_empty_files"
        else:
            MediLink_ConfigLoader.log("No files were processed.", config, level="WARNING")
            return {}, "error"
            
    except Exception as e:
        MediLink_ConfigLoader.log("Error loading and parsing Z data: {}".format(e), config, level="ERROR")
        return {}, "error" 