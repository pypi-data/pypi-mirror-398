# MediLink_837p_utilities.py
"""
837P Encoder Utility Functions

This module contains utility functions extracted from MediLink_837p_encoder_library.py
to reduce the size and complexity of the main encoder library while avoiding circular imports.

Functions included:
- Date/time formatting utilities
- User interaction utilities  
- File/path handling utilities
- Processing utilities
- Validation utilities
- Insurance matching utilities
- EDI segment utilities

Import Strategy:
This module only imports base Python modules and MediLink_ConfigLoader to avoid 
circular dependencies. Other modules import from this utilities module.
"""

from datetime import datetime
import sys, os, difflib

# Import MediLink_ConfigLoader for logging functionality
from MediCafe.core_utils import get_shared_config_loader
MediLink_ConfigLoader = get_shared_config_loader()

# =============================================================================
# DATE/TIME UTILITIES
# =============================================================================

def convert_date_format(date_str):
    """
    Converts date format from one format to another.
    
    Parameters:
    - date_str: Date string in MM-DD-YYYY or MM-DD-YY format
    
    Returns:
    - Date string in YYYYMMDD format
    """
    # Parse the input date string into a datetime object using the input format    
    # Determine the input date format based on the length of the input string
    input_format = "%m-%d-%Y" if len(date_str) == 10 else "%m-%d-%y"
    date_obj = datetime.strptime(date_str, input_format)
    # Format the datetime object into the desired output format and return
    return date_obj.strftime("%Y%m%d")

def format_datetime(dt=None, format_type='date'):
    """
    Formats date and time according to the specified format.
    
    Parameters:
    - dt: datetime object (defaults to current datetime if None)
    - format_type: 'date', 'isa', or 'time'
    
    Returns:
    - Formatted date/time string
    """
    if dt is None:
        dt = datetime.now()
    if format_type == 'date':
        return dt.strftime('%Y%m%d')
    elif format_type == 'isa':
        return dt.strftime('%y%m%d')
    elif format_type == 'time':
        return dt.strftime('%H%M')

# =============================================================================
# USER INTERACTION UTILITIES
# =============================================================================

def get_user_confirmation(prompt_message):
    """
    Prompts user for yes/no confirmation with validation.
    
    Parameters:
    - prompt_message: Message to display to user
    
    Returns:
    - Boolean: True for yes, False for no
    """
    while True:
        response = input(prompt_message).strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please respond with 'yes' or 'no'.")

def is_valid_payer_id_format(payer_id):
    """
    Validates that a payer ID conforms to expected format.
    
    Payer IDs should be:
    - 3-10 characters long (typically 5 digits)
    - Numeric or alphanumeric only
    - No punctuation, spaces, or special characters
    
    Args:
        payer_id (str): Payer ID to validate
        
    Returns:
        bool: True if format is valid, False otherwise
    """
    if not isinstance(payer_id, str):
        return False
    
    payer_id = payer_id.strip()
    
    if not payer_id:
        return False
    
    # Validate: reasonable length (payer IDs are short)
    if not (3 <= len(payer_id) <= 10):
        return False
    
    # Validate: numeric or alphanumeric only (no punctuation/spaces)
    if not payer_id.isalnum():
        return False
    
    return True

def prompt_user_for_payer_id(insurance_name):
    """
    Prompts the user to input the payer ID manually. Warns user if format is invalid 
    but allows them to proceed anyway.
    
    Parameters:
    - insurance_name: Name of the insurance for context
    
    Returns:
    - Payer ID (may be invalid format if user chooses to proceed)
    """
    while True:
        print("Manual intervention required: No payer ID found for insurance name '{}'.".format(insurance_name))
        payer_id = input("Please enter the payer ID manually: ").strip()
        
        if not payer_id:
            print("Error: Payer ID cannot be empty. Please try again.")
            continue
        
        # Check if format is valid
        if is_valid_payer_id_format(payer_id):
            return payer_id
        else:
            # Warn user but allow them to proceed
            print("WARNING: This payer ID does not match the expected format (should be 3-10 alphanumeric characters).")
            confirm = input("Do you want to proceed anyway? (yes/no): ").strip().lower()
            if confirm in ('yes', 'y'):
                return payer_id
            else:
                print("Please try again.")

# =============================================================================
# FILE/PATH UTILITIES
# =============================================================================

def format_claim_number(chart_number, date_of_service):
    """
    Formats claim number by combining chart number and date of service.
    
    Parameters:
    - chart_number: Patient chart number
    - date_of_service: Date of service
    
    Returns:
    - Formatted claim number (alphanumeric only)
    """
    # Remove any non-alphanumeric characters from chart number and date
    chart_number_alphanumeric = ''.join(filter(str.isalnum, chart_number))
    date_of_service_alphanumeric = ''.join(filter(str.isalnum, date_of_service))
    
    # Combine the alphanumeric components without spaces
    formatted_claim_number = chart_number_alphanumeric + date_of_service_alphanumeric
    
    return formatted_claim_number

def winscp_validate_output_directory(output_directory):
    """
    Validates the output directory path to ensure it has no spaces.
    If spaces are found, prompts the user to input a new path.
    If the directory doesn't exist, creates it.
    
    Parameters:
    - output_directory: Directory path to validate
    
    Returns:
    - Validated directory path
    """
    while ' ' in output_directory:
        print("\nWARNING: The output directory path contains spaces, which can cause issues with upload operations.")
        print("    Current proposed path: {}".format(output_directory))
        new_path = input("Please enter a new path for the output directory: ")
        output_directory = new_path.strip()  # Remove leading/trailing spaces
    
    # Check if the directory exists, if not, create it
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print("INFO: Created output directory: {}".format(output_directory))
    
    return output_directory

def get_output_directory(config):
    """
    Retrieves and validates output directory from configuration.
    
    Parameters:
    - config: Configuration dictionary
    
    Returns:
    - Valid output directory path or None if invalid
    """
    # Retrieve desired default output file path from config 
    output_directory = config.get('outputFilePath', '').strip()
    # BUG (Low SFTP) Add WinSCP validation because of the mishandling of spaces in paths. (This shouldn't need to exist.)
    if not output_directory:
        print("Output file path is not specified in the configuration.")
        output_directory = input("Please enter a valid output directory path: ").strip()
    
    # Validate the directory path (checks for spaces and existence)
    # XP/WinSCP PATH NOTE:
    # - WinSCP CLI can be finicky with paths containing spaces on Windows XP.
    # - Prefer quoting paths at the call-site constructing WinSCP commands and avoid trailing slashes.
    # - Where possible, prefer short 8.3 paths or pre-create target directories.
    # - This function only validates; quoting is applied in MediLink_DataMgmt.build_command() for lcd/put.
    output_directory = winscp_validate_output_directory(output_directory)
    
    if not os.path.isdir(output_directory):
        print("Output directory does not exist or is not accessible. Please check the configuration.")
        return None
    
    return output_directory

# =============================================================================
# PROCESSING UTILITIES
# =============================================================================

def generate_segment_counts(compiled_segments, transaction_set_control_number):
    """
    Generates segment counts for the formatted 837P transaction and updates SE segment.
    
    Parameters:
    - compiled_segments: String containing compiled 837P segments
    - transaction_set_control_number: Transaction set control number
    
    Returns:
    - Formatted 837P string with correct SE segment
    """
    # Count the number of segments, not including the placeholder SE segment
    segment_count = compiled_segments.count('~')   # + 1 Including SE segment itself, but seems to be giving errors.
    
    # Ensure transaction set control number is correctly formatted as a string
    formatted_control_number = str(transaction_set_control_number).zfill(4)  # Pad to ensure minimum 4 characters

    # Construct the SE segment with the actual segment count and the formatted transaction set control_number
    se_segment = "SE*{0}*{1}~".format(segment_count, formatted_control_number)

    # Assuming the placeholder SE segment was the last segment added before compiling
    # This time, we directly replace the placeholder with the correct SE segment
    formatted_837p = compiled_segments.rsplit('SE**', 1)[0] + se_segment
    
    return formatted_837p

# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def handle_validation_errors(transaction_set_control_number, validation_errors, config):
    """
    Handles validation errors with user interaction for decision making.
    
    Parameters:
    - transaction_set_control_number: Current transaction set control number
    - validation_errors: List of validation errors
    - config: Configuration for logging
    
    Returns:
    - Boolean: True to skip patient, False to halt processing
    """
    for error in validation_errors:
        MediLink_ConfigLoader.log("Validation error for transaction set {}: {}".format(transaction_set_control_number, error), config, level="WARNING")
    
    print("Validation errors encountered for transaction set {}. Errors: {}".format(transaction_set_control_number, validation_errors))
    user_input = input("Skip this patient and continue without incrementing transaction set number? (yes/no): ")
    if user_input.lower() == 'yes':
        print("Skipping patient...")
        MediLink_ConfigLoader.log("Skipped processing of transaction set {} due to user decision.".format(transaction_set_control_number), config, level="INFO")
        return True  # Skip the current patient
    else:
        print("Processing halted due to validation errors.")
        MediLink_ConfigLoader.log("HALT: Processing halted at transaction set {} due to unresolved validation errors.".format(transaction_set_control_number), config, level="ERROR")
        sys.exit()  # Optionally halt further processing

# =============================================================================
# INSURANCE MATCHING UTILITIES
# =============================================================================

def find_closest_insurance_matches(insurance_name, insurance_to_id, max_matches=3):
    """
    Find the closest matches for an insurance name in the MAINS data.
    
    Args:
        insurance_name (str): The insurance name to find matches for
        insurance_to_id (dict): Dictionary mapping insurance names to IDs from MAINS
        max_matches (int): Maximum number of matches to return
        
    Returns:
        list: List of tuples (insurance_name, similarity_score) sorted by similarity
    """
    if not insurance_to_id:
        return []
    
    # Normalize the search term
    normalized_search = insurance_name.upper().strip()
    
    # Calculate similarity scores for all insurance names
    matches = []
    for mains_insurance_name in insurance_to_id.keys():
        normalized_mains = mains_insurance_name.upper().strip()
        
        # Use difflib for similarity scoring
        similarity = difflib.SequenceMatcher(None, normalized_search, normalized_mains).ratio()
        
        # Boost score for partial matches
        if normalized_search in normalized_mains or normalized_mains in normalized_search:
            similarity += 0.2
        
        # Boost score for word matches
        search_words = set(normalized_search.split())
        mains_words = set(normalized_mains.split())
        word_overlap = len(search_words.intersection(mains_words))
        if word_overlap > 0:
            similarity += 0.1 * word_overlap
        
        matches.append((mains_insurance_name, similarity))
    
    # Sort by similarity score (highest first) and return top matches
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:max_matches]

def prompt_for_insurance_selection(insurance_name, closest_matches, config):
    """
    Prompt the user to select from the closest matches or choose manual intervention.
    
    Args:
        insurance_name (str): The original insurance name that wasn't found
        closest_matches (list): List of tuples (insurance_name, similarity_score)
        config (dict): Configuration object
        
    Returns:
        str or None: Selected insurance name or None for manual intervention
    """
    print("\n" + "="*60)
    print("INSURANCE NAME NOT FOUND IN MAINS")
    print("="*60)
    print("Original insurance name: '{}'".format(insurance_name))
    print("\nClosest matches found in MAINS:")
    print("-" * 40)
    
    for i, (match_name, similarity) in enumerate(closest_matches, 1):
        print("{}. {} (similarity: {:.1%})".format(i, match_name, similarity))
    
    print("\n{}. None of these - I need to fix this manually".format(len(closest_matches) + 1))
    print("-" * 40)
    
    while True:
        try:
            choice = input("\nPlease select an option (1-{}): ".format(len(closest_matches) + 1))
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(closest_matches):
                selected_name = closest_matches[choice_num - 1][0]
                print("\nSelected: '{}'".format(selected_name))
                MediLink_ConfigLoader.log("User selected insurance name '{}' for original '{}'".format(selected_name, insurance_name), config, level="INFO")
                return selected_name
            elif choice_num == len(closest_matches) + 1:
                print("\n" + "="*60)
                print("MANUAL INTERVENTION REQUIRED")
                print("="*60)
                print("To resolve this issue, you may need to:")
                print("1. Check if the insurance name is spelled correctly in your source data")
                print("2. Verify the insurance exists in MAINS with a different name")
                print("3. Add the insurance to MAINS if it's missing")
                print("4. Update the crosswalk with the correct payer ID mapping")
                print("\nThe process will continue with other claims, but this claim will be skipped.")
                print("="*60)
                MediLink_ConfigLoader.log("User chose manual intervention for insurance name '{}'".format(insurance_name), config, level="WARNING")
                return None
            else:
                print("Invalid choice. Please enter a number between 1 and {}.".format(len(closest_matches) + 1))
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nProcess interrupted by user.")
            return None

# =============================================================================
# EDI SEGMENT UTILITIES
# =============================================================================

def build_nm1_segment(payer_name, payer_id):
    """
    Build NM1 segment using payer name and ID.
    
    Args:
        payer_name (str): Name of the payer
        payer_id (str): Payer ID
        
    Returns:
        str: Formatted NM1 segment
    """
    return "NM1*PR*2*{}*****PI*{}~".format(payer_name, payer_id)

# =============================================================================
# UTILITY FUNCTION REGISTRY
# =============================================================================

# Export all utility functions for easy importing
__all__ = [
    'convert_date_format',
    'format_datetime', 
    'get_user_confirmation',
    'is_valid_payer_id_format',
    'prompt_user_for_payer_id',
    'format_claim_number',
    'winscp_validate_output_directory', 
    'get_output_directory',
    'generate_segment_counts',
    'handle_validation_errors',
    'find_closest_insurance_matches',
    'prompt_for_insurance_selection',
    'build_nm1_segment'
] 