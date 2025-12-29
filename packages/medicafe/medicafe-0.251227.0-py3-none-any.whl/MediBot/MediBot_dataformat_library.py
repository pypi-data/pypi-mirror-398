# MediBot_dataformat_library.py
"""
Data formatting library for MediBot
Contains functions for formatting various data types and handling CSV operations.
"""

import os
import sys
import re
from datetime import datetime

# Add parent directory and current directory to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
current_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Use core utilities for standardized imports
from MediCafe.core_utils import (
    import_medibot_module,
    get_shared_config_loader,
    create_config_cache
)

# Initialize configuration loader - CRITICAL: This module requires MediLink_ConfigLoader
MediLink_ConfigLoader = get_shared_config_loader()
if MediLink_ConfigLoader is None:
    raise ImportError(
        "[MediBot_dataformat_library] CRITICAL: MediLink_ConfigLoader module import failed. "
        "This module requires MediLink_ConfigLoader to function. "
        "Check PYTHONPATH, module dependencies, and ensure MediCafe package is properly installed."
    )

# Import MediBot modules using centralized import functions
MediBot_Preprocessor_lib = import_medibot_module('MediBot_Preprocessor_lib')
if MediBot_Preprocessor_lib:
    open_csv_for_editing = getattr(MediBot_Preprocessor_lib, 'open_csv_for_editing', None)
    initialize = getattr(MediBot_Preprocessor_lib, 'initialize', None)
else:
    open_csv_for_editing = None
    initialize = None

MediBot_UI = import_medibot_module('MediBot_UI')
if MediBot_UI:
    manage_script_pause = getattr(MediBot_UI, 'manage_script_pause', None)
    app_control = getattr(MediBot_UI, 'app_control', None)
    get_app_control = getattr(MediBot_UI, '_get_app_control', None)
    def _ac():
        try:
            return get_app_control() if get_app_control else getattr(MediBot_UI, 'app_control', None)
        except Exception:
            return getattr(MediBot_UI, 'app_control', None)
else:
    manage_script_pause = None
    app_control = None

# Configuration will be loaded when needed
_get_config, (_config_cache, _crosswalk_cache) = create_config_cache()

# Initialize constants when needed
_initialized = False

def _ensure_initialized():
    """Ensure initialization has been done."""
    global _initialized
    if not _initialized:
        config, _ = _get_config()
        initialize(config)
        _initialized = True

# Format Data
def format_name(value):  
    if ',' in value:
        comma_count = value.count(',')
        if comma_count > 1:
            MediLink_ConfigLoader.log("Error: Multiple commas found in name value: {value}", level="ERROR")
            # Keep only the first comma and remove the rest
            first_comma_index = value.find(',')
            value = value[:first_comma_index + 1] + value[first_comma_index + 1:].replace(',', '')
        return value
    
    hyphenated_name_pattern = r'(?P<First>[\w-]+)\s+(?P<Middle>[\w-]?)\s+(?P<Last>[\w-]+)'
    match = re.match(hyphenated_name_pattern, value)
    if match:
        first_name = match.group('First')
        middle_name = match.group('Middle') or ''
        if len(middle_name) > 1:
            middle_name = middle_name[0]  # take only the first character
        last_name = match.group('Last')
        return '{}, {} {}'.format(last_name, first_name, middle_name).strip()
    parts = value.split()
    return '{}, {}'.format(parts[-1], ' '.join(parts[:-1]))

def format_date(value):
    try:
        date_obj = datetime.strptime(value, '%m/%d/%Y')
        return date_obj.strftime('%m%d%Y')
    except ValueError as e:
        print("Date format error:", e)
        return value

def format_phone(value):
    digits = ''.join(filter(str.isdigit, value))
    if len(digits) == 10:
        return digits
    print("Phone number format error: Invalid number of digits")
    return value

def format_policy(value):
    alphanumeric = ''.join(filter(str.isalnum, value))
    return alphanumeric

def format_gender(value):
    return value[0].upper()

def enforce_significant_length(output):
    # Replace spaces with a placeholder that counts as one significant digit
    temp_output = output.replace('{Space}', ' ')
    
    # Check if the number of significant digits exceeds 30
    if len(temp_output) > 30:
        
        # First line of defense: Replace ' APT ' or ' UNIT ' with ' #' if the original length is longer than 30 characters.
        temp_output = temp_output.replace(' APT ', ' #').replace(' UNIT ', ' #')
        
        # PERFORMANCE FIX: Remove spaces in a controlled manner from right to left if still too long
        # Cache length calculation to avoid repeated calls
        temp_length = len(temp_output)
        while temp_length > 30:
            # Find the last space
            last_space_index = temp_output.rfind(' ')
            if last_space_index == -1:
                break
            # Remove the last space
            temp_output = temp_output[:last_space_index] + temp_output[last_space_index+7:]
            temp_length = len(temp_output)  # Update cached length

        # If still greater than 30, truncate to 30 characters
        if len(temp_output) > 30:
            temp_output = temp_output[:30]

    # Replace placeholder back with actual space for final return
    return temp_output.replace(' ', '{Space}')

def format_street(value, csv_data, reverse_mapping, parsed_address_components):
    _ensure_initialized()
    # Temporarily disable script pause status
    if _ac():
        _ac().set_pause_status(False)
    
    # Remove period characters.
    value = value.replace('.', '')
    
    # Proceed only if there's a comma, indicating a likely full address
    if ',' in value:
        try:
            MediLink_ConfigLoader.log("Attempting to resolve address via regex...")
            # Retrieve common city names from configuration and prepare a regex pattern
            config, _ = _get_config()
            common_cities = config.get('cities', [])
            city_pattern = '|'.join(re.escape(city) for city in common_cities)
            city_regex_pattern = r'(?P<City>{})'.format(city_pattern)
            city_regex = re.compile(city_regex_pattern, re.IGNORECASE)

            # Search for a common city in the address
            city_match = city_regex.search(value)
                    
            if city_match:
                # Extract city name and partition the value around it
                city = city_match.group('City').upper()
                street, _, remainder = value.partition(city)
                
                # Regex pattern to find state and zip code in the remainder
                address_pattern = r',\s*(?P<State>[A-Z]{2})\s*(?P<Zip>\d{5}(?:-\d{4})?)?'
                match = re.search(address_pattern, remainder)

                if match:
                    # Update parsed address components
                    parsed_address_components['City'] = city
                    parsed_address_components['State'] = match.group('State')
                    parsed_address_components['Zip Code'] = match.group('Zip')
                    # Return formatted street address, enforcing significant length
                    return enforce_significant_length(street.strip())
            else:
                # Fallback regex for parsing addresses without a common city
                address_pattern = r'(?P<Street>[\w\s]+),?\s+(?P<City>[\w\s]+),\s*(?P<State>[A-Z]{2})\s*(?P<Zip>\d{5}(-\d{4})?)'
                match = re.match(address_pattern, value)

                if match:
                    # Update parsed address components
                    parsed_address_components['City'] = match.group('City')
                    parsed_address_components['State'] = match.group('State')
                    parsed_address_components['Zip Code'] = match.group('Zip')
                    # Return formatted street address, enforcing significant length
                    return enforce_significant_length(match.group('Street').strip())
                    
        except Exception as e:
            # Handle exceptions by logging and offering to correct data manually
            print("Address format error: Unable to parse address '{}'. Error: {}".format(value, e))
            if _ac():
                _ac().set_pause_status(True)
            if MediBot_Preprocessor_lib and hasattr(MediBot_Preprocessor_lib, 'CSV_FILE_PATH'):
                open_csv_for_editing(MediBot_Preprocessor_lib.CSV_FILE_PATH)
            else:
                open_csv_for_editing('')
            manage_script_pause(csv_data, e, reverse_mapping)
            # Return original value with spaces formatted, enforcing significant length
            return enforce_significant_length(value.replace(' ', '{Space}'))
    else:
        # If no comma is present, treat the input as a simple street name
        formatted_value = value.replace(' ', '{Space}')
        enforced_format = enforce_significant_length(formatted_value)
        return enforced_format

    # Fallback return in case no address components are matched even though a comma was present
    return enforce_significant_length(value.replace(' ', '{Space}')) 

def format_zip(value):
    # Ensure the value is a string, in case it's provided as an integer
    value_str = str(value)
    # Return only the first 5 characters of the zip code
    # TODO Future, they might start using 9 digit zip codes but we don't know what format they'll use yet. 
    return value_str[:5]

def format_data(medisoft_field, value, csv_data, reverse_mapping, parsed_address_components):
    formatters = {
        'Patient Name': format_name,
        'Birth Date': format_date,
        'Phone': format_phone,
        'Phone #2': format_phone,
        'Gender': format_gender,
        'Street': lambda v: format_street(v, csv_data, reverse_mapping, parsed_address_components),
        'Zip Code': format_zip,
        'Primary Policy Number': format_policy,
        'Secondary Policy Number': format_policy,
        'Primary Group Number': format_policy,
        'Secondary Group Number': format_policy
    }

    formatted_value = formatters.get(medisoft_field, str)(value)  # Default to str if not found
    formatted_value = formatted_value.replace(',', '{,}').replace(' ', '{Space}')
    
    ahk_command = 'SendInput, {}{{Enter}}'.format(formatted_value)
    return ahk_command