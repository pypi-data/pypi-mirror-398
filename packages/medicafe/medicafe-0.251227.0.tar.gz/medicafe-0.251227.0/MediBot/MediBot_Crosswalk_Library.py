# MediBot_Crosswalk_Library.py
"""
Core crosswalk library for MediBot
Handles crosswalk operations and API interactions.
"""

import sys

# Use core utilities for standardized imports
from MediCafe.core_utils import (
    import_medibot_module,
    get_config_loader_with_fallback,
    smart_import
)

# Initialize configuration loader with fallback
MediLink_ConfigLoader = get_config_loader_with_fallback()

# Import MediBot modules using centralized import functions
MediBot_Preprocessor_lib = import_medibot_module('MediBot_Preprocessor_lib')

# Import utility functions from MediBot_Crosswalk_Utils.py using centralized import
MediBot_Crosswalk_Utils = import_medibot_module('MediBot_Crosswalk_Utils')
if MediBot_Crosswalk_Utils:
    check_crosswalk_health = getattr(MediBot_Crosswalk_Utils, 'check_crosswalk_health', None)
    prompt_user_for_api_calls = getattr(MediBot_Crosswalk_Utils, 'prompt_user_for_api_calls', None)
    select_endpoint = getattr(MediBot_Crosswalk_Utils, 'select_endpoint', None)
    ensure_full_config_loaded = getattr(MediBot_Crosswalk_Utils, 'ensure_full_config_loaded', None)
    save_crosswalk = getattr(MediBot_Crosswalk_Utils, 'save_crosswalk', None)
    update_crosswalk_with_corrected_payer_id = getattr(MediBot_Crosswalk_Utils, 'update_crosswalk_with_corrected_payer_id', None)
    update_crosswalk_with_new_payer_id = getattr(MediBot_Crosswalk_Utils, 'update_crosswalk_with_new_payer_id', None)
    load_and_parse_z_data = getattr(MediBot_Crosswalk_Utils, 'load_and_parse_z_data', None)
else:
    # Set all functions to None if import fails completely
    check_crosswalk_health = None
    prompt_user_for_api_calls = None
    select_endpoint = None
    ensure_full_config_loaded = None
    save_crosswalk = None
    update_crosswalk_with_corrected_payer_id = None
    update_crosswalk_with_new_payer_id = None
    load_and_parse_z_data = None

# Import API functions using centralized import pattern
MediLink_API_v3 = smart_import(['MediCafe.api_core'])
fetch_payer_name_from_api = getattr(MediLink_API_v3, 'fetch_payer_name_from_api', None) if MediLink_API_v3 else None

# Module-level cache to prevent redundant API calls
_api_cache = {}

"""
# RESOLVED: Redundant API calls have been eliminated through module-level caching.
# The _api_cache prevents duplicate API calls for the same payer_id within a session.
"""

# =============================================================================
# CORE CROSSWALK OPERATIONS - Main Library Functions
# =============================================================================
# These functions handle the primary crosswalk operations and are kept in the main
# library because they are frequently called and contain the core business logic.
# Utility functions have been moved to MediBot_Crosswalk_Utils.py to reduce
# the main library size and improve maintainability.

def fetch_and_store_payer_name(client, payer_id, crosswalk, config, api_cache=None):
    """
    Fetches the payer name for a given payer ID and stores it in the crosswalk.
    Now with optional API cache to prevent redundant calls.
    
    Args:
        payer_id (str): The ID of the payer to fetch.
        crosswalk (dict): The crosswalk dictionary to store the payer name.
        config (dict): Configuration settings for logging.
        api_cache (dict, optional): Cache to prevent redundant API calls. Uses module-level cache if None.

    Returns:
        bool: True if the payer name was fetched and stored successfully, False otherwise.
    """
    global _api_cache
    
    # Use provided cache or module-level cache
    if api_cache is None:
        api_cache = _api_cache
    
    # Check if we already have this payer_id in cache
    if payer_id in api_cache:
        payer_name = api_cache[payer_id]
        MediLink_ConfigLoader.log("Using cached payer name for Payer ID: {}".format(payer_id), config, level="DEBUG")
    else:
        MediLink_ConfigLoader.log("Attempting to fetch payer name for Payer ID: {}".format(payer_id), config, level="DEBUG")
        try:
            # Fetch the payer name from the API
            payer_name = fetch_payer_name_from_api(client, payer_id, config, primary_endpoint=None)
            # Cache the result
            api_cache[payer_id] = payer_name
            MediLink_ConfigLoader.log("Fetched and cached payer name: {} for Payer ID: {}".format(payer_name, payer_id), config, level="DEBUG")
        except Exception as e:
            # Log any errors encountered during the fetching process
            MediLink_ConfigLoader.log("Failed to fetch name for Payer ID {}: {}".format(payer_id, e), config, level="WARNING")
            payer_name = "Unknown"
            api_cache[payer_id] = payer_name
            return False
        
        # Ensure the 'payer_id' key exists in the crosswalk
        if 'payer_id' not in crosswalk: 
            crosswalk['payer_id'] = {}
            MediLink_ConfigLoader.log("Initialized 'payer_id' in crosswalk.", config, level="DEBUG")
        
        # Initialize the payer ID entry if it doesn't exist
        if payer_id not in crosswalk['payer_id']:
            crosswalk['payer_id'][payer_id] = {}  # Initialize the entry
            MediLink_ConfigLoader.log("Initialized entry for Payer ID: {}".format(payer_id), config, level="DEBUG")
        
        # Store the fetched payer name in the crosswalk
        crosswalk['payer_id'][payer_id]['name'] = payer_name
        message = "Payer ID {} ({}) fetched and stored successfully.".format(payer_id, payer_name)
        MediLink_ConfigLoader.log(message, config, level="INFO")
        print(message)
        return True

def validate_and_correct_payer_ids(client, crosswalk, config, auto_correct=False, api_cache=None):
    """
    Validates and corrects payer IDs in the crosswalk. If a payer ID is invalid, it prompts the user for correction.
    
    Args:
        crosswalk (dict): The crosswalk dictionary containing payer IDs.
        config (dict): Configuration settings for logging.
        auto_correct (bool): If True, automatically corrects invalid payer IDs to 'Unknown'.
        api_cache (dict, optional): Cache to prevent redundant API calls.
    """
    processed_payer_ids = set()  # Track processed payer IDs
    payer_ids = list(crosswalk.get('payer_id', {}).keys())  # Static list to prevent modification issues
    
    for payer_id in payer_ids:
        if payer_id in processed_payer_ids:
            continue  # Skip already processed payer IDs
        
        # Validate the payer ID by fetching its name
        is_valid = fetch_and_store_payer_name(client, payer_id, crosswalk, config, api_cache)
        
        if not is_valid:
            if auto_correct:
                # Automatically correct invalid payer IDs to 'Unknown'
                crosswalk['payer_id'][payer_id]['name'] = "Unknown"
                MediLink_ConfigLoader.log(
                    "Auto-corrected Payer ID {} to 'Unknown'.".format(payer_id),
                    config,
                    level="WARNING"
                )
                print("Auto-corrected Payer ID '{}' to 'Unknown'.".format(payer_id))
                processed_payer_ids.add(payer_id)
                continue
            
            # Prompt the user for a corrected payer ID
            current_name = crosswalk['payer_id'].get(payer_id, {}).get('name', 'Unknown')
            corrected_payer_id = input(
                "WARNING: Invalid Payer ID {} ({}).\n"
                "Enter the correct Payer ID for replacement or type 'FORCE' to continue with the unresolved Payer ID: ".format(
                    payer_id, current_name)
            ).strip()
            
            if corrected_payer_id.lower() == 'force':
                # Assign "Unknown" and log the action
                crosswalk['payer_id'][payer_id]['name'] = "Unknown"
                MediLink_ConfigLoader.log(
                    "User forced unresolved Payer ID {} to remain as 'Unknown'.".format(payer_id),
                    config,
                    level="WARNING"
                )
                print("Payer ID '{}' has been marked as 'Unknown'.".format(payer_id))
                processed_payer_ids.add(payer_id)
                continue
            
            if corrected_payer_id:
                # Validate format and warn if invalid, but allow user to proceed
                try:
                    from MediLink.MediLink_837p_utilities import is_valid_payer_id_format
                    if not is_valid_payer_id_format(corrected_payer_id):
                        print("WARNING: The entered payer ID '{}' does not match the expected format (should be 3-10 alphanumeric characters).".format(corrected_payer_id))
                        confirm = input("Do you want to proceed with this payer ID anyway? (yes/no): ").strip().lower()
                        if confirm not in ('yes', 'y'):
                            MediLink_ConfigLoader.log(
                                "User cancelled entry of invalid payer ID format: {}".format(corrected_payer_id),
                                config,
                                level="INFO"
                            )
                            print("Please try again with a corrected payer ID.")
                            continue
                except ImportError:
                    # If import fails, skip format validation but log for awareness
                    MediLink_ConfigLoader.log(
                        "Could not import is_valid_payer_id_format - skipping format validation for corrected payer ID",
                        config,
                        level="DEBUG"
                    )
                # Validate the corrected payer ID
                if fetch_and_store_payer_name(client, corrected_payer_id, crosswalk, config, api_cache):
                    # Replace the old payer ID with the corrected one in the crosswalk
                    success = update_crosswalk_with_corrected_payer_id(client, payer_id, corrected_payer_id, config, crosswalk, api_cache)
                    if success:
                        print("Payer ID '{}' has been successfully replaced with '{}'.".format(
                            payer_id, corrected_payer_id))
                        processed_payer_ids.add(corrected_payer_id)
                else:
                    # Only set to "Unknown" if the corrected payer ID is not valid
                    crosswalk['payer_id'][corrected_payer_id] = {'name': "Unknown"}
                    MediLink_ConfigLoader.log(
                        "Failed to validate corrected Payer ID {}. Set to 'Unknown'.".format(corrected_payer_id),
                        config,
                        level="ERROR"
                    )
                    print("Payer ID '{}' has been added with name 'Unknown'.".format(corrected_payer_id))
                    processed_payer_ids.add(corrected_payer_id)
            else:
                MediLink_ConfigLoader.log(
                    "No correction provided for Payer ID {}. Skipping.".format(payer_id),
                    config,
                    level="WARNING"
                )
                print("No correction provided for Payer ID '{}'. Skipping.".format(payer_id))

def initialize_crosswalk_from_mapat(client, config, crosswalk):
    """
    Initializes the crosswalk from the MAPAT data source. Loads configuration and data sources, 
    validates payer IDs, and saves the crosswalk.
    
    Returns:
        dict: The payer ID mappings from the initialized crosswalk.
    """
    # Ensure full configuration and crosswalk are loaded
    config, crosswalk = ensure_full_config_loaded(config, crosswalk)
    
    try:
        # Load data sources for patient and payer IDs
        patient_id_to_insurance_id, payer_id_to_patient_ids = MediBot_Preprocessor_lib.load_data_sources(config, crosswalk)
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    # Map payer IDs to insurance IDs
    payer_id_to_details = MediBot_Preprocessor_lib.map_payer_ids_to_insurance_ids(patient_id_to_insurance_id, payer_id_to_patient_ids)
    crosswalk['payer_id'] = payer_id_to_details
    
    # Validate and correct payer IDs in the crosswalk
    validate_and_correct_payer_ids(client, crosswalk, config)
    
    # Save the crosswalk and log the result
    if save_crosswalk(client, config, crosswalk):
        message = "Crosswalk initialized with mappings for {} payers.".format(len(crosswalk.get('payer_id', {})))
        print(message)
        MediLink_ConfigLoader.log(message, config, level="INFO")
    else:
        print("Failed to save the crosswalk.")
        sys.exit(1)
    
    return crosswalk['payer_id']


# =============================================================================
# MAIN CROSSWALK UPDATE FUNCTION
# =============================================================================

def crosswalk_update(client, config, crosswalk): # Upstream of this is only MediBot_Preprocessor.py and MediBot.py
    """
    Updates the crosswalk with insurance data and historical mappings. 
    It loads insurance data, historical payer mappings, and updates the crosswalk accordingly.
    
    Args:
        config (dict): Configuration settings for logging.
        crosswalk (dict): The crosswalk dictionary to update.
    
    Returns:
        bool: True if the crosswalk was updated successfully, False otherwise.
    """
    MediLink_ConfigLoader.log("Starting crosswalk update process...", config, level="INFO")

    # Initialize API cache for this session to prevent redundant calls
    api_cache = {}

    # Load insurance data from MAINS (optional - continue if not available)
    # XP/Python34 Compatibility: Enhanced error handling with verbose output
    insurance_name_to_id = {}
    try:
        MediLink_ConfigLoader.log("Attempting to load insurance data from MAINS...", config, level="DEBUG")
        
        if MediBot_Preprocessor_lib and hasattr(MediBot_Preprocessor_lib, 'load_insurance_data_from_mains'):
            insurance_name_to_id = MediBot_Preprocessor_lib.load_insurance_data_from_mains(config)
            if insurance_name_to_id:
                MediLink_ConfigLoader.log("Loaded insurance data from MAINS with {} entries.".format(len(insurance_name_to_id)), config, level="INFO")
            else:
                MediLink_ConfigLoader.log("load_insurance_data_from_mains returned empty data", config, level="WARNING")
        else:
            error_msg = "MediBot_Preprocessor_lib or load_insurance_data_from_mains not available"
            MediLink_ConfigLoader.log(error_msg, config, level="WARNING")
            print("Warning: {}".format(error_msg))
            
    except AttributeError as e:
        error_msg = "AttributeError accessing load_insurance_data_from_mains: {}".format(str(e))
        MediLink_ConfigLoader.log(error_msg, config, level="WARNING")
        print("Warning: {}. Some crosswalk features may be limited.".format(error_msg))
    except ImportError as e:
        error_msg = "ImportError with MediBot_Preprocessor_lib: {}".format(str(e))
        MediLink_ConfigLoader.log(error_msg, config, level="WARNING")
        print("Warning: {}. Some crosswalk features may be limited.".format(error_msg))
    except Exception as e:
        MediLink_ConfigLoader.log("Error loading insurance data from MAINS: {}. Continuing without MAINS data.".format(e), config, level="WARNING")
        print("Warning: MAINS data not available ({}). Some crosswalk features may be limited.".format(str(e)))
        # Continue without MAINS data - don't return False

    # Load historical payer to patient mappings (optional - continue if not available)
    patient_id_to_payer_id = {}
    try:
        MediLink_ConfigLoader.log("Attempting to load historical payer to patient mappings...", config, level="DEBUG")
        patient_id_to_payer_id = MediBot_Preprocessor_lib.load_historical_payer_to_patient_mappings(config)
        MediLink_ConfigLoader.log("Loaded historical mappings with {} entries.".format(len(patient_id_to_payer_id)), config, level="INFO")
    except Exception as e:
        MediLink_ConfigLoader.log("Error loading historical mappings: {}. Continuing without historical data.".format(e), config, level="WARNING")
        print("Warning: Historical mappings not available. Some crosswalk features may be limited.")
        # Continue without historical data - don't return False

    # Parse Z data for patient to insurance name mappings
    try:
        patient_id_to_insurance_name, z_data_status = load_and_parse_z_data(config)
        mapping_count = len(patient_id_to_insurance_name) if patient_id_to_insurance_name is not None else 0
        MediLink_ConfigLoader.log("Parsed Z data with {} mappings found. Status: {}".format(mapping_count, z_data_status), config, level="INFO")
        
        # Handle different Z data statuses
        if z_data_status == "error":
            MediLink_ConfigLoader.log("Error occurred during Z data parsing.", config, level="ERROR")
            return False
        elif z_data_status == "success_no_new_files":
            MediLink_ConfigLoader.log("No new Z data files to process - this is normal if all files have been processed.", config, level="INFO")
            # Continue with crosswalk update even if no new Z data
        elif z_data_status == "success_empty_files":
            MediLink_ConfigLoader.log("Z data files were processed but contained no valid mappings - this may indicate empty or malformed files.", config, level="WARNING")
            # Continue with crosswalk update even if Z data is empty
        elif z_data_status == "success_with_data":
            MediLink_ConfigLoader.log("Successfully processed Z data with new mappings.", config, level="INFO")
            # Normal case - continue with crosswalk update
    except Exception as e:
        MediLink_ConfigLoader.log("Error parsing Z data in crosswalk update: {}".format(e), config, level="ERROR")
        return False

    # Check if 'payer_id' key exists and is not empty
    MediLink_ConfigLoader.log("Checking for 'payer_id' key in crosswalk...", config, level="DEBUG")
    if 'payer_id' not in crosswalk or not crosswalk['payer_id']:
        MediLink_ConfigLoader.log("The 'payer_id' list is empty or missing.", config, level="WARNING")
        user_input = input(
            "The 'payer_id' list is empty or missing. Would you like to initialize the crosswalk? (yes/no): "
        ).strip().lower()
        if user_input in ['yes', 'y']:
            MediLink_ConfigLoader.log("User chose to initialize the crosswalk.", config, level="INFO")
            initialize_crosswalk_from_mapat(client, config, crosswalk)
            return True  # Indicate that the crosswalk was initialized
        else:
            MediLink_ConfigLoader.log("User opted not to initialize the crosswalk.", config, level="WARNING")
            return False  # Indicate that the update was not completed

    # NEW: Check if we should skip API calls based on crosswalk health
    if not prompt_user_for_api_calls(crosswalk, config):
        print("Skipping crosswalk API validation - using existing data")
        MediLink_ConfigLoader.log("Skipped crosswalk API validation per user choice", config, level="INFO")
        return True

    # Continue with existing crosswalk update logic...
    # Update the crosswalk with new payer IDs and insurance IDs
    for patient_id, payer_id in patient_id_to_payer_id.items():
        insurance_name = patient_id_to_insurance_name.get(patient_id)
        if insurance_name and insurance_name in insurance_name_to_id:
            insurance_id = insurance_name_to_id[insurance_name]
           
            # Log the assembly of data
            MediLink_ConfigLoader.log("Assembling data for patient_id '{}': payer_id '{}', insurance_name '{}', insurance_id '{}'.".format(
                patient_id, payer_id, insurance_name, insurance_id), config, level="INFO")
            # Ensure the 'payer_id' key exists in the crosswalk
            if 'payer_id' not in crosswalk:
                crosswalk['payer_id'] = {}
                MediLink_ConfigLoader.log("Initialized 'payer_id' in crosswalk.", config, level="DEBUG")

            # Initialize the payer ID entry if it doesn't exist
            if payer_id not in crosswalk['payer_id']:
                # Prompt the user to select an endpoint name or use the default
                endpoint_options = list(config['MediLink_Config']['endpoints'].keys())
                print("Available endpoints:")
                for idx, key in enumerate(endpoint_options):
                    print("{0}: {1}".format(idx + 1, config['MediLink_Config']['endpoints'][key]['name']))
                user_choice = input("Select an endpoint by number (or press Enter to use the default): ").strip()

                if user_choice.isdigit() and 1 <= int(user_choice) <= len(endpoint_options):
                    selected_endpoint = config['MediLink_Config']['endpoints'][endpoint_options[int(user_choice) - 1]]['name']
                else:
                    selected_endpoint = config['MediLink_Config']['endpoints'][endpoint_options[0]]['name']
                    MediLink_ConfigLoader.log("User opted for default endpoint: {}".format(selected_endpoint), config, level="INFO")

                crosswalk['payer_id'][payer_id] = {
                    'endpoint': selected_endpoint,
                    'medisoft_id': [],  # PERFORMANCE FIX: Use list instead of set to avoid conversions
                    'medisoft_medicare_id': []  # PERFORMANCE FIX: Use list instead of set to avoid conversions
                }
                MediLink_ConfigLoader.log("Initialized payer ID {} in crosswalk with endpoint '{}'.".format(payer_id, selected_endpoint), config, level="DEBUG")
                # STRATEGIC NOTE (Medicare Endpoint Routing): Medicare detection logic exists
                # To activate Medicare-specific routing, implement:
                # try:
                #     medicare_payer_ids = config.get('MediLink_Config', {}).get('cob_settings', {}).get('medicare_payer_ids', ['00850'])
                #     if payer_id in medicare_payer_ids or 'MEDICARE' in payer_id.upper():
                #         selected_endpoint = 'MEDICARE_PRIMARY'
                #         crosswalk['payer_id'][payer_id]['crossover_endpoint'] = 'MEDICARE_CROSSOVER'
                # except Exception as e:
                #     MediLink_ConfigLoader.log("Medicare endpoint routing error: {}".format(str(e)), level="WARNING")
                #
                # IMPLEMENTATION QUESTIONS:
                # 1. Should Medicare routing be automatic or require manual confirmation?
                # 2. How should Medicare Advantage plans be routed differently from traditional Medicare?
                # 3. Should crossover endpoints be configured per payer or globally?
                # 4. What fallback behavior when Medicare-specific endpoints are unavailable?

            # Add the insurance ID to the payer ID entry (PERFORMANCE FIX: Use list operations)
            insurance_id_str = str(insurance_id)  # Ensure ID is string
            if insurance_id_str not in crosswalk['payer_id'][payer_id]['medisoft_id']:
                crosswalk['payer_id'][payer_id]['medisoft_id'].append(insurance_id_str)  # Avoid duplicates
            MediLink_ConfigLoader.log(
                "Added new insurance ID {} to payer ID {}.".format(insurance_id, payer_id),
                config,
                level="INFO"
            )

            # Log the update of the crosswalk
            MediLink_ConfigLoader.log("Updated crosswalk for payer_id '{}': added insurance_id '{}'.".format(payer_id, insurance_id), config, level="DEBUG")

            # Fetch and store the payer name
            MediLink_ConfigLoader.log("Fetching and storing payer name for payer_id: {}".format(payer_id), config, level="DEBUG")
            fetch_and_store_payer_name(client, payer_id, crosswalk, config, api_cache)
            MediLink_ConfigLoader.log("Successfully fetched and stored payer name for payer_id: {}".format(payer_id), config, level="INFO")

    # Validate and correct payer IDs in the crosswalk
    MediLink_ConfigLoader.log("Validating and correcting payer IDs in the crosswalk.", config, level="DEBUG")
    validate_and_correct_payer_ids(client, crosswalk, config, api_cache=api_cache)

    # Check for any entries marked as "Unknown" and validate them
    unknown_payers = [
        payer_id for payer_id, details in crosswalk.get('payer_id', {}).items()
        if details.get('name') == "Unknown"
    ]
    MediLink_ConfigLoader.log("Found {} unknown payer(s) to validate.".format(len(unknown_payers)), config, level="INFO")
    for payer_id in unknown_payers:
        MediLink_ConfigLoader.log("Fetching and storing payer name for unknown payer_id: {}".format(payer_id), config, level="DEBUG")
        fetch_and_store_payer_name(client, payer_id, crosswalk, config, api_cache)
        MediLink_ConfigLoader.log("Successfully fetched and stored payer name for unknown payer_id: {}".format(payer_id), config, level="INFO")

    # PERFORMANCE FIX: Optimized list management - avoid redundant set/list conversions
    # Ensure multiple medisoft_id values are preserved and deduplicated efficiently
    for payer_id, details in crosswalk.get('payer_id', {}).items():
        # Handle medisoft_id - convert sets to lists or deduplicate existing lists
        medisoft_id = details.get('medisoft_id', [])
        if isinstance(medisoft_id, set):
            crosswalk['payer_id'][payer_id]['medisoft_id'] = sorted(list(medisoft_id))
            MediLink_ConfigLoader.log("Converted medisoft_id set to sorted list for payer ID {}.".format(payer_id), config, level="DEBUG")
        elif isinstance(medisoft_id, list) and medisoft_id:
            # Remove duplicates using dict.fromkeys() - preserves order, O(n) performance
            crosswalk['payer_id'][payer_id]['medisoft_id'] = list(dict.fromkeys(medisoft_id))
        
        # Handle medisoft_medicare_id - convert sets to lists or deduplicate existing lists  
        medicare_id = details.get('medisoft_medicare_id', [])
        if isinstance(medicare_id, set):
            crosswalk['payer_id'][payer_id]['medisoft_medicare_id'] = sorted(list(medicare_id))
            MediLink_ConfigLoader.log("Converted medisoft_medicare_id set to sorted list for payer ID {}.".format(payer_id), config, level="DEBUG")
        elif isinstance(medicare_id, list) and medicare_id:
            # Remove duplicates using dict.fromkeys() - preserves order, O(n) performance
            crosswalk['payer_id'][payer_id]['medisoft_medicare_id'] = list(dict.fromkeys(medicare_id))

    MediLink_ConfigLoader.log("Crosswalk update process completed. Processed {} payer IDs.".format(len(patient_id_to_payer_id)), config, level="INFO")
    return save_crosswalk(client, config, crosswalk, api_cache=api_cache)





