# MediBot_Preprocessor_lib.py
"""
Core preprocessing library for MediBot
Contains core preprocessing functions and utilities.
"""

import csv
import os
import re
import sys
import time
from collections import OrderedDict
from datetime import datetime, timedelta

# Try to import chardet for encoding detection
try:
    import chardet
except ImportError:
    chardet = None  # Fallback if chardet is not available

# SORTING STRATEGY CONFIGURATION
# Set to 'schedule_based' to enable surgery schedule sorting
# Set to 'date_based' to use current date-based sorting (default)
SORTING_STRATEGY = 'date_based'  # Hard-coded with clear comments

# When enabled, patients will be sorted based on their position in the DOCX surgery schedule
# When disabled, patients will be sorted by earliest surgery date (current behavior)

# Constants
DEFAULT_SCHEDULE_POSITION = 9999  # High number to put items at end of list
MTIME_TOLERANCE = 0.001  # Tolerance for file modification time comparison

# Use core utilities for standardized imports
from MediCafe.core_utils import (
    import_medibot_module,
    import_medilink_module,
    get_shared_config_loader
)

# Add the parent directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configuration cache to avoid repeated loading
_config_cache = None
_crosswalk_cache = None

# Initialize configuration loader - CRITICAL: This module requires MediLink_ConfigLoader
MediLink_ConfigLoader = get_shared_config_loader()
if MediLink_ConfigLoader is None:
    raise ImportError(
        "[MediBot_Preprocessor_lib] CRITICAL: MediLink_ConfigLoader module import failed. "
        "This module requires MediLink_ConfigLoader to function. "
        "Check PYTHONPATH, module dependencies, and ensure MediCafe package is properly installed."
    )

# Import MediLink_DataMgmt using centralized import function
MediLink_DataMgmt = import_medilink_module('MediLink_DataMgmt')

# Import MediBot modules using centralized import functions
MediBot_UI = import_medibot_module('MediBot_UI')
if MediBot_UI:
    app_control = getattr(MediBot_UI, 'app_control', None)
    get_app_control = getattr(MediBot_UI, '_get_app_control', None)
    
    def _ac():
        try:
            return get_app_control() if get_app_control else getattr(MediBot_UI, 'app_control', None)
        except Exception:
            return getattr(MediBot_UI, 'app_control', None)
else:
    app_control = None

MediBot_docx_decoder = import_medibot_module('MediBot_docx_decoder')
if MediBot_docx_decoder:
    parse_docx = getattr(MediBot_docx_decoder, 'parse_docx', None)
else:
    parse_docx = None

# Import centralized logging configuration
try:
    from MediCafe.logging_config import PERFORMANCE_LOGGING
except ImportError:
    # Fallback to local flag if centralized config is not available
    PERFORMANCE_LOGGING = False

# XP Compatibility: Add robust fallback for configuration loading
def get_cached_configuration_xp_safe():
    """
    XP-compatible version of get_cached_configuration with robust fallbacks.
    """
    global _config_cache, _crosswalk_cache
    
    # If we already have cached data, return it
    if _config_cache is not None and _crosswalk_cache is not None:
        return _config_cache, _crosswalk_cache
    
    # Try to load configuration using the standard method
    try:
        if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'load_configuration'):
            _config_cache, _crosswalk_cache = MediLink_ConfigLoader.load_configuration()
            return _config_cache, _crosswalk_cache
    except Exception as e:
        print("Warning: Failed to load configuration via MediLink_ConfigLoader: {}".format(e))
    
    # Fallback: Try to load configuration files directly
    try:
        import json
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Try to load config.json
        config_path = os.path.join(project_dir, 'json', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                _config_cache = json.load(f)
        else:
            _config_cache = {}
        
        # Try to load crosswalk.json
        crosswalk_path = os.path.join(project_dir, 'json', 'crosswalk.json')
        if os.path.exists(crosswalk_path):
            with open(crosswalk_path, 'r') as f:
                _crosswalk_cache = json.load(f)
        else:
            _crosswalk_cache = {}
        
        return _config_cache, _crosswalk_cache
        
    except Exception as e:
        print("Warning: Failed to load configuration files directly: {}".format(e))
        # Return empty defaults
        _config_cache = {}
        _crosswalk_cache = {}
        return _config_cache, _crosswalk_cache

# --- Helper: Read endpoint default from config with safe fallback (XP-safe) ---
def _get_default_endpoint(config):
    try:
        mlc = config.get('MediLink_Config', {}) if isinstance(config, dict) else {}
        default_ep = mlc.get('default_endpoint', None)
        return default_ep if default_ep else 'OPTUMEDI'
    except Exception:
        return 'OPTUMEDI'

class InitializationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def initialize(config):
    global AHK_EXECUTABLE, CSV_FILE_PATH, field_mapping, page_end_markers
    
    required_keys = {
        'AHK_EXECUTABLE': "",
        'CSV_FILE_PATH': "",
        'field_mapping': {},
        'page_end_markers': []
    }
    
    for key, default in required_keys.items():
        try:
            globals()[key] = config.get(key, default) if key != 'field_mapping' else OrderedDict(config.get(key, default))
        except AttributeError:
            raise InitializationError("Error: '{}' not found in config.".format(key))

def get_cached_configuration():
    """
    Returns cached configuration and crosswalk data to avoid repeated I/O operations.
    """
    return get_cached_configuration_xp_safe()

def open_csv_for_editing(csv_file_path):
    try:
        # Open the CSV file with its associated application
        os.system('start "" "{}"'.format(csv_file_path))
        print("After saving the revised CSV, please re-run MediBot.")
    except Exception as e:
        print("Failed to open CSV file:", e)
        
# Function to clean the headers
def clean_header(headers):
    """
    Cleans the header strings by removing unwanted characters and trimming whitespace.

    Parameters:
    headers (list of str): The original header strings.

    Returns:
    list of str: The cleaned header strings.
    """
    cleaned_headers = []
    
    for header in headers:
        # Strip leading and trailing whitespace
        cleaned_header = header.strip()
        # Remove unwanted characters while keeping spaces, alphanumeric characters, hyphens, and underscores
        cleaned_header = ''.join(char for char in cleaned_header if char.isalnum() or char.isspace() or char in ['-', '_'])
        cleaned_headers.append(cleaned_header)

    # Log the cleaned headers for debugging
    MediLink_ConfigLoader.log("Cleaned headers: {}".format(cleaned_headers), level="DEBUG")

    # Check if 'Surgery Date' is in the cleaned headers
    if 'Surgery Date' not in cleaned_headers:
        MediLink_ConfigLoader.log("WARNING: 'Surgery Date' header not found after cleaning.", level="WARNING")
        print("WARNING: 'Surgery Date' header not found after cleaning.")
        raise ValueError("Error: 'Surgery Date' header not found after cleaning.")

    return cleaned_headers

# Function to load and process CSV data
def load_csv_data(csv_file_path):
    try:
        # Check if the file exists
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError("***Error: CSV file '{}' not found.".format(csv_file_path))
        
        # Detect the file encoding
        with open(csv_file_path, 'rb') as f:
            raw_data = f.read()
            if chardet:
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
            else:
                # Fallback to UTF-8 when chardet is not available
                encoding = 'utf-8'
                confidence = 1.0
            print("Detected encoding: {} (Confidence: {:.2f})".format(encoding, confidence))

        # Read the CSV file with the detected encoding
        with open(csv_file_path, 'r', encoding=encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            # Clean the headers
            cleaned_headers = clean_header(reader.fieldnames)

            # PERFORMANCE FIX: Use zip() instead of range(len()) for header mapping
            header_mapping = {clean: orig for clean, orig in zip(cleaned_headers, reader.fieldnames)}

            # Process the remaining rows - optimize by pre-allocating the list
            csv_data = []
            # Pre-allocate list size if we can estimate it (optional optimization)
            # csv_data = [None] * estimated_size  # if we had row count
            
            for row in reader:
                # PERFORMANCE FIX: Use zip() instead of range(len()) for row processing
                cleaned_row = {clean: row[header_mapping[clean]] for clean in cleaned_headers}
                csv_data.append(cleaned_row)

            return csv_data  # Return a list of dictionaries
    except FileNotFoundError as e:
        print(e)  # Print the informative error message
        print("Hint: Check if CSV file is located in the expected directory or specify a different path in config file.")
        print("Please correct the issue and re-run MediBot.")
        sys.exit(1)  # Halt the script
    except IOError as e:
        print("Error reading CSV file: {}. Please check the file path and permissions.".format(e))
        sys.exit(1)  # Halt the script in case of other IO errors

# CSV Pre-processor Helper functions
def add_columns(csv_data, column_headers):
    """
    Adds one or multiple columns to the CSV data.
    
    Parameters:
    csv_data (list of dict): The CSV data where each row is represented as a dictionary.
    column_headers (list of str or str): A list of column headers to be added to each row, or a single column header.
    
    Returns:
    None: The function modifies the csv_data in place.
    """
    if isinstance(column_headers, str):
        column_headers = [column_headers]
    elif not isinstance(column_headers, list):
        raise ValueError("column_headers should be a list or a string")

    # PERFORMANCE FIX: Optimize column initialization to avoid nested loop
    for row in csv_data:
        # Use dict.update() to set multiple columns at once
        row.update({header: '' for header in column_headers})

# Extracting the list to a variable for future refactoring:
def filter_rows(csv_data):
    # TODO: This should be written in the crosswalk and not hardcoded here.
    excluded_insurance = {'AETNA', 'AETNA MEDICARE', 'HUMANA MED HMO'}
    csv_data[:] = [row for row in csv_data if row.get('Patient ID') and row.get('Primary Insurance') not in excluded_insurance]

def clean_patient_ssn(csv_data):
    """
    Cleans and validates Patient SSN fields by extracting only digits and ensuring 9-digit format.

    Parameters:
    csv_data (list of dict): The CSV data where each row is represented as a dictionary.

    Returns:
    None: The function modifies the csv_data in place.
    """
    for row in csv_data:
        ssn_digits = re.sub(r"\D", "", row.get("Patient SSN", "") or "")
        row["Patient SSN"] = ssn_digits if len(ssn_digits) == 9 else ""

def detect_date_format(date_str):
    """
    PERFORMANCE OPTIMIZATION: Quickly detect the most likely date format
    to avoid trying all formats for every date string.
    
    Parameters:
    - date_str (str): The date string to analyze
    
    Returns:
    - str: The most likely format string, or None if unclear
    """
    if not date_str:
        return None
    
    # Remove time components if present
    date_only = date_str.split()[0]
    
    # Count separators to guess format
    slash_count = date_only.count('/')
    dash_count = date_only.count('-')
    
    # Check for 4-digit year (likely YYYY format)
    if len(date_only) >= 10:  # YYYY-MM-DD or YYYY/MM/DD
        if dash_count == 2:
            return '%Y-%m-%d'
        elif slash_count == 2:
            return '%Y/%m/%d'
    
    # Check for 2-digit year (likely MM/DD/YY or MM-DD-YY)
    if len(date_only) >= 8:  # MM/DD/YY or MM-DD-YY
        if dash_count == 2:
            return '%m-%d-%y'
        elif slash_count == 2:
            return '%m/%d/%y'
    
    # Default to most common format (MM/DD/YYYY)
    if dash_count == 2:
        return '%m-%d-%Y'
    elif slash_count == 2:
        return '%m/%d/%Y'
    
    return None

class OptimizedDate:
    """
    Optimized date object that pre-computes all common format variations
    to avoid redundant datetime conversions throughout the application.
    """
    def __init__(self, datetime_obj):
        self.datetime = datetime_obj
        # Pre-compute all common format variations
        self._display_short = datetime_obj.strftime('%m-%d')  # For table display
        self._display_full = datetime_obj.strftime('%m-%d-%Y')  # Full format
        self._medisoft_format = datetime_obj.strftime('%m%d%Y')  # For Medisoft entry
        self._iso_format = datetime_obj.strftime('%Y-%m-%d')  # For sorting/comparison
        
    @property
    def display_short(self):
        """Short display format: MM-DD"""
        return self._display_short
        
    @property
    def display_full(self):
        """Full display format: MM-DD-YYYY"""
        return self._display_full
        
    @property
    def medisoft_format(self):
        """Medisoft entry format: MMDDYYYY"""
        return self._medisoft_format
        
    @property
    def iso_format(self):
        """ISO format for sorting: YYYY-MM-DD"""
        return self._iso_format
    
    def __str__(self):
        return self._display_full
        
    def __repr__(self):
        return "OptimizedDate({})".format(self._display_full)
        
    def __eq__(self, other):
        if isinstance(other, OptimizedDate):
            return self.datetime == other.datetime
        elif hasattr(other, 'strftime'):  # datetime object
            return self.datetime == other
        return False
        
    def __lt__(self, other):
        if isinstance(other, OptimizedDate):
            return self.datetime < other.datetime
        elif hasattr(other, 'strftime'):  # datetime object
            return self.datetime < other
        return NotImplemented
        
    def __gt__(self, other):
        if isinstance(other, OptimizedDate):
            return self.datetime > other.datetime
        elif hasattr(other, 'strftime'):  # datetime object
            return self.datetime > other
        return NotImplemented
    
    def strftime(self, format_str):
        """Fallback for any custom format needs"""
        return self.datetime.strftime(format_str)
        
    @classmethod
    def from_string(cls, date_str, cleaned=False):
        """
        Create OptimizedDate from string, with optional pre-cleaning.
        
        Args:
            date_str: Date string to parse
            cleaned: If True, assumes string is already cleaned
            
        Returns:
            OptimizedDate object or None if parsing fails
        """
        if not cleaned:
            date_str = clean_surgery_date_string(date_str)
            if not date_str:
                return None
        
        # Try standard format first (most common)
        try:
            return cls(datetime.strptime(date_str, '%m/%d/%Y'))
        except ValueError:
            pass
            
        # Try alternative formats
        formats = ['%m-%d-%Y', '%m/%d/%y', '%m-%d-%y', '%Y/%m/%d', '%Y-%m-%d']
        for fmt in formats:
            try:
                return cls(datetime.strptime(date_str, fmt))
            except ValueError:
                continue
                
        return None

def clean_surgery_date_string(date_str):
    """
    Cleans and normalizes surgery date strings to handle damaged data.
    
    Parameters:
    - date_str (str): The raw date string from the CSV
    
    Returns:
    - str: Cleaned date string in MM/DD/YYYY format, or empty string if unparseable
    """
    if not date_str:
        return ''
    
    # Convert to string and strip whitespace
    date_str = str(date_str).strip()
    if not date_str:
        return ''
    
    # Remove common problematic characters and normalize
    date_str = date_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    date_str = ' '.join(date_str.split())  # Normalize whitespace
    
    # PERFORMANCE OPTIMIZATION: Try detected format first
    detected_format = detect_date_format(date_str)
    if detected_format:
        try:
            parsed_date = datetime.strptime(date_str, detected_format)
            return parsed_date.strftime('%m/%d/%Y')
        except ValueError:
            pass
    
    # PERFORMANCE OPTIMIZATION: Try most common format first (MM/DD/YYYY)
    # This reduces the average number of format attempts from 8 to ~1-2
    try:
        parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    # PERFORMANCE OPTIMIZATION: Try second most common format (MM-DD-YYYY)
    try:
        parsed_date = datetime.strptime(date_str, '%m-%d-%Y')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    # PERFORMANCE OPTIMIZATION: Try 2-digit year formats only if needed
    try:
        parsed_date = datetime.strptime(date_str, '%m/%d/%y')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    try:
        parsed_date = datetime.strptime(date_str, '%m-%d-%y')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    # PERFORMANCE OPTIMIZATION: Try YYYY formats only if needed
    try:
        parsed_date = datetime.strptime(date_str, '%Y/%m/%d')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    # PERFORMANCE OPTIMIZATION: Try datetime formats only if needed
    try:
        parsed_date = datetime.strptime(date_str, '%m/%d/%Y %H:%M:%S')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    try:
        parsed_date = datetime.strptime(date_str, '%m-%d-%Y %H:%M:%S')
        return parsed_date.strftime('%m/%d/%Y')
    except ValueError:
        pass
    
    # If no format matches, try to extract date components
    try:
        # Remove any time components and extra text
        date_only = date_str.split()[0]  # Take first part if there's extra text
        
        # Try to extract numeric components
        import re
        numbers = re.findall(r'\d+', date_only)
        
        if len(numbers) >= 3:
            # Assume MM/DD/YYYY or MM-DD-YYYY format
            month, day, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
            
            # Validate ranges
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                # Handle 2-digit years
                if year < 100:
                    year += 2000 if year < 50 else 1900
                
                parsed_date = datetime(year, month, day)
                return parsed_date.strftime('%m/%d/%Y')
    except (ValueError, IndexError):
        pass
    
    # If all parsing attempts fail, return empty string
    return ''

def convert_surgery_date(csv_data):
    """
    Converts surgery date strings to datetime objects with comprehensive data cleaning.
    
    Parameters:
    - csv_data (list): List of dictionaries containing CSV row data
    """
    # TIMING: Start surgery date conversion with granular tracking
    total_start_time = time.time()
    date_cleaning_time = 0
    date_parsing_time = 0
    processed_count = 0
    empty_count = 0
    error_count = 0
    
    print("Starting surgery date conversion for {} rows...".format(len(csv_data)))
    
    # PERFORMANCE OPTIMIZATION: Pre-compile datetime.strptime for the most common format
    # This avoids repeated format string parsing
    standard_format = '%m/%d/%Y'
    
    for row in csv_data:
        surgery_date_str = row.get('Surgery Date', '')
        
        if not surgery_date_str:
            empty_count += 1
            row['Surgery Date'] = datetime.min  # Assign a minimum datetime value if empty
        else:
            # TIMING: Start date string cleaning
            cleaning_start = time.time()
            
            # Clean the date string first
            cleaned_date_str = clean_surgery_date_string(surgery_date_str)
            
            # TIMING: End date string cleaning
            cleaning_end = time.time()
            date_cleaning_time += (cleaning_end - cleaning_start)
            
            if not cleaned_date_str:
                error_count += 1
                # LOGGING STRATEGY: Log actual errors (cleaning failures) at INFO level
                if error_count <= 5:  # Only log first 5 errors
                    MediLink_ConfigLoader.log("Error: Could not clean Surgery Date '{}' for row: {}".format(surgery_date_str, row), level="INFO")
                    print("Could not clean Surgery Date '{}' for row: {}".format(surgery_date_str, row))
                row['Surgery Date'] = datetime.min  # Assign a minimum datetime value if cleaning fails
            else:
                # TIMING: Start date parsing
                parsing_start = time.time()
                
                try:
                    # PERFORMANCE OPTIMIZATION: Use pre-compiled format string
                    # Parse the cleaned date string
                    row['Surgery Date'] = datetime.strptime(cleaned_date_str, standard_format)
                    processed_count += 1
                except ValueError as e:
                    error_count += 1
                    # LOGGING STRATEGY: Log actual errors (parsing failures) at INFO level
                    if error_count <= 5:  # Only log first 5 parsing errors
                        MediLink_ConfigLoader.log("Error parsing cleaned Surgery Date '{}': {} for row: {}".format(
                            cleaned_date_str, e, row), level="INFO")
                    row['Surgery Date'] = datetime.min  # Assign a minimum datetime value if parsing fails
                
                # TIMING: End date parsing
                parsing_end = time.time()
                date_parsing_time += (parsing_end - parsing_start)
    
    # TIMING: End total surgery date conversion
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    if PERFORMANCE_LOGGING:
        print("Surgery date conversion completed:")
        print("  - Total duration: {:.2f} seconds".format(total_duration))
        print("  - Date cleaning time: {:.2f} seconds ({:.1f}%)".format(date_cleaning_time, (date_cleaning_time/total_duration)*100))
        print("  - Date parsing time: {:.2f} seconds ({:.1f}%)".format(date_parsing_time, (date_parsing_time/total_duration)*100))
        print("  - Processed: {} rows, Empty: {} rows, Errors: {} rows".format(processed_count, empty_count, error_count))
    
    # LOGGING STRATEGY: Log completion summary at INFO level (end of looped event)
    MediLink_ConfigLoader.log("Surgery date conversion completed - Total: {:.2f}s, Cleaning: {:.2f}s, Parsing: {:.2f}s, Processed: {}, Empty: {}, Errors: {}".format(
        total_duration, date_cleaning_time, date_parsing_time, processed_count, empty_count, error_count), level="INFO")

def _create_common_tie_breakers(row):
    """
    Creates common tie-breaker components used across multiple sorting strategies.
    This follows DRY principle by extracting shared logic.
    """
    last_name = ((row.get('Patient Last') or '')).strip().upper()
    first_name = ((row.get('Patient First') or '')).strip().upper()
    patient_id_tiebreak = str(row.get('Patient ID') or '')
    return (last_name, first_name, patient_id_tiebreak)

def _normalize_surgery_date(row):
    """
    Normalizes surgery date for consistent sorting across strategies.
    """
    # Prefer earliest surgery date across all known dates for the patient
    earliest = row.get('_earliest_surgery_date')
    if isinstance(earliest, str) and earliest and earliest != 'MISSING':
        try:
            return datetime.strptime(earliest, '%m-%d-%Y')
        except Exception:
            pass
    
    # Fallback to the single Surgery Date field
    surgery_date = row.get('Surgery Date')
    if isinstance(surgery_date, datetime):
        return surgery_date
    elif isinstance(surgery_date, str) and surgery_date.strip():
        try:
            return datetime.strptime(surgery_date, '%m/%d/%Y')
        except ValueError:
            try:
                return datetime.strptime(surgery_date, '%m-%d-%Y')
            except ValueError:
                pass
    
    return datetime.min

def _get_schedule_position(row):
    """
    Gets the schedule position for a patient from stored DOCX data.
    Returns a high number if no schedule data is available (puts at end).
    """
    schedule_positions = row.get('_schedule_positions', {})
    surgery_date = row.get('Surgery Date')
    
    # Convert surgery date to string format for lookup
    if isinstance(surgery_date, datetime):
        surgery_date_str = surgery_date.strftime('%m-%d-%Y')
    else:
        surgery_date_str = str(surgery_date)
    
    # Return schedule position if available, otherwise high number (end of list)
    return schedule_positions.get(surgery_date_str, DEFAULT_SCHEDULE_POSITION)

def _get_surgery_date_string(row):
    """
    Gets surgery date as string for consistent sorting.
    """
    surgery_date = row.get('Surgery Date')
    if isinstance(surgery_date, datetime):
        return surgery_date.strftime('%m-%d-%Y')
    else:
        return str(surgery_date)

def _create_date_based_sort_key(row):
    """
    Current date-based sorting logic (extracted from existing sort_key function).
    """
    normalized_date = _normalize_surgery_date(row)
    tie_breakers = _create_common_tie_breakers(row)
    return (normalized_date,) + tie_breakers

def _create_schedule_based_sort_key(row):
    """
    Schedule-based sorting logic (new strategy).
    Uses patient position in DOCX surgery schedule as primary sort criterion.
    """
    schedule_position = _get_schedule_position(row)
    surgery_date_str = _get_surgery_date_string(row)
    tie_breakers = _create_common_tie_breakers(row)
    return (schedule_position, surgery_date_str) + tie_breakers

def create_sort_key_strategy(strategy_type='date_based'):
    """
    Factory function that returns the appropriate sort key function.
    Follows existing strategy patterns in the codebase.
    """
    if strategy_type == 'schedule_based':
        return _create_schedule_based_sort_key
    else:
        return _create_date_based_sort_key

def _normalize_date_for_comparison(date_value):
    """Normalize date value for comparison, converting strings to datetime objects."""
    if isinstance(date_value, datetime):
        return date_value
    elif isinstance(date_value, str) and date_value.strip():
        try:
            return datetime.strptime(date_value, '%m/%d/%Y')
        except ValueError:
            try:
                return datetime.strptime(date_value, '%m-%d-%Y')
            except ValueError:
                return datetime.min
    else:
        return datetime.min

def sort_and_deduplicate(csv_data):
    # Create a dictionary to hold unique patients based on Patient ID
    unique_patients = {}
    # Create a dictionary to store multiple surgery dates per patient
    patient_surgery_dates = {}
    
    # Iterate through the CSV data and populate the unique_patients dictionary
    for row in csv_data:
        patient_id = row.get('Patient ID')
        surgery_date = row.get('Surgery Date')
        
        if patient_id not in unique_patients:
            unique_patients[patient_id] = row
            patient_surgery_dates[patient_id] = [surgery_date]
        else:
            # If the patient ID already exists, compare surgery dates
            existing_row = unique_patients[patient_id]
            existing_date = existing_row['Surgery Date']
            
            normalized_surgery_date = _normalize_date_for_comparison(surgery_date)
            normalized_existing_date = _normalize_date_for_comparison(existing_date)

            # DATE PREFERENCE CHANGE (2025-11-05): Modified to prefer EARLIER surgery date instead of later
            # This ensures the FIRST (earliest) date of service is used for AHK entry rather than the latest
            # ORIGINAL: if normalized_surgery_date > normalized_existing_date:  # kept later date
            # CHANGED TO: if normalized_surgery_date < normalized_existing_date:  # keep earlier date
            # REASON: User requirement to use earliest date for primary patient entry
            # TO SWITCH BACK: Change '<' back to '>' to revert to later date preference
            if normalized_surgery_date < normalized_existing_date:
                # Store the old row's surgery date before replacing
                old_date = existing_row['Surgery Date']
                # Add the old date to the list if it's not already there
                if old_date not in patient_surgery_dates[patient_id]:
                    patient_surgery_dates[patient_id].append(old_date)
                # Replace with newer row (better demographics)
                unique_patients[patient_id] = row
                # Add the new surgery date to the list if it's not already there
                if surgery_date not in patient_surgery_dates[patient_id]:
                    patient_surgery_dates[patient_id].append(surgery_date)
            else:
                # Add this surgery date to the list for this patient if it's not already there
                if surgery_date not in patient_surgery_dates[patient_id]:
                    patient_surgery_dates[patient_id].append(surgery_date)

    # Store the surgery dates information in the first row of each patient for later access
    for patient_id, row in unique_patients.items():
        # Convert surgery dates to strings for consistent storage
        surgery_date_strings = []
        for date in patient_surgery_dates[patient_id]:
            if isinstance(date, datetime):
                if date == datetime.min:
                    surgery_date_strings.append('MISSING')
                else:
                    surgery_date_strings.append(date.strftime('%m-%d-%Y'))
            else:
                surgery_date_strings.append(str(date) if date else 'MISSING')
        
        # Remove duplicates and sort
        unique_surgery_dates = list(set(surgery_date_strings))
        sorted_surgery_dates = sorted(unique_surgery_dates, key=lambda x: datetime.strptime(x, '%m-%d-%Y') if x != 'MISSING' else datetime.min)
        row['_all_surgery_dates'] = sorted_surgery_dates
        row['_primary_surgery_date'] = row['Surgery Date']  # Keep track of which date has the demographics
        # Compute and store earliest surgery date for emission sort
        earliest_str = None
        for d in sorted_surgery_dates:
            if d and d != 'MISSING':
                try:
                    # Validate date format by parsing (but we only need the string)
                    datetime.strptime(d, '%m-%d-%Y')
                    earliest_str = d
                    break
                except Exception:
                    pass
        # Fallback to demographics date if earliest could not be determined
        if earliest_str is None:
            try:
                sd = row.get('Surgery Date')
                if isinstance(sd, datetime) and sd != datetime.min:
                    earliest_str = sd.strftime('%m-%d-%Y')
                elif isinstance(sd, str) and sd.strip():
                    # Validate date format by parsing (but we only need the string)
                    try:
                        datetime.strptime(sd, '%m/%d/%Y')
                    except Exception:
                        try:
                            datetime.strptime(sd, '%m-%d-%Y')
                        except Exception:
                            pass
                    earliest_str = sd
            except Exception:
                earliest_str = None
        row['_earliest_surgery_date'] = earliest_str

    # Convert the unique_patients dictionary back to a list and sort it
    # Use strategy pattern for sorting (follows existing codebase patterns)
    sort_key_func = create_sort_key_strategy(SORTING_STRATEGY)
    
    csv_data[:] = sorted(unique_patients.values(), key=sort_key_func)
    
    # TODO: Consider adding an option in the config to sort based on Surgery Schedules when available.
    # If no schedule is available, the current sorting strategy will be used.
    # 
    # IMPLEMENTATION STATUS: Backend infrastructure is ready.
    # To enable surgery schedule sorting, set SORTING_STRATEGY = 'schedule_based' above.
    # The system will automatically fall back to date-based sorting if schedule data is unavailable.

def combine_fields(csv_data):
    for row in csv_data:
        # Safely handle the 'Surgery Date' conversion with clear missing indicator
        surgery_date = row.get('Surgery Date')
        try:
            if isinstance(surgery_date, datetime):
                if surgery_date == datetime.min:
                    row['Surgery Date'] = 'MISSING'
                else:
                    row['Surgery Date'] = surgery_date.strftime('%m-%d-%Y')
            elif surgery_date:
                # Already a non-empty string
                row['Surgery Date'] = str(surgery_date)
            else:
                row['Surgery Date'] = 'MISSING'
        except Exception:
            row['Surgery Date'] = 'MISSING'
        
        first_name = '_'.join(part.strip() for part in row.get('Patient First', '').split())
        middle_name = row.get('Patient Middle', '').strip()
        middle_name = middle_name[0] if len(middle_name) > 1 else ''
        last_name = '_'.join(part.strip() for part in row.get('Patient Last', '').split())
        row['Patient Name'] = ', '.join(filter(None, [last_name, first_name])) + (' ' + middle_name if middle_name else '')
        
        address1 = row.get('Patient Address1', '').strip()
        address2 = row.get('Patient Address2', '').strip()
        row['Patient Street'] = ' '.join(filter(None, [address1, address2]))

def apply_replacements(csv_data, crosswalk):
    replacements = crosswalk.get('csv_replacements', {})
    # Pre-define the keys to check for better performance
    keys_to_check = ['Patient SSN', 'Primary Insurance', 'Ins1 Payer ID']
    
    for row in csv_data:
        # Apply all applicable replacements - check all keys for all replacements
        # This ensures multiple replacements per row are applied (e.g., both SSN and Payer ID)
        for old_value, new_value in replacements.items():
            for key in keys_to_check:
                if row.get(key) == old_value:
                    row[key] = new_value
                    # Continue checking other keys and other replacements

import difflib
from collections import defaultdict

def find_best_medisoft_id(insurance_name, medisoft_ids, medisoft_to_mains_names):
    """
    Finds the best matching Medisoft ID for a given insurance name using fuzzy matching.

    Parameters:
    - insurance_name (str): The insurance name from the CSV row.
    - medisoft_ids (list): List of Medisoft IDs associated with the Payer ID.
    - medisoft_to_mains_names (dict): Mapping from Medisoft ID to list of MAINS names.

    Returns:
    - int or None: The best matching Medisoft ID or None if no match is found.
    """
    best_match_ratio = 0
    best_medisoft_id = None

    # Pre-process insurance name once
    processed_insurance = ''.join(c for c in insurance_name if not c.isdigit()).upper()

    for medisoft_id in medisoft_ids:
        mains_names = medisoft_to_mains_names.get(medisoft_id, [])
        for mains_name in mains_names:
            # Preprocess names by extracting non-numeric characters and converting to uppercase
            # Use more efficient string processing
            processed_mains = ''.join(c for c in mains_name if not c.isdigit()).upper()

            # Log the processed names before computing the match ratio
            MediLink_ConfigLoader.log("Processing Medisoft ID '{}': Comparing processed insurance '{}' with processed mains '{}'.".format(medisoft_id, processed_insurance, processed_mains), level="DEBUG")

            # Compute the similarity ratio
            match_ratio = difflib.SequenceMatcher(None, processed_insurance, processed_mains).ratio()

            # Log the match ratio
            MediLink_ConfigLoader.log("Match ratio for Medisoft ID '{}': {:.2f}".format(medisoft_id, match_ratio), level="DEBUG")

            if match_ratio > best_match_ratio:
                best_match_ratio = match_ratio
                best_medisoft_id = medisoft_id
                # Log the current best match
                MediLink_ConfigLoader.log("New best match found: Medisoft ID '{}' with match ratio {:.2f}".format(best_medisoft_id, best_match_ratio), level="DEBUG")

    # Log the final best match ratio and ID
    MediLink_ConfigLoader.log("Final best match ratio: {:.2f} for Medisoft ID '{}'".format(best_match_ratio, best_medisoft_id), level="DEBUG")

    # No threshold applied, return the best match found
    return best_medisoft_id

def NEW_update_insurance_ids(csv_data, config, crosswalk):
    """
    Updates the 'Ins1 Insurance ID' field in each row of csv_data based on the crosswalk and MAINS data.

    Parameters:
    - csv_data (list of dict): The CSV data where each row is represented as a dictionary.
    - config (dict): Configuration object containing necessary paths and parameters.
    - crosswalk (dict): Crosswalk data containing mappings between Payer IDs and Medisoft IDs.

    Returns:
    - None: The function modifies the csv_data in place.
    """
    processed_payer_ids = set()  # Track processed Payer IDs
    MediLink_ConfigLoader.log("Starting update of insurance IDs.", level="INFO")

    # PERFORMANCE FIX: Pre-build flattened payer lookup cache to avoid nested dictionary access
    payer_cache = {}
    crosswalk_payers = crosswalk.get('payer_id', {})
    for payer_id, details in crosswalk_payers.items():
        payer_cache[payer_id] = {
            'medisoft_id': details.get('medisoft_id', []),
            'medisoft_medicare_id': details.get('medisoft_medicare_id', []),
            'endpoint': details.get('endpoint', None)
        }
    MediLink_ConfigLoader.log("Built payer cache for {} payers".format(len(payer_cache)), level="DEBUG")

    # Load MAINS data to get mapping from Medisoft ID to MAINS names
    insurance_to_id = load_insurance_data_from_mains(config)  # Assuming it returns a dict mapping insurance names to IDs
    MediLink_ConfigLoader.log("Loaded MAINS data for insurance to ID mapping.", level="DEBUG")
    
    # Invert the mapping to get Medisoft ID to MAINS names
    medisoft_to_mains_names = defaultdict(list)
    for insurance_name, medisoft_id in insurance_to_id.items():
        medisoft_to_mains_names[medisoft_id].append(insurance_name)

    for row_idx, row in enumerate(csv_data, 1):
        # PERFORMANCE FIX: Store row index to avoid O(n) csv_data.index() calls later
        row['_row_index'] = row_idx
        ins1_payer_id = row.get('Ins1 Payer ID', '').strip()
        MediLink_ConfigLoader.log("Processing row with Ins1 Payer ID: '{}'.".format(ins1_payer_id), level="DEBUG")
        
        if ins1_payer_id:
            # Mark this Payer ID as processed
            if ins1_payer_id not in processed_payer_ids:
                processed_payer_ids.add(ins1_payer_id)  # Add to set
                MediLink_ConfigLoader.log("Marked Payer ID '{}' as processed.".format(ins1_payer_id), level="DEBUG")
                
                # PERFORMANCE FIX: Use flattened cache instead of nested dictionary lookups
                payer_info = payer_cache.get(ins1_payer_id, {})
                medisoft_ids = payer_info.get('medisoft_id', [])
                MediLink_ConfigLoader.log("Retrieved Medisoft IDs for Payer ID '{}': {}".format(ins1_payer_id, medisoft_ids), level="DEBUG")

        if not medisoft_ids:
            MediLink_ConfigLoader.log("No Medisoft IDs available for Payer ID '{}', creating placeholder entry.".format(ins1_payer_id), level="WARNING")
            # Create a placeholder entry in the crosswalk and cache
            placeholder_entry = {
                'medisoft_id': [],  # Placeholder for future Medisoft IDs
                'medisoft_medicare_id': [],  # Placeholder for future Medicare IDs
                'endpoint': None  # Placeholder for future endpoint
            }
            if 'payer_id' not in crosswalk:
                crosswalk['payer_id'] = {}
            crosswalk['payer_id'][ins1_payer_id] = placeholder_entry
            # PERFORMANCE FIX: Update cache with placeholder entry
            payer_cache[ins1_payer_id] = placeholder_entry
            continue  # Skip further processing for this Payer ID

        # If only one Medisoft ID is associated, assign it directly
        if len(medisoft_ids) == 1:
            try:
                medisoft_id = int(medisoft_ids[0])
                row['Ins1 Insurance ID'] = medisoft_id
                # PERFORMANCE FIX: Use enumerate index instead of csv_data.index() which is O(n)
                row_number = row.get('_row_index', 'Unknown')
                MediLink_ConfigLoader.log("Assigned Medisoft ID '{}' to row number {} with Payer ID '{}'.".format(medisoft_id, row_number, ins1_payer_id), level="DEBUG")
            except ValueError as e:
                MediLink_ConfigLoader.log("Error converting Medisoft ID '{}' to integer for Payer ID '{}': {}".format(medisoft_ids[0], ins1_payer_id, e), level="ERROR")
                row['Ins1 Insurance ID'] = None
            continue  # Move to the next row

        # If multiple Medisoft IDs are associated, perform fuzzy matching
        insurance_name = row.get('Primary Insurance', '').strip()
        if not insurance_name:
            MediLink_ConfigLoader.log("Row with Payer ID '{}' missing 'Primary Insurance', skipping assignment.".format(ins1_payer_id), level="WARNING")
            continue  # Skip if insurance name is missing

        best_medisoft_id = find_best_medisoft_id(insurance_name, medisoft_ids, medisoft_to_mains_names)

        if best_medisoft_id:
            row['Ins1 Insurance ID'] = best_medisoft_id
            MediLink_ConfigLoader.log("Assigned Medisoft ID '{}' to row with Payer ID '{}' based on fuzzy match.".format(best_medisoft_id, ins1_payer_id), level="INFO")
        else:
            # Default to the first Medisoft ID if no good match is found
            try:
                default_medisoft_id = int(medisoft_ids[0])
                row['Ins1 Insurance ID'] = default_medisoft_id
                MediLink_ConfigLoader.log("No suitable match found. Defaulted to Medisoft ID '{}' for Payer ID '{}'.".format(default_medisoft_id, ins1_payer_id), level="INFO")
            except ValueError as e:
                MediLink_ConfigLoader.log("Error converting default Medisoft ID '{}' to integer for Payer ID '{}': {}".format(medisoft_ids[0], ins1_payer_id, e), level="ERROR")
                row['Ins1 Insurance ID'] = None

def validate_csv_payer_ids(csv_data):
    """
    Validates all unique payer IDs extracted from CSV data.
    Since 99% of contamination comes from CSV, bulk validation catches issues early.
    
    Note: This function is no longer used in the main processing flow, but kept for
    potential future use or debugging purposes.
    
    Args:
        csv_data (list): List of CSV row dictionaries
        
    Returns:
        tuple: (valid_payer_ids_set, invalid_payer_ids_set)
            - valid_payer_ids_set: Set of valid payer IDs to process
            - invalid_payer_ids_set: Set of invalid payer IDs to reject
    """
    # Import validation function
    try:
        from MediLink.MediLink_837p_utilities import is_valid_payer_id_format
    except ImportError:
        # Fallback if import fails
        is_valid_payer_id_format = None
    
    # Extract all unique payer IDs from CSV
    unique_payer_ids = set()
    for row in csv_data:
        ins1_payer_id = row.get('Ins1 Payer ID', '').strip()
        if ins1_payer_id:  # Only consider non-empty payer IDs
            unique_payer_ids.add(ins1_payer_id)
    
    valid_payer_ids = set()
    invalid_payer_ids = set()
    
    if is_valid_payer_id_format:
        for payer_id in unique_payer_ids:
            if is_valid_payer_id_format(payer_id):
                valid_payer_ids.add(payer_id)
            else:
                invalid_payer_ids.add(payer_id)
    else:
        # If validation function unavailable, treat all as valid
        valid_payer_ids = unique_payer_ids
    
    return valid_payer_ids, invalid_payer_ids

def update_insurance_ids(csv_data, config, crosswalk):
    # TIMING: Start insurance ID updates with granular tracking
    total_start_time = time.time()
    lookup_build_time = 0
    csv_processing_time = 0
    processed_count = 0
    medicare_count = 0
    regular_count = 0
    placeholder_count = 0
    
    print("Starting insurance ID updates for {} rows...".format(len(csv_data)))
    
    # Import validation function for DEBUG logging
    try:
        from MediLink.MediLink_837p_utilities import is_valid_payer_id_format
    except ImportError:
        # Fallback if import fails
        is_valid_payer_id_format = None
    
    # TIMING: Start lookup dictionary building
    lookup_start_time = time.time()
    
    # PERFORMANCE FIX: Pre-build optimized lookup dictionaries for both regular and Medicare IDs
    # This reduces Medicare processing overhead by building lookups once instead of repeated processing
    payer_id_to_medisoft = {}
    payer_id_to_medicare = {}
    
    # Build both lookup dictionaries simultaneously to avoid multiple iterations
    for payer_id, details in crosswalk.get('payer_id', {}).items():
        # Get both regular and Medicare IDs
        medisoft_ids = details.get('medisoft_id', [])
        medicare_ids = details.get('medisoft_medicare_id', [])
        
        # Filter empty strings once for each type
        medisoft_ids = [id for id in medisoft_ids if id] if medisoft_ids else []
        medicare_ids = [id for id in medicare_ids if id] if medicare_ids else []
        
        # Store first valid ID for quick lookup (Medicare takes precedence if available)
        payer_id_to_medisoft[payer_id] = int(medisoft_ids[0]) if medisoft_ids else None
        payer_id_to_medicare[payer_id] = int(medicare_ids[0]) if medicare_ids else None
    
    # TIMING: End lookup dictionary building
    lookup_end_time = time.time()
    lookup_build_time = lookup_end_time - lookup_start_time
    
    if PERFORMANCE_LOGGING:
        print("Built lookup dictionaries in {:.2f} seconds for {} payer IDs".format(lookup_build_time, len(payer_id_to_medisoft)))

    
    # TIMING: Start CSV processing
    csv_start_time = time.time()
    
    # PERFORMANCE FIX: Single pass through CSV data with optimized Medicare ID resolution
    # Process all rows regardless of payer ID format (self-pay/charity cases may have notes instead of IDs)
    for row in csv_data:
        ins1_payer_id = row.get('Ins1 Payer ID', '').strip()
        
        # Skip empty payer IDs
        if not ins1_payer_id:
            continue
        
        # DEBUG: Log potential self-pay/charity cases with non-standard payer ID format
        is_invalid_format = False
        if is_valid_payer_id_format and not is_valid_payer_id_format(ins1_payer_id):
            is_invalid_format = True
            patient_id = row.get('Patient ID', 'Unknown')
            MediLink_ConfigLoader.log(
                "Detected potential self-pay/charity case with non-standard payer ID format: '{}' for Patient ID '{}'".format(
                    ins1_payer_id[:100], patient_id
                ),
                config,
                level="DEBUG"
            )
        
        # Try Medicare ID first, then fall back to regular ID (optimized Medicare processing)
        insurance_id = (payer_id_to_medicare.get(ins1_payer_id) or 
                       payer_id_to_medisoft.get(ins1_payer_id))
        
        # Only create placeholder entries for valid-format payer IDs that aren't in crosswalk
        # Invalid formats (self-pay/charity notes) should not pollute the crosswalk
        if insurance_id is None and ins1_payer_id not in payer_id_to_medisoft and not is_invalid_format:
            # Add placeholder entry for new payer ID (preserve original functionality)
            payer_id_to_medisoft[ins1_payer_id] = None
            payer_id_to_medicare[ins1_payer_id] = None
            crosswalk.setdefault('payer_id', {})[ins1_payer_id] = {
                'medisoft_id': [],  # Placeholder for future Medisoft IDs
                'medisoft_medicare_id': [],  # Placeholder for future Medicare IDs
                'endpoint': None  # Placeholder for future endpoint
            }
            placeholder_count += 1
            # LOGGING STRATEGY: Log actual events (new payer IDs) at INFO level
            if placeholder_count <= 5:  # Only log first 5 placeholders
                MediLink_ConfigLoader.log("Added placeholder entry for new Payer ID '{}'.".format(ins1_payer_id), config, level="INFO")
        elif insurance_id is not None:
            # Only count as medicare/regular if we have a valid insurance_id
            if insurance_id == payer_id_to_medicare.get(ins1_payer_id):
                medicare_count += 1
            else:
                regular_count += 1
        # Note: If insurance_id is None and is_invalid_format is True, don't increment counters
        # (self-pay/charity cases are processed but not counted in statistics)
        
        # Assign the resolved insurance ID to the row
        row['Ins1 Insurance ID'] = insurance_id
        # TODO (SECONDARY QUEUE): When building a secondary-claims queue after Medicare crossover,
        # set claim_type='secondary' and attach prior payer fields here from the Medicare primary outcome:
        # - row['prior_payer_name'] = 'MEDICARE'
        # - row['prior_payer_id'] = best Medicare ID from config/crosswalk
        # - optionally row['primary_paid_amount'], row['cas_adjustments'] extracted from 835
        processed_count += 1
    
    # TIMING: End CSV processing
    csv_end_time = time.time()
    csv_processing_time = csv_end_time - csv_start_time
    
    # TIMING: End total insurance ID updates
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    if PERFORMANCE_LOGGING:
        print("Insurance ID updates completed:")
        print("  - Total duration: {:.2f} seconds".format(total_duration))
        if total_duration > 0:
            print("  - Lookup building time: {:.2f} seconds ({:.1f}%)".format(lookup_build_time, (lookup_build_time/total_duration)*100))
            print("  - CSV processing time: {:.2f} seconds ({:.1f}%)".format(csv_processing_time, (csv_processing_time/total_duration)*100))
        else:
            print("  - Lookup building time: {:.2f} seconds".format(lookup_build_time))
            print("  - CSV processing time: {:.2f} seconds".format(csv_processing_time))
    print("  - Processed: {} rows, Medicare: {} rows, Regular: {} rows, Placeholders: {} rows".format(
        processed_count, medicare_count, regular_count, placeholder_count))
    
    # LOGGING STRATEGY: Log completion summary at INFO level (end of looped event)
    MediLink_ConfigLoader.log("Insurance ID updates completed - Total: {:.2f}s, Lookup: {:.2f}s, Processing: {:.2f}s, Processed: {}, Medicare: {}, Regular: {}, Placeholders: {}".format(
        total_duration, lookup_build_time, csv_processing_time, processed_count, medicare_count, regular_count, placeholder_count), level="INFO")

def update_procedure_codes(csv_data, crosswalk):
    # Get Medisoft shorthand dictionary from crosswalk and reverse it
    diagnosis_to_medisoft = crosswalk.get('diagnosis_to_medisoft', {}) # BUG We need to be careful here in case we decide we need to change the crosswalk data specifically with regard to the T8/H usage.
    medisoft_to_diagnosis = {v: k for k, v in diagnosis_to_medisoft.items()}

    # Get procedure code to diagnosis dictionary from crosswalk and reverse it for easier lookup
    diagnosis_to_procedure = {
        diagnosis_code: procedure_code
        for procedure_code, diagnosis_codes in crosswalk.get('procedure_to_diagnosis', {}).items()
        for diagnosis_code in diagnosis_codes
    }

    # Initialize counters for tracking
    updated_count = 0
    missing_medisoft_codes = set()
    missing_procedure_mappings = set()

    # Update the "Procedure Code" column in the CSV data
    for row_num, row in enumerate(csv_data, start=1):
        try:
            medisoft_code = row.get('Default Diagnosis #1', '').strip()
            diagnosis_code = medisoft_to_diagnosis.get(medisoft_code)
            
            if diagnosis_code:
                procedure_code = diagnosis_to_procedure.get(diagnosis_code)
                if procedure_code:
                    row['Procedure Code'] = procedure_code
                    updated_count += 1
                else:
                    # Track missing procedure mapping
                    missing_procedure_mappings.add(diagnosis_code)
                    row['Procedure Code'] = "Unknown"  # Will be handled by 837p encoder
                    MediLink_ConfigLoader.log("Missing procedure mapping for diagnosis code '{}' (Medisoft code: '{}') in row {}".format(
                        diagnosis_code, medisoft_code, row_num), level="WARNING")
            else:
                # Track missing Medisoft code mapping
                if medisoft_code:  # Only track if there's actually a code
                    missing_medisoft_codes.add(medisoft_code)
                row['Procedure Code'] = "Unknown"  # Will be handled by 837p encoder
                MediLink_ConfigLoader.log("Missing Medisoft code mapping for '{}' in row {}".format(
                    medisoft_code, row_num), level="WARNING")
        except Exception as e:
            MediLink_ConfigLoader.log("In update_procedure_codes, Error processing row {}: {}".format(row_num, e), level="ERROR")

    # Log summary statistics
    MediLink_ConfigLoader.log("Total {} 'Procedure Code' rows updated.".format(updated_count), level="INFO")
    
    if missing_medisoft_codes:
        MediLink_ConfigLoader.log("Missing Medisoft code mappings: {}".format(sorted(missing_medisoft_codes)), level="WARNING")
        print("WARNING: {} Medisoft codes need to be added to diagnosis_to_medisoft mapping: {}".format(
            len(missing_medisoft_codes), sorted(missing_medisoft_codes)))
    
    if missing_procedure_mappings:
        MediLink_ConfigLoader.log("Missing procedure mappings for diagnosis codes: {}".format(sorted(missing_procedure_mappings)), level="WARNING")
        print("WARNING: {} diagnosis codes need to be added to procedure_to_diagnosis mapping: {}".format(
            len(missing_procedure_mappings), sorted(missing_procedure_mappings)))

    return True

def update_diagnosis_codes(csv_data):
    try:
        # TIMING: Start surgery schedule parsing timing
        parsing_start_time = time.time()
        print("Starting surgery schedule parsing at: {}".format(time.strftime("%H:%M:%S")))
        MediLink_ConfigLoader.log("Starting surgery schedule parsing at: {}".format(time.strftime("%H:%M:%S")), level="INFO")
        
        # Use cached configuration instead of loading repeatedly
        config, crosswalk = get_cached_configuration()
        
        # Extract the local storage path from the configuration
        local_storage_path = config['MediLink_Config']['local_storage_path']
        
        # Initialize a dictionary to hold diagnosis codes from all DOCX files
        all_patient_data = {}
        all_schedule_positions = {}  # NEW: Store schedule positions for future sorting

        # Convert surgery dates in CSV data
        convert_surgery_date(csv_data)
        
        # Extract all valid surgery dates from csv_data
        surgery_dates = [row['Surgery Date'] for row in csv_data if row['Surgery Date'] != datetime.min]
        
        if not surgery_dates:
            raise ValueError("No valid surgery dates found in csv_data.")
        
        # Determine the minimum and maximum surgery dates
        min_surgery_date = min(surgery_dates)
        max_surgery_date = max(surgery_dates)
        
        # Apply a +/-8-day margin to the surgery dates... Increased from 5 days.
        margin = timedelta(days=8)
        threshold_start = min_surgery_date - margin
        threshold_end = max_surgery_date + margin
        
        # TODO (Low) This is a bad idea. We need a better way to handle this because it leaves 
        # us with a situation where if we take 'too long' to download the DOCX files, it will presume that the DOCX files are out of range because 
        # the modfied date is a bad proxy for the date of the surgery which would be contained inside the DOCX file. The processing overhead for extracting the
        # date of the surgery from the DOCX file is non-trivial and computationally expensive so we need a smarter way to handle this.

        MediLink_ConfigLoader.log("BAD IDEA: Processing DOCX files modified between {} and {}.".format(threshold_start, threshold_end), level="INFO")

        # TIMING: Start file system operations
        filesystem_start_time = time.time()
        
        # PERFORMANCE OPTIMIZATION: Batch file system operations with caching
        # Pre-convert threshold timestamps for efficient comparison (Windows XP compatible)
        threshold_start_ts = threshold_start.timestamp() if hasattr(threshold_start, 'timestamp') else time.mktime(threshold_start.timetuple())
        threshold_end_ts = threshold_end.timestamp() if hasattr(threshold_end, 'timestamp') else time.mktime(threshold_end.timetuple())

        # Lightweight on-disk index to avoid relying on mtime for clinical windowing
        # Index format: { filename: { 'mtime': float, 'dates': ['MM-DD-YYYY', ...] } }
        index_path = os.path.join(local_storage_path, '.docx_index.json')
        docx_index = {}
        try:
            if os.path.exists(index_path):
                import json
                with open(index_path, 'r') as jf:
                    docx_index = json.load(jf)
        except Exception:
            docx_index = {}
        
        valid_files = []
        try:
            # Use os.listdir() with optimized timestamp comparison (XP/3.4.4 compatible)
            for filename in os.listdir(local_storage_path):
                if filename.endswith('.docx'):
                    filepath = os.path.join(local_storage_path, filename)
                    # Get file modification time in single operation
                    try:
                        stat_info = os.stat(filepath)
                        # Direct timestamp comparison avoids datetime conversion overhead
                        # First filter by mtime for performance
                        if not (threshold_start_ts <= stat_info.st_mtime <= threshold_end_ts):
                            continue
                        # If indexed and mtime unchanged, prefer date-based decision from index
                        rec = docx_index.get(filename)
                        if rec and isinstance(rec, dict) and abs(rec.get('mtime', 0) - stat_info.st_mtime) < MTIME_TOLERANCE:
                            # If any extracted date falls within threshold window, keep file
                            dates = rec.get('dates', []) or []
                            keep = False
                            for d in dates:
                                try:
                                    # parse 'MM-DD-YYYY' to timestamp
                                    dt = datetime.strptime(d, '%m-%d-%Y')
                                    ts = dt.timestamp() if hasattr(dt, 'timestamp') else time.mktime(dt.timetuple())
                                    if threshold_start_ts <= ts <= threshold_end_ts:
                                        keep = True
                                        break
                                except Exception:
                                    continue
                            if not keep:
                                continue
                        # mtime passes or index indicates date window match
                        valid_files.append(filepath)
                    except (OSError, ValueError):
                        # Skip files with invalid modification times
                        continue
        except OSError:
            MediLink_ConfigLoader.log("Error accessing directory: {}".format(local_storage_path), level="ERROR")
            return
            
        # TIMING: End file system operations
        filesystem_end_time = time.time()
        filesystem_duration = filesystem_end_time - filesystem_start_time
        
        # PERFORMANCE OPTIMIZATION: Log file count for debugging without processing overhead
        MediLink_ConfigLoader.log("Found {} DOCX files within date threshold".format(len(valid_files)), level="INFO")

        # TIMING: Start CSV data preprocessing
        csv_prep_start_time = time.time()
        
        # PERFORMANCE OPTIMIZATION: Pre-process patient IDs for efficient lookup
        # Create a set of patient IDs from CSV data for faster lookups
        patient_ids_in_csv = {row.get('Patient ID', '').strip() for row in csv_data}

        # PERFORMANCE OPTIMIZATION: Pre-convert surgery dates to string format
        # Convert all surgery dates to string format once to avoid repeated conversions in loops
        surgery_date_strings = {}
        for row in csv_data:
            patient_id = row.get('Patient ID', '').strip()
            surgery_date = row.get('Surgery Date')
            if surgery_date != datetime.min:
                surgery_date_strings[patient_id] = surgery_date.strftime("%m-%d-%Y")
            else:
                surgery_date_strings[patient_id] = ''
        
        # TIMING: End CSV data preprocessing
        csv_prep_end_time = time.time()
        csv_prep_duration = csv_prep_end_time - csv_prep_start_time

        # TIMING: Log before processing DOCX files
        docx_processing_start_time = time.time()
        print("Found {} DOCX files to process. Starting DOCX parsing...".format(len(valid_files)))
        MediLink_ConfigLoader.log("Found {} DOCX files to process. Starting DOCX parsing...".format(len(valid_files)), level="INFO")

        # TIMING: Track individual DOCX file processing
        docx_files_processed = 0
        docx_files_skipped = 0
        docx_parse_errors = 0

        # Process valid DOCX files
        updated_index = False
        for filepath in valid_files:
            # TIMING: Start individual file processing
            file_start_time = time.time()
            
            try:
                if SORTING_STRATEGY == 'schedule_based':
                    # Enhanced parsing to capture schedule positions
                    patient_data, schedule_positions = parse_docx(filepath, surgery_dates, capture_schedule_positions=True)  # Pass surgery_dates to parse_docx
                    # Store schedule positions for future sorting
                    for patient_id, dates in schedule_positions.items():
                        if patient_id not in all_schedule_positions:
                            all_schedule_positions[patient_id] = {}
                        all_schedule_positions[patient_id].update(dates)
                else:
                    # Standard parsing (maintains backward compatibility)
                    patient_data = parse_docx(filepath, surgery_dates, capture_schedule_positions=False)  # Pass surgery_dates to parse_docx
                
                docx_files_processed += 1
                
                # PERFORMANCE OPTIMIZATION: Use defaultdict for more efficient dictionary operations
                for patient_id, service_dates in patient_data.items():
                    if patient_id not in all_patient_data:
                        all_patient_data[patient_id] = {}
                    for date_of_service, diagnosis_data in service_dates.items():
                        # TODO: SURGERY SCHEDULE CONFLICT RESOLUTION
                        # Implement enhanced conflict detection and logging as outlined in 
                        # surgery_schedule_conflict_resolution_strategy.md
                        # 
                        # Current behavior: Silent overwriting with latest file wins
                        # Proposed enhancement:
                        # 1. Detect when multiple files contain data for same date
                        # 2. Log conflicts with date-organized notifications showing:
                        #    - Source files (with modification timestamps)
                        #    - Patients affected (added/removed/modified)
                        #    - Specific changes (diagnosis, laterality, etc.)
                        # 3. Use file modification time to determine priority
                        # 4. Generate summary report organized by surgery date
                        # 
                        # Example notification format:
                        # "SURGERY SCHEDULE CONFLICTS DETECTED FOR: 12/15/2023"
                        # "  Original: file1.docx (modified: 08:30:00)"  
                        # "  Revised: file2.docx (modified: 14:45:00)"
                        # "  Patients affected: 3 modified, 1 added, 1 removed"
                        # "  Resolution: Using latest file (file2.docx)"
                        #
                        # This will provide transparency when revised schedules overwrite 
                        # original schedules, organized by the affected surgery dates.
                        all_patient_data[patient_id][date_of_service] = diagnosis_data
                # Update index entry for this file (store union of extracted surgery dates)
                try:
                    dates_list = []
                    for _pid, _dates in patient_data.items():
                        for _dos in _dates.keys():
                            dates_list.append(_dos)
                    if dates_list:
                        filename = os.path.basename(filepath)
                        stat_info = os.stat(filepath)
                        docx_index[filename] = {
                            'mtime': stat_info.st_mtime,
                            'dates': sorted(list(set(dates_list)))
                        }
                        updated_index = True
                except Exception:
                    pass
            except Exception as e:
                docx_parse_errors += 1
                MediLink_ConfigLoader.log("Error parsing DOCX file {}: {}".format(filepath, e), level="ERROR")
            
            # TIMING: End individual file processing
            file_end_time = time.time()
            file_duration = file_end_time - file_start_time
            
            # Log slow files (taking more than 1 second)
            if file_duration > 1.0 and PERFORMANCE_LOGGING:
                print("  - Slow file: {} (Duration: {:.2f} seconds)".format(os.path.basename(filepath), file_duration))

        # Write index back if updated
        if updated_index:
            try:
                import json
                with open(index_path, 'w') as jf:
                    json.dump(docx_index, jf)
            except Exception:
                pass

        # TIMING: Log DOCX processing completion
        docx_processing_end_time = time.time()
        docx_processing_duration = docx_processing_end_time - docx_processing_start_time
        if PERFORMANCE_LOGGING:
            print("DOCX parsing completed at: {} (Duration: {:.2f} seconds)".format(
                time.strftime("%H:%M:%S"), docx_processing_duration))
            print("  - Files processed: {}, Files skipped: {}, Parse errors: {}".format(
                docx_files_processed, docx_files_skipped, docx_parse_errors))
        MediLink_ConfigLoader.log("DOCX parsing completed at: {} (Duration: {:.2f} seconds)".format(
            time.strftime("%H:%M:%S"), docx_processing_duration), level="INFO")

        # Log if no valid files were found
        if not valid_files:
            MediLink_ConfigLoader.log("No valid DOCX files found within the modification time threshold.", level="INFO")
        
        # Debug logging for all_patient_data
        MediLink_ConfigLoader.log("All patient data collected from DOCX files: {}".format(all_patient_data), level="DEBUG")
        
        # Check if any patient data was collected
        if not all_patient_data or not patient_ids_in_csv.intersection(all_patient_data.keys()):
            MediLink_ConfigLoader.log("No patient data collected or no matching Patient IDs found. Skipping further processing.", level="INFO")
            return  # Exit the function early if no data is available

        # TIMING: Start CSV data matching
        csv_matching_start_time = time.time()

        # Get Medisoft shorthand dictionary from crosswalk.
        diagnosis_to_medisoft = crosswalk.get('diagnosis_to_medisoft', {})
        
        # Initialize counter for updated rows
        updated_count = 0

        # PERFORMANCE OPTIMIZATION: Single pass through CSV data with pre-processed lookups
        # Update the "Default Diagnosis #1" column in the CSV data and store diagnosis codes for all surgery dates
        for row_num, row in enumerate(csv_data, start=1):
            patient_id = row.get('Patient ID', '').strip()
            # Use pre-processed patient ID lookup for efficiency
            if patient_id not in patient_ids_in_csv:
                continue  # Skip rows that do not match any patient ID

            MediLink_ConfigLoader.log("Processing row number {}.".format(row_num), level="DEBUG")
            
            # Get all surgery dates for this patient
            all_surgery_dates = row.get('_all_surgery_dates', [row.get('Surgery Date')])
            
            # Create a mapping of surgery dates to diagnosis codes for this patient
            surgery_date_to_diagnosis = {}
            
            if patient_id in all_patient_data:
                # Process each surgery date for this patient
                for surgery_date in all_surgery_dates:
                    # Convert surgery date to string format for lookup
                    try:
                        if hasattr(surgery_date, 'strftime'):
                            surgery_date_str = surgery_date.strftime('%m-%d-%Y')
                        else:
                            surgery_date_str = str(surgery_date)
                    except Exception:
                        surgery_date_str = str(surgery_date)
                    
                    MediLink_ConfigLoader.log("Patient ID: {}, Surgery Date: {}".format(patient_id, surgery_date_str), level="DEBUG")

                    if surgery_date_str in all_patient_data[patient_id]:
                        diagnosis_data = all_patient_data[patient_id][surgery_date_str]
                        # XP SP3 + Py3.4.4 compatible tuple unpacking with safety check
                        try:
                            if isinstance(diagnosis_data, (list, tuple)) and len(diagnosis_data) >= 3:
                                diagnosis_code, left_or_right_eye, femto_yes_or_no = diagnosis_data
                            else:
                                # Handle case where diagnosis_data is not a proper tuple
                                diagnosis_code = diagnosis_data if diagnosis_data else None
                                left_or_right_eye = None
                                femto_yes_or_no = None
                        except Exception as e:
                            MediLink_ConfigLoader.log("Error unpacking diagnosis data for Patient ID: {}, Surgery Date: {}: {}".format(
                                patient_id, surgery_date_str, str(e)), level="WARNING")
                            diagnosis_code = None
                            left_or_right_eye = None
                            femto_yes_or_no = None
                        
                        MediLink_ConfigLoader.log("Found diagnosis data for Patient ID: {}, Surgery Date: {}".format(patient_id, surgery_date_str), level="DEBUG")
                        
                        # Convert diagnosis code to Medisoft shorthand format.
                        # XP SP3 + Py3.4.4 compatible null check
                        if diagnosis_code is None:
                            medisoft_shorthand = 'N/A'
                            MediLink_ConfigLoader.log("Diagnosis code is None for Patient ID: {}, Surgery Date: {}".format(
                                patient_id, surgery_date_str), level="WARNING")
                        else:
                            # TODO(MediBot Diagnosis Intake):
                            # Today we silently fall back to an auto-generated Medisoft shorthand when the
                            # DOCX delivers a diagnosis code that is missing from crosswalk['diagnosis_to_medisoft'].
                            # That fallback lets the flow continue, but Medisoft rejects the unknown code and
                            # starts prompting the user in the middle of the automation. We need to capture the
                            # new diagnosis codes observed here, compare them against crosswalk dictionaries, and
                            # (ideally early in the MediCafe flow) ask the user how to proceed:
                            #   1. Confirm which procedure bucket from crosswalk['procedure_to_diagnosis'] (e.g. 00142,
                            #      00145, 00140) the new diagnosis should belong to or allow typing a new procedure.
                            #   2. Offer to auto-generate a `diagnosis_to_medisoft` shorthand that the user can accept
                            #      or edit, and write a pending TODO reminding them to create the same shorthand inside
                            #      Medisoft before automation resumes.
                            #   3. Persist the accepted mapping back into crosswalk.json so subsequent runs stay in sync.
                            # Without that workflow, brute-force AHK typing keeps crashing into the Medisoft prompt.
                            medisoft_shorthand = diagnosis_to_medisoft.get(diagnosis_code, None)
                            if medisoft_shorthand is None and diagnosis_code:
                                # Use fallback logic for missing mapping (XP SP3 + Py3.4.4 compatible)
                                try:
                                    defaulted_code = diagnosis_code.lstrip('H').lstrip('T8').replace('.', '')[-5:]
                                    # Basic validation: ensure code is not empty and has reasonable length
                                    if defaulted_code and len(defaulted_code) >= 3:
                                        medisoft_shorthand = defaulted_code
                                        MediLink_ConfigLoader.log("Missing diagnosis mapping for '{}', using fallback code '{}'".format(
                                            diagnosis_code, medisoft_shorthand), level="WARNING")
                                    else:
                                        medisoft_shorthand = 'N/A'
                                        MediLink_ConfigLoader.log("Fallback diagnosis code validation failed for '{}', using 'N/A'".format(
                                            diagnosis_code), level="WARNING")
                                except Exception as e:
                                    medisoft_shorthand = 'N/A'
                                    MediLink_ConfigLoader.log("Error in fallback diagnosis code generation for '{}': {}".format(
                                        diagnosis_code, str(e)), level="WARNING")
                        
                        MediLink_ConfigLoader.log("Converted diagnosis code to Medisoft shorthand: {}".format(medisoft_shorthand), level="DEBUG")
                        
                        surgery_date_to_diagnosis[surgery_date_str] = medisoft_shorthand
                    else:
                        MediLink_ConfigLoader.log("No matching surgery date found for Patient ID: {} on date {}.".format(patient_id, surgery_date_str), level="INFO")
                        surgery_date_to_diagnosis[surgery_date_str] = 'N/A'
                
                # Store the diagnosis mapping for all surgery dates
                row['_surgery_date_to_diagnosis'] = surgery_date_to_diagnosis
                
                # NEW: Store schedule positions for future sorting if available
                if SORTING_STRATEGY == 'schedule_based' and patient_id in all_schedule_positions:
                    row['_schedule_positions'] = all_schedule_positions[patient_id]
                
                # Set the primary diagnosis code (for the main surgery date)
                primary_surgery_date = row.get('Surgery Date')
                # Convert primary surgery date to string for lookup
                if isinstance(primary_surgery_date, datetime):
                    primary_surgery_date_str = primary_surgery_date.strftime('%m-%d-%Y')
                else:
                    primary_surgery_date_str = str(primary_surgery_date)
                primary_diagnosis = surgery_date_to_diagnosis.get(primary_surgery_date_str, 'N/A')
                row['Default Diagnosis #1'] = primary_diagnosis
                
                updated_count += 1
                MediLink_ConfigLoader.log("Updated row number {} with diagnosis codes for {} surgery dates.".format(row_num, len(all_surgery_dates)), level="INFO")
            else:
                MediLink_ConfigLoader.log("Patient ID: {} not found in DOCX data for row {}.".format(patient_id, row_num), level="INFO")

        # TIMING: End CSV data matching
        csv_matching_end_time = time.time()
        csv_matching_duration = csv_matching_end_time - csv_matching_start_time

        # Log total count of updated rows
        MediLink_ConfigLoader.log("Total {} 'Default Diagnosis #1' rows updated.".format(updated_count), level="INFO")

        # TIMING: End surgery schedule parsing timing
        parsing_end_time = time.time()
        parsing_duration = parsing_end_time - parsing_start_time
        if PERFORMANCE_LOGGING:
            print("Surgery schedule parsing completed at: {} (Duration: {:.2f} seconds)".format(
                time.strftime("%H:%M:%S"), parsing_duration))
            print("  - File system operations: {:.2f} seconds ({:.1f}%)".format(filesystem_duration, (filesystem_duration/parsing_duration)*100))
            print("  - CSV data preprocessing: {:.2f} seconds ({:.1f}%)".format(csv_prep_duration, (csv_prep_duration/parsing_duration)*100))
            print("  - DOCX file processing: {:.2f} seconds ({:.1f}%)".format(docx_processing_duration, (docx_processing_duration/parsing_duration)*100))
            print("  - CSV data matching: {:.2f} seconds ({:.1f}%)".format(csv_matching_duration, (csv_matching_duration/parsing_duration)*100))
            print("  - Files processed: {}, Files skipped: {}, Parse errors: {}".format(docx_files_processed, docx_files_skipped, docx_parse_errors))
        MediLink_ConfigLoader.log("Surgery schedule parsing completed at: {} (Duration: {:.2f} seconds)".format(
            time.strftime("%H:%M:%S"), parsing_duration), level="INFO")

    except Exception as e:
        message = "An error occurred while updating diagnosis codes. Please check the DOCX files and configuration: {}".format(e)
        MediLink_ConfigLoader.log(message, level="ERROR")
        print(message)

def load_data_sources(config, crosswalk):
    """Loads historical mappings from MAPAT and Carol's CSVs."""
    patient_id_to_insurance_id = load_insurance_data_from_mapat(config, crosswalk)
    if not patient_id_to_insurance_id:
        raise ValueError("Failed to load historical Patient ID to Insurance ID mappings from MAPAT.")

    payer_id_to_patient_ids = load_historical_payer_to_patient_mappings(config)
    if not payer_id_to_patient_ids:
        raise ValueError("Failed to load historical Carol's CSVs.")

    return patient_id_to_insurance_id, payer_id_to_patient_ids

def map_payer_ids_to_insurance_ids(patient_id_to_insurance_id, payer_id_to_patient_ids):
    """Maps Payer IDs to Insurance IDs based on the historical mappings."""
    payer_id_to_details = {}
    for payer_id, patient_ids in payer_id_to_patient_ids.items():
        medisoft_ids = set()
        for patient_id in patient_ids:
            if patient_id in patient_id_to_insurance_id:
                medisoft_id = patient_id_to_insurance_id[patient_id]
                medisoft_ids.add(medisoft_id)
                MediLink_ConfigLoader.log("Added Medisoft ID {} for Patient ID {} and Payer ID {}".format(medisoft_id, patient_id, payer_id))
            else:
                MediLink_ConfigLoader.log("No matching Insurance ID found for Patient ID {}".format(patient_id))
        if medisoft_ids:
            # Read default endpoint from cached configuration (maintains existing OPTUMEDI behavior)
            try:
                cfg, _cw = get_cached_configuration()
            except Exception:
                cfg = {}
            default_ep = _get_default_endpoint(cfg)
            payer_id_to_details[payer_id] = {
                "endpoint": default_ep,
                "medisoft_id": list(medisoft_ids),
                "medisoft_medicare_id": []  # Placeholder for future implementation
            }
    return payer_id_to_details

def _display_mains_file_error(mains_path):
    """
    Helper function to display the critical MAINS file error message.
    
    Args:
        mains_path (str): The path where the MAINS file was expected to be found.
    """
    error_msg = "CRITICAL: MAINS file not found at: {}. This file is required for insurance name to Medisoft ID mapping.".format(mains_path)
    if hasattr(MediLink_ConfigLoader, 'log'):
        MediLink_ConfigLoader.log(error_msg, level="CRITICAL")
    print("\n" + "="*80)
    print("CRITICAL ERROR: MAINS FILE MISSING")
    print("="*80)
    print("\nThe MAINS file is required for the following critical functions:")
    print("* Mapping insurance company names to Medisoft IDs")
    print("* Converting insurance names to payer IDs for claim submission")
    print("* Creating properly formatted 837p claim files")
    print("\nWithout this file, claim submission will fail because:")
    print("* Insurance names cannot be converted to payer IDs")
    print("* 837p claim files cannot be generated")
    print("* Claims cannot be submitted to insurance companies")
    print("\nTO FIX THIS:")
    print("1. Ensure the MAINS file exists at: {}".format(mains_path))
    print("2. If the file is missing, llamar a Dani")
    print("3. The file should contain insurance company data from your Medisoft system")
    print("="*80)
    time.sleep(3)  # 3 second pause to allow user to read critical error message


def load_insurance_data_from_mains(config):
    """
    Loads insurance data from MAINS and creates a mapping from insurance names to their respective IDs.
    This mapping is critical for the crosswalk update process to correctly associate payer IDs with insurance IDs.

    Args:
        config (dict): Configuration object containing necessary paths and parameters.

    Returns:
        dict: A dictionary mapping insurance names to insurance IDs.
    """
    # Use cached configuration to avoid repeated loading
    try:
        config, crosswalk = get_cached_configuration()
    except Exception as e:
        print("Warning: Failed to load cached configuration: {}".format(e))
        # Return empty mapping if configuration loading fails
        return {}
    
    # XP Compatibility: Check if MediLink_DataMgmt is available
    if MediLink_DataMgmt is None:
        print("Warning: MediLink_DataMgmt not available. Cannot load MAINS data.")
        return {}
    
    # Retrieve MAINS path and slicing information from the configuration
    # TODO (Low) For secondary insurance, this needs to be pulling from the correct MAINS (there are 2)
    # TODO (Low) Performance: There probably needs to be a dictionary proxy for MAINS that gets updated.
    # TODO (High) The Medisoft Medicare flag needs to be brought in here.
    try:
        mains_path = config.get('MAINS_MED_PATH', '')
        mains_slices = crosswalk.get('mains_mapping', {}).get('slices', {})
    except (KeyError, AttributeError) as e:
        print("Warning: Failed to get MAINS configuration: {}".format(e))
        return {}
    
    # Initialize the dictionary to hold the insurance to insurance ID mappings
    insurance_to_id = {}
    
    try:
        # Check if MAINS file exists before attempting to read
        if not os.path.exists(mains_path):
            _display_mains_file_error(mains_path)
            return insurance_to_id
        
        # XP Compatibility: Check if MediLink_DataMgmt has the required function
        if not hasattr(MediLink_DataMgmt, 'read_general_fixed_width_data'):
            print("Warning: MediLink_DataMgmt.read_general_fixed_width_data not available. Cannot load MAINS data.")
            return insurance_to_id
        
        # Read data from MAINS using a provided function to handle fixed-width data
        for record, line_number in MediLink_DataMgmt.read_general_fixed_width_data(mains_path, mains_slices):
            insurance_name = record['MAINSNAME']
            # Assuming line_number gives the correct insurance ID without needing adjustment
            insurance_to_id[insurance_name] = line_number
        
        if hasattr(MediLink_ConfigLoader, 'log'):
            MediLink_ConfigLoader.log("Successfully loaded {} insurance records from MAINS".format(len(insurance_to_id)), level="INFO")
        else:
            print("Successfully loaded {} insurance records from MAINS".format(len(insurance_to_id)))
        
    except FileNotFoundError:
        _display_mains_file_error(mains_path)
    except Exception as e:
        error_msg = "Error loading MAINS data: {}. Continuing without MAINS data.".format(str(e))
        if hasattr(MediLink_ConfigLoader, 'log'):
            MediLink_ConfigLoader.log(error_msg, level="ERROR")
        print("Error loading MAINS data: {}. Continuing without MAINS data.".format(str(e)))
    
    return insurance_to_id

def load_insurance_data_from_mapat(config, crosswalk):
    """
    Loads insurance data from MAPAT and creates a mapping from patient ID to insurance ID.
    
    Args:
        config (dict): Configuration object containing necessary paths and parameters.
        crosswalk (dict): Crosswalk data containing mapping information.

    Returns:
        dict: A dictionary mapping patient IDs to insurance IDs.
    """
    # Retrieve MAPAT path and slicing information from the configuration
    ac = _ac()
    mapat_path = ac.get_mapat_med_path() if ac else ''
    mapat_slices = crosswalk['mapat_mapping']['slices']
    
    # Initialize the dictionary to hold the patient ID to insurance ID mappings
    patient_id_to_insurance_id = {}
    
    # Read data from MAPAT using a provided function to handle fixed-width data
    for record, _ in MediLink_DataMgmt.read_general_fixed_width_data(mapat_path, mapat_slices):
        patient_id = record['MAPATPXID']
        insurance_id = record['MAPATINID']
        patient_id_to_insurance_id[patient_id] = insurance_id
        
    return patient_id_to_insurance_id

def parse_z_dat(z_dat_path, config):
    # TODO: Consider moving this to MediLink module
    """
    Parses the Z.dat file to map Patient IDs to Insurance Names using the provided fixed-width file format.

    Args:
        z_dat_path (str): Path to the Z.dat file.
        config (dict): Configuration object containing slicing information and other parameters.

    Returns:
        dict: A dictionary mapping Patient IDs to Insurance Names.
    """
    patient_id_to_insurance_name = {}

    try:
        # Reading blocks of fixed-width data (up to 5 lines per record)
        for personal_info, insurance_info, service_info, service_info_2, service_info_3 in MediLink_DataMgmt.read_fixed_width_data(z_dat_path):
            # Parse Z.dat reserved record format: 3 active + 2 reserved lines
            parsed_data = MediLink_DataMgmt.parse_fixed_width_data(personal_info, insurance_info, service_info, service_info_2, service_info_3, config.get('MediLink_Config', config))

            # Extract Patient ID and Insurance Name from parsed data
            patient_id = parsed_data.get('PATID')
            insurance_name = parsed_data.get('INAME')

            if patient_id and insurance_name:
                patient_id_to_insurance_name[patient_id] = insurance_name
                MediLink_ConfigLoader.log("Mapped Patient ID {} to Insurance Name {}".format(patient_id, insurance_name), config, level="INFO")

    except FileNotFoundError:
        MediLink_ConfigLoader.log("File not found: {}".format(z_dat_path), config, level="INFO")
    except Exception as e:
        MediLink_ConfigLoader.log("Failed to parse Z.dat: {}".format(str(e)), config, level="INFO")

    return patient_id_to_insurance_name

def load_historical_payer_to_patient_mappings(config):
    """
    Loads historical mappings from multiple Carol's CSV files in a specified directory,
    mapping Payer IDs to sets of Patient IDs.

    Args:
        config (dict): Configuration object containing the directory path for Carol's CSV files
                       and other necessary parameters.

    Returns:
        dict: A dictionary where each key is a Payer ID and the value is a set of Patient IDs.
    """
    directory_path = os.path.dirname(config['CSV_FILE_PATH'])
    payer_to_patient_ids = defaultdict(set)

    try:
        # Check if the directory exists
        if not os.path.isdir(directory_path):
            raise FileNotFoundError("Directory '{}' not found.".format(directory_path))

        # Loop through each file in the directory containing Carol's historical CSVs
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if filename.endswith('.csv'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        patient_count = 0  # Counter for Patient IDs found in this CSV
                        for row in reader:
                            if 'Patient ID' not in row or 'Ins1 Payer ID' not in row:
                                continue  # Skip this row if either key is missing
                            if not row.get('Patient ID').strip() or not row.get('Ins1 Payer ID').strip():
                                continue  # Skip this row if either value is missing or empty
                            
                            payer_id = row['Ins1 Payer ID'].strip()
                            patient_id = row['Patient ID'].strip()
                            payer_to_patient_ids[payer_id].add(patient_id)
                            patient_count += 1  # Increment the counter for each valid mapping
                        
                        # Log the accumulated count for this CSV file
                        if patient_count > 0:
                            MediLink_ConfigLoader.log("CSV file '{}' has {} Patient IDs with Payer IDs.".format(filename, patient_count), level="DEBUG")
                        else:
                            MediLink_ConfigLoader.log("CSV file '{}' is empty or does not have valid Patient ID or Payer ID mappings.".format(filename), level="DEBUG")
                except Exception as e:
                    print("Error processing file {}: {}".format(filename, e))
                    MediLink_ConfigLoader.log("Error processing file '{}': {}".format(filename, e), level="ERROR")
    except FileNotFoundError as e:
        print("Error: {}".format(e))

    if not payer_to_patient_ids:
        print("No historical mappings were generated.")
    
    return dict(payer_to_patient_ids)

def capitalize_all_fields(csv_data):
    """
    Converts all text fields in the CSV data to uppercase.
    
    Parameters:
    csv_data (list of dict): The CSV data where each row is represented as a dictionary.
    
    Returns:
    None: The function modifies the csv_data in place.
    """
    # PERFORMANCE FIX: Optimize uppercase conversion while preserving complex types
    for row in csv_data:
        updated_row = {}
        for key, value in row.items():
            # Preserve internal/derived fields intact (e.g., `_all_surgery_dates`, `_surgery_date_to_diagnosis`)
            if isinstance(key, str) and key.startswith('_'):
                updated_row[key] = value
                continue
            # Uppercase plain strings
            if isinstance(value, str):
                updated_row[key] = value.upper()
                continue
            # Preserve complex containers; optionally uppercase their string contents
            if isinstance(value, list):
                updated_row[key] = [elem.upper() if isinstance(elem, str) else elem for elem in value]
                continue
            if isinstance(value, dict):
                updated_row[key] = {k: (v.upper() if isinstance(v, str) else v) for k, v in value.items()}
                continue
            # Leave datetimes as-is; coerce simple scalars to string upper for consistency
            if isinstance(value, datetime):
                updated_row[key] = value
            else:
                updated_row[key] = str(value).upper() if value is not None else value
        row.update(updated_row)