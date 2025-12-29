import csv, os, re, subprocess, time
from datetime import datetime, timedelta

# Import centralized logging configuration
try:
    from MediCafe.logging_config import PERFORMANCE_LOGGING
except ImportError:
    # Fallback to local flag if centralized config is not available
    PERFORMANCE_LOGGING = False

# Need this for running Medibot and MediLink
from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config
MediLink_ConfigLoader = get_shared_config_loader()
try:
    import MediLink_Display_Utils
except ImportError:
    from MediLink import MediLink_Display_Utils

# Module-level flag to control skipping API-sourced insurance types during bulk edit
# Set to False to allow editing of API-sourced patients (useful for debugging)
# NOTE: API-sourced codes not in insurance_options will always be shown regardless of this flag
SKIP_API_SOURCED_INSURANCE_EDIT = True

# Import validation function
try:
    from MediLink.MediLink_insurance_utils import validate_insurance_type_from_config
except ImportError:
    validate_insurance_type_from_config = None

# MediBot imports will be done locally in functions to avoid circular imports
def _get_medibot_function(module_name, function_name):
    """Dynamically import MediBot functions when needed to avoid circular imports."""
    try:
        module = __import__('MediBot.{}'.format(module_name), fromlist=[function_name])
        return getattr(module, function_name)
    except (ImportError, AttributeError):
        return None

# Helper function to slice and strip values with optional key suffix
def slice_data(data, slices, suffix=''):
    # Convert slices list to a tuple for slicing operation
    return {key + suffix: data[slice(*slices[key])].strip() for key in slices}

# Function to parse fixed-width Medisoft output and extract claim data
def parse_fixed_width_data(personal_info, insurance_info, service_info, service_info_2=None, service_info_3=None, config=None):
    
    # Make sure we have the right config
    if not config:  # Checks if config is None or an empty dictionary
        MediLink_ConfigLoader.log("No config passed to parse_fixed_width_data. Re-loading config...", level="WARNING")
        config, _ = MediLink_ConfigLoader.load_configuration()
    
    medi = extract_medilink_config(config)
    
    # Load slice definitions from config within the MediLink_Config section
    personal_slices = medi['fixedWidthSlices']['personal_slices']
    insurance_slices = medi['fixedWidthSlices']['insurance_slices']
    service_slices = medi['fixedWidthSlices']['service_slices']

    # Parse each segment - core 3-line record structure
    parsed_data = {}
    parsed_data.update(slice_data(personal_info, personal_slices))    # Line 1: Personal info
    parsed_data.update(slice_data(insurance_info, insurance_slices))  # Line 2: Insurance info
    parsed_data.update(slice_data(service_info, service_slices))      # Line 3: Service info
    
    # Parse reserved expansion lines (future-ready design)
    if service_info_2:  # Line 4: Reserved for additional service data
        parsed_data.update(slice_data(service_info_2, service_slices, suffix='_2'))
    
    if service_info_3:  # Line 5: Reserved for additional service data
        parsed_data.update(slice_data(service_info_3, service_slices, suffix='_3'))
    
    # Replace underscores with spaces in first and last names since this is downstream of MediSoft. 
    if 'FIRST' in parsed_data:
        parsed_data['FIRST'] = parsed_data['FIRST'].replace('_', ' ')
    if 'LAST' in parsed_data:
        parsed_data['LAST'] = parsed_data['LAST'].replace('_', ' ')
    
    MediLink_ConfigLoader.log("Successfully parsed data from segments", config, level="DEBUG")
    
    return parsed_data

# Function to read fixed-width Medisoft output and extract claim data
def read_fixed_width_data(file_path):
    """
    Legacy function maintained for backward compatibility.
    Reads fixed-width Medisoft data with RESERVED 5-line patient record format.
    
    DESIGN NOTE: This implements a reserved record structure where each patient
    record can contain 3-5 lines (currently using 3, with 2 reserved for future expansion).
    The peek-ahead logic is intentional to handle variable-length records and maintain
    proper spacing between patient records.
    """
    # Use the consolidated function with Medisoft-specific configuration
    medisoft_config = {
        'mode': 'medisoft_records',
        'min_lines': 3,
        'max_lines': 5,
        'skip_header': False
    }
    return read_consolidated_fixed_width_data(file_path, config=medisoft_config)

def read_general_fixed_width_data(file_path, slices):
    """
    Legacy function maintained for backward compatibility.
    Handles fixed-width data based on provided slice definitions.
    """
    # Use the consolidated function with slice-based configuration
    slice_config = {
        'mode': 'slice_based',
        'slices': slices,
        'skip_header': True
    }
    return read_consolidated_fixed_width_data(file_path, config=slice_config)

# CONSOLIDATED IMPLEMENTATION - Replaces both read_fixed_width_data and read_general_fixed_width_data
def read_consolidated_fixed_width_data(file_path, config=None):
    """
    Unified function for reading various fixed-width data formats.
    
    Parameters:
    - file_path: Path to the fixed-width data file
    - config: Configuration dictionary with the following keys:
        - mode: 'medisoft_records' (reserved 5-line format) or 'slice_based'
        - slices: Dictionary of field slices (for slice_based mode)
        - skip_header: Boolean, whether to skip first line
        - min_lines: Minimum lines per record (for medisoft_records mode)
        - max_lines: Maximum lines per record (for medisoft_records mode)
    
    Returns:
    - Generator yielding parsed records based on the specified mode
    """
    if config is None:
        config = {'mode': 'medisoft_records', 'min_lines': 3, 'max_lines': 5, 'skip_header': False}
    
    mode = config.get('mode', 'medisoft_records')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Skip header if configured
            if config.get('skip_header', False):
                next(file)
            
            if mode == 'medisoft_records':
                # Handle Medisoft reserved 5-line patient record format
                yield from _process_medisoft_records(file, file_path, config)
            elif mode == 'slice_based':
                # Handle slice-based field extraction
                yield from _process_slice_based_records(file, file_path, config)
            else:
                raise ValueError("Invalid mode '{}'. Use 'medisoft_records' or 'slice_based'".format(mode))
                
    except FileNotFoundError:
        print("File not found: {}".format(file_path))
        MediLink_ConfigLoader.log("File not found: {}".format(file_path), level="ERROR")
        return

def _process_medisoft_records(file, file_path, config):
    """Helper function to process Medisoft-style multi-line patient records
    
    RECORD FORMAT DESIGN (RESERVED 5-LINE STRUCTURE):
    ════════════════════════════════════════════════════════════════
    Each patient record is designed as a RESERVED 5-line block:
    
    Line 1: Personal Info     (REQUIRED - Always present)
    Line 2: Insurance Info    (REQUIRED - Always present)  
    Line 3: Service Info      (REQUIRED - Always present)
    Line 4: Service Info 2    (RESERVED - Future expansion)
    Line 5: Service Info 3    (RESERVED - Future expansion)
    [Blank line]             (Record separator)
    
    CURRENT PRODUCTION STATE:
    ────────────────────────────
    - Currently using: 3 active lines per record
    - Lines 4-5: Reserved for future service data expansion
    - Blank lines: Maintain proper record separation
    - Total: 5-line reserved format ready for expansion
    
    PEEK-AHEAD LOGIC PURPOSE:
    ────────────────────────────
    The peek-ahead logic serves to:
    1. Detect when we've reached the end of a record (blank line)
    2. Allow for future expansion to 4-5 lines without code changes
    3. Maintain proper spacing between patient records
    4. Handle variable-length records (3-5 lines) gracefully
    
    FUTURE EXPANSION READY:
    ────────────────────────────
    When additional service lines are needed:
    - No code changes required in reader logic
    - Parser automatically handles service_info_2 and service_info_3
    - Slice definitions can be extended in configuration
    - Maintains backward compatibility with 3-line records
    ════════════════════════════════════════════════════════════════
    """
    MediLink_ConfigLoader.log("Starting to read fixed width data...")
    MediLink_ConfigLoader.log("Successfully read data from file: {}".format(file_path), level="INFO")
    lines_buffer = []  # Buffer to hold lines for current patient data
    min_lines = config.get('min_lines', 3)
    max_lines = config.get('max_lines', 5)
    
    # Helper function to extract record from buffer (reduces code duplication)
    def extract_record(buffer):
        """Extract record tuple from buffer, handling variable-length records (3-5 lines)."""
        personal_info = buffer[0]        # Line 1: Always present (personal data)
        insurance_info = buffer[1]       # Line 2: Always present (insurance data)
        service_info = buffer[2]         # Line 3: Always present (primary service data)
        service_info_2 = buffer[3] if len(buffer) > 3 else None  # Line 4: Reserved (future expansion)
        service_info_3 = buffer[4] if len(buffer) > 4 else None  # Line 5: Reserved (future expansion)
        return personal_info, insurance_info, service_info, service_info_2, service_info_3
    
    # Use readline() consistently to avoid iterator mixing issues
    # Maintain a look-ahead buffer for proper peek-ahead functionality
    look_ahead = None
    
    while True:
        # Get next line: use look-ahead if available, otherwise read from file
        if look_ahead is not None:
            line = look_ahead
            look_ahead = None
        else:
            line = file.readline()
            if not line:  # End of file
                break
        
        stripped_line = line.strip()
        
        if stripped_line:
            # Non-blank line: add to buffer
            lines_buffer.append(stripped_line)
            
            # Check if we're within the reserved record size (3-5 lines)
            if min_lines <= len(lines_buffer) <= max_lines:
                # Peek ahead to detect record boundary (intentional design)
                next_line = file.readline()
                if not next_line:
                    # End of file - yield complete record
                    yield extract_record(lines_buffer)
                    lines_buffer.clear()
                    break
                
                next_stripped = next_line.strip()
                if not next_stripped:
                    # Found record separator (blank line) - yield complete record
                    yield extract_record(lines_buffer)
                    lines_buffer.clear()
                    # Don't store the blank line in look_ahead, just continue
                else:
                    # Next line has content - check if we can add it without exceeding max_lines
                    if len(lines_buffer) < max_lines:
                        # Store in look_ahead for next iteration
                        # This handles future expansion to 4-5 line records
                        look_ahead = next_line
                    else:
                        # Buffer already at max_lines, yield current record and start new one
                        yield extract_record(lines_buffer)
                        lines_buffer.clear()
                        # Store the peeked line for next record
                        look_ahead = next_line
        else:
            # Blank line encountered - end of current record
            if len(lines_buffer) >= min_lines:
                yield extract_record(lines_buffer)
                lines_buffer.clear()
                
    # Yield any remaining buffer if file ends without a blank line
    # Only yield if buffer has minimum required lines
    if len(lines_buffer) >= min_lines:
        yield extract_record(lines_buffer)

def _process_slice_based_records(file, file_path, config):
    """Helper function to process slice-based field extraction"""
    slices = config.get('slices', {})
    for line_number, line in enumerate(file, start=1):
        extracted_data = {key: line[start:end].strip() for key, (start, end) in slices.items()}
        yield extracted_data, line_number

# REFACTORING STATUS: COMPLETED - Legacy functions are PERMANENT compatibility layers
# 
# Consolidated read_fixed_width_data and read_general_fixed_width_data into
# read_consolidated_fixed_width_data with unified configuration-based approach.
# Legacy wrapper functions are maintained as PERMANENT compatibility layers (not temporary shims).
# 
# DESIGN NOTE: The reserved 5-line record format is intentional architecture:
# - Lines 1-3: Active data (personal, insurance, service)  
# - Lines 4-5: Reserved for future service expansion
# - Peek-ahead logic maintains proper record spacing and handles variable-length records
# 
# IMPLEMENTATION STATUS & RATIONALE:
# - Primary value achieved: Single consolidated implementation provides unified parsing and logging
#   behavior across MediLink UI, MediBot preprocessors, MediCafe CLI, and 837 encoder.
#   This reduces per-module parser drift and keeps config slice tweaks centralized.
# 
# - Legacy functions MUST remain: They provide type-safe APIs with incompatible return signatures:
#   * read_fixed_width_data: Returns 5-tuples (personal_info, insurance_info, service_info, 
#     service_info_2, service_info_3) for Medisoft record format
#   * read_general_fixed_width_data: Returns 2-tuples (extracted_data, line_number) for 
#     slice-based extraction
#   These cannot be unified without breaking all existing callers.
# 
# - Active callers (verified):
#   * read_fixed_width_data: MediLink_837p_encoder.py:256, MediLink_UI.py:150, 
#     MediLink_PatientProcessor.py:359 (all expect 5-tuple unpacking)
#   * read_general_fixed_width_data: MediBot_Preprocessor_lib.py:1803 (expects 2-tuple unpacking)
#   * MediCafe/__main__.py:59 validates both functions exist at startup
# 
# - Risk assessment: HIGH if legacy functions removed. Removing them would cause:
#   * ValueError: too many/few values to unpack in all callers
#   * Startup validation failures in MediCafe/__main__.py
#   * Breaking changes across 5+ files with no clear benefit
# 
# - Legacy wrappers are minimal (3-4 lines each) and correctly delegate to consolidated function.
#   They provide clear, type-safe APIs for each use case with no performance or maintenance burden.
#   Recommendation: Keep permanently as intentional compatibility layers.

def consolidate_csvs(source_directory, file_prefix="Consolidated", interactive=False):
    """
    Consolidate CSV files in the source directory into a single CSV file.
    
    Parameters:
        source_directory (str): The directory containing the CSV files to consolidate.
        file_prefix (str): The prefix for the consolidated file's name.
        interactive (bool): If True, prompt the user for confirmation before overwriting existing files.
    
    Returns:
        str: The filepath of the consolidated CSV file, or None if no files were consolidated.
    """
    today = datetime.now()
    consolidated_filename = "{}_{}.csv".format(file_prefix, today.strftime("%m%d%y"))
    consolidated_filepath = os.path.join(source_directory, consolidated_filename)

    consolidated_data = []
    header_saved = False
    expected_header = None

    # Check if the file already exists and log the action
    if os.path.exists(consolidated_filepath):
        MediLink_ConfigLoader.log("The file {} already exists. It will be overwritten.".format(consolidated_filename), level="INFO")
        if interactive:
            overwrite = input("The file {} already exists. Do you want to overwrite it? (y/n): ".format(consolidated_filename)).strip().lower()
            if overwrite != 'y':
                MediLink_ConfigLoader.log("User opted not to overwrite the file {}.".format(consolidated_filename), level="INFO")
                return None

    for filename in os.listdir(source_directory):
        filepath = os.path.join(source_directory, filename)
        if not filepath.endswith('.csv') or os.path.isdir(filepath) or filepath == consolidated_filepath:
            continue  # Skip non-CSV files, directories, and the target consolidated file itself

        # Check if the file was created within the last day
        modification_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        if modification_time < today - timedelta(days=1):
            continue  # Skip files not modified in the last day

        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # Read the header
                if not header_saved:
                    expected_header = header
                    consolidated_data.append(header)
                    header_saved = True
                elif header != expected_header:
                    MediLink_ConfigLoader.log("Header mismatch in file {}. Skipping file.".format(filepath), level="WARNING")
                    continue

                consolidated_data.extend(row for row in reader)
        except StopIteration:
            MediLink_ConfigLoader.log("File {} is empty or contains only header. Skipping file.".format(filepath), level="WARNING")
            continue
        except Exception as e:
            MediLink_ConfigLoader.log("Error processing file {}: {}".format(filepath, e), level="ERROR")
            continue

        os.remove(filepath)
        MediLink_ConfigLoader.log("Deleted source file after consolidation: {}".format(filepath), level="INFO")

    if consolidated_data:
        with open(consolidated_filepath, 'w', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(consolidated_data)
        MediLink_ConfigLoader.log("Consolidated CSVs into {}".format(consolidated_filepath), level="INFO")
        return consolidated_filepath
    else:
        MediLink_ConfigLoader.log("No valid CSV files were found for consolidation.", level="INFO")
        return None

def operate_winscp(operation_type, files, endpoint_config, local_storage_path, config):
    """
    General function to operate WinSCP for uploading or downloading files.
    """
    MediLink_ConfigLoader.log("Starting operate_winscp with operation_type: {}".format(operation_type))
    
    config = ensure_config_loaded(config)
    winscp_path = get_winscp_path(config)
    
    if not os.path.isfile(winscp_path):
        MediLink_ConfigLoader.log("WinSCP.com not found at {}".format(winscp_path), level="ERROR")
        return []

    validate_endpoint_config(endpoint_config)
    winscp_log_path = setup_logging(operation_type, local_storage_path)

    # Validate the local_storage_path and replace it if necessary
    local_storage_path = validate_local_storage_path(local_storage_path, config)

    remote_directory = get_remote_directory(endpoint_config, operation_type)
    if operation_type == "download":
        # Prefer explicit ack-focused mask if not provided by endpoint
        filemask = endpoint_config.get('filemask') or ['era', '277', '277ibr', '277ebr', '999']
    else:
        filemask = None
    command = build_command(winscp_path, winscp_log_path, endpoint_config, remote_directory, operation_type, files, local_storage_path, newer_than=None, filemask=filemask)

    if config.get("TestMode", True):
        MediLink_ConfigLoader.log("Test mode is enabled. Simulating operation.")
        return simulate_operation(operation_type, files, config)
    
    result = execute_winscp_command(command, operation_type, files, local_storage_path)
    MediLink_ConfigLoader.log("[Execute WinSCP Command] Result: {}".format(result), level="DEBUG")
    return result

def validate_local_storage_path(local_storage_path, config):
    """
    Validates the local storage path and replaces it with outputFilePath from config if it contains spaces.
    """
    if ' ' in local_storage_path:
        MediLink_ConfigLoader.log("Local storage path contains spaces, using outputFilePath from config.", level="WARN")
        output_file_path = config.get('outputFilePath', None)
        if not output_file_path:
            raise ValueError("outputFilePath not found in config.")
        return os.path.normpath(output_file_path)
    return os.path.normpath(local_storage_path)

def ensure_config_loaded(config):
    MediLink_ConfigLoader.log("Ensuring configuration is loaded.")
    if not config:
        MediLink_ConfigLoader.log("Warning: No config passed to ensure_config_loaded. Re-loading config...")
        config, _ = MediLink_ConfigLoader.load_configuration()
    
    # Check if config was successfully loaded
    if not config or 'MediLink_Config' not in config:
        MediLink_ConfigLoader.log("Failed to load the MediLink configuration. Config is None or missing 'MediLink_Config'.")
        raise RuntimeError("Failed to load the MediLink configuration. Config is None or missing 'MediLink_Config'.")

    # Check that 'endpoints' key exists within 'MediLink_Config'
    if 'endpoints' not in config['MediLink_Config']:
        MediLink_ConfigLoader.log("The loaded configuration is missing the 'endpoints' section.")
        raise ValueError("The loaded configuration is missing the 'endpoints' section.")

    # Additional checks can be added here to ensure all expected keys and structures are present
    if 'local_storage_path' not in config['MediLink_Config']:
        MediLink_ConfigLoader.log("The loaded configuration is missing the 'local_storage_path' setting.")
        raise ValueError("The loaded configuration is missing the 'local_storage_path' setting.")

    MediLink_ConfigLoader.log("Configuration loaded successfully.")
    return config['MediLink_Config']  # Return the relevant part of the config for simplicity

def get_winscp_path(config):
    MediLink_ConfigLoader.log("Retrieving WinSCP path from provided config.")
    
    def find_winscp_path(cfg):
        if 'winscp_path' in cfg:
            # cfg is already 'MediLink_Config'
            MediLink_ConfigLoader.log("Config provided directly as 'MediLink_Config'.")
            return cfg.get('winscp_path')
        else:
            # cfg is the full configuration, retrieve 'MediLink_Config'
            MediLink_ConfigLoader.log("Config provided as full configuration; accessing 'MediLink_Config'.")
            medi_link_config = cfg.get('MediLink_Config', {})
            return medi_link_config.get('winscp_path')

    # Attempt to find the WinSCP path using the provided config
    winscp_path = find_winscp_path(config)
    
    # If the path is not found, attempt to use default paths
    if not winscp_path:
        error_message = "WinSCP path not found in config. Attempting to use default paths."
        # print(error_message)
        MediLink_ConfigLoader.log(error_message)
        
        # Try the default paths
        default_paths = [
            os.path.join(os.getcwd(), "Installers", "WinSCP-Portable", "WinSCP.com"),
            os.path.join(os.getcwd(), "Necessary Programs", "WinSCP-Portable", "WinSCP.com")
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                found_message = "WinSCP found at {}. Using this path.".format(path)
                # print(found_message)
                MediLink_ConfigLoader.log(found_message)
                return path
        
        # If no valid path is found, attempt to reload the configuration
        reload_message = "WinSCP not found in config or default paths. Reloading the entire configuration."
        # print(reload_message)
        MediLink_ConfigLoader.log(reload_message)
        
        try:
            config, _ = MediLink_ConfigLoader.load_configuration()
            winscp_path = find_winscp_path(config)
            
            if winscp_path:
                success_message = "WinSCP path found after reloading configuration. Using this path."
                # print(success_message)
                MediLink_ConfigLoader.log(success_message)
                return winscp_path
            else:
                raise FileNotFoundError("WinSCP path not found even after reloading configuration.")
        
        except Exception as e:
            error_message = "Failed to reload configuration or find WinSCP path: {}. Exiting script.".format(e)
            print(error_message)
            MediLink_ConfigLoader.log(error_message)
            raise FileNotFoundError(error_message)
    
    return winscp_path

def validate_endpoint_config(endpoint_config):
    MediLink_ConfigLoader.log("Validating endpoint configuration.")
    if not isinstance(endpoint_config, dict):
        MediLink_ConfigLoader.log("Endpoint configuration object is invalid. Expected a dictionary, got: {}".format(type(endpoint_config)))
        raise ValueError("Endpoint configuration object is invalid. Expected a dictionary, got: {}".format(type(endpoint_config)))

def setup_logging(operation_type, local_storage_path):
    MediLink_ConfigLoader.log("Setting up logging for operation type: {}".format(operation_type))
    log_filename = "winscp_upload.log" if operation_type == "upload" else "winscp_download.log"
    return os.path.join(local_storage_path, log_filename)

def get_remote_directory(endpoint_config, operation_type):
    MediLink_ConfigLoader.log("Getting remote directory for operation type: {}".format(operation_type))
    if endpoint_config is None:
        MediLink_ConfigLoader.log("Error: Endpoint configuration is None.")
        raise ValueError("Endpoint configuration is None. Expected a dictionary with configuration details.")

    if not isinstance(endpoint_config, dict):
        MediLink_ConfigLoader.log("Error: Endpoint configuration is invalid. Expected a dictionary, got: {}".format(type(endpoint_config)))
        raise TypeError("Endpoint configuration is invalid. Expected a dictionary, got: {}".format(type(endpoint_config)))

    try:
        if operation_type == "upload":
            return endpoint_config['remote_directory_up']
        elif operation_type == "download":
            return endpoint_config['remote_directory_down']
        else:
            MediLink_ConfigLoader.log("Invalid operation type: {}. Expected 'upload' or 'download'.".format(operation_type))
            raise ValueError("Invalid operation type: {}. Expected 'upload' or 'download'.".format(operation_type))
    except KeyError as e:
        MediLink_ConfigLoader.log("Critical Error: Endpoint config is missing key: {}".format(e))
        raise RuntimeError("Configuration error: Missing required remote directory in endpoint configuration.")

def normalize_filemask(filemask):
    """
    Normalize various filemask inputs into WinSCP-compatible string.
    Supports list of extensions, comma-separated string, or dict with 'extensions' and other filters.
    Falls back to '*' when input is invalid.
    """
    try:
        if not filemask:
            return '*'
        if isinstance(filemask, list):
            parts = []
            for ext in filemask:
                s = str(ext).strip().lstrip('*.').lstrip('.')
                if s:
                    parts.append('*.{}'.format(s))
            return '|'.join(parts) if parts else '*'
        if isinstance(filemask, dict):
            exts = filemask.get('extensions', [])
            other = []
            for k, v in filemask.items():
                if k == 'extensions':
                    continue
                other.append(str(v))
            ext_part = normalize_filemask(exts)
            other_part = ';'.join(other)
            if ext_part and other_part:
                return '{};{}'.format(ext_part, other_part)
            return ext_part or other_part or '*'
        if isinstance(filemask, str):
            # Support comma-separated or pipe-separated lists of extensions
            raw = filemask.replace(' ', '')
            if any(sep in raw for sep in [',', '|']):
                tokens = raw.replace('|', ',').split(',')
                return normalize_filemask([t for t in tokens if t])
            # If looks like an extension, prefix
            s = raw.lstrip('*.').lstrip('.')
            if s and all(ch.isalnum() for ch in s):
                return '*.{}'.format(s)
            return raw or '*'
    except Exception:
        return '*'

def build_command(winscp_path, winscp_log_path, endpoint_config, remote_directory, operation_type, files, local_storage_path, newer_than=None, filemask=None):
    # Log the operation type
    MediLink_ConfigLoader.log("[Build Command] Building WinSCP command for operation type: {}".format(operation_type))

    session_name = endpoint_config.get('session_name', '')

    # Initial command structure with options to disable timestamp preservation and permission setting (should now be compatible with Availity, hopefully this doesn't break everything else)
    command = [
        winscp_path,
        '/log=' + winscp_log_path,
        '/loglevel=1',
        '/nopreservetime',  # Disable timestamp preservation
        '/nopermissions',   # Disable permission setting
        '/command',
        'open {}'.format(session_name),
        'cd /',
        'cd {}'.format(remote_directory)
    ]

    try:
        # Handle upload operation
        if operation_type == "upload":
            if not files:
                MediLink_ConfigLoader.log("Error: No files provided for upload operation.", level="ERROR")
                raise ValueError("No files provided for upload operation.")

            put_commands = []
            for f in files:
                # Normalize the path
                normalized_path = os.path.normpath(f)
                original_path = normalized_path  # Keep for logging

                # Remove leading slash if present
                if normalized_path.startswith('\\') or normalized_path.startswith('/'):
                    normalized_path = normalized_path.lstrip('\\/')
                    MediLink_ConfigLoader.log("Removed leading slash from path: {}".format(original_path), level="DEBUG")

                # Remove trailing slash if present
                if normalized_path.endswith('\\') or normalized_path.endswith('/'):
                    normalized_path = normalized_path.rstrip('\\/')
                    MediLink_ConfigLoader.log("Removed trailing slash from path: {}".format(original_path), level="DEBUG")

                # Determine if quotes are necessary (e.g., if path contains spaces)
                if ' ' in normalized_path:
                    put_command = 'put "{}"'.format(normalized_path)
                    MediLink_ConfigLoader.log("Constructed put command with quotes: {}".format(put_command), level="DEBUG")
                else:
                    put_command = 'put {}'.format(normalized_path)
                    MediLink_ConfigLoader.log("Constructed put command without quotes: {}".format(put_command), level="DEBUG")

                put_commands.append(put_command)
            command += put_commands

        # Handle download operation
        elif operation_type == "download":
            lcd_path = os.path.normpath(local_storage_path)
            original_lcd_path = lcd_path  # Keep for logging

            # Remove leading slash if present
            if lcd_path.startswith('\\') or lcd_path.startswith('/'):
                lcd_path = lcd_path.lstrip('\\/')
                MediLink_ConfigLoader.log("Removed leading slash from local storage path: {}".format(original_lcd_path), level="DEBUG")

            # Remove trailing slash if present
            if lcd_path.endswith('\\') or lcd_path.endswith('/'):
                lcd_path = lcd_path.rstrip('\\/')
                MediLink_ConfigLoader.log("Removed trailing slash from local storage path: {}".format(original_lcd_path), level="DEBUG")

            # Determine if quotes are necessary (e.g., if path contains spaces)
            if ' ' in lcd_path:
                lcd_command = 'lcd "{}"'.format(lcd_path)
                MediLink_ConfigLoader.log("Constructed lcd command with quotes: {}".format(lcd_command), level="DEBUG")
            else:
                lcd_command = 'lcd {}'.format(lcd_path)
                MediLink_ConfigLoader.log("Constructed lcd command without quotes: {}".format(lcd_command), level="DEBUG")

            # XP/WinSCP NOTE:
            # - On XP, shell parsing quirks can break unquoted paths; prefer explicit quoting as above.
            # - Also avoid trailing backslashes which can be treated as escape characters in some shells.
            # - If downloads still do not appear in 'local_storage_path', cross-check WinSCP's session logs
            #   for the absolute target path actually used.
            command.append(lcd_command)

            # Handle filemask input
            if filemask:
                # TODO (MEDIUM PRIORITY - WinSCP Filemask Implementation):
                # PROBLEM: Need to translate various filemask input formats into proper WinSCP syntax.
                # Current implementation is incomplete and may not handle all edge cases.
                #
                # WINSCP FILEMASK SYNTAX REQUIREMENTS:
                # - Multiple extensions: "*.ext1|*.ext2|*.ext3" (pipe-separated)
                # - Single extension: "*.ext"
                # - All files: "*" or "*.*"
                # - Date patterns: "*YYYYMMDD*" for date-based filtering
                # - Size patterns: ">100K" for files larger than 100KB
                # - Combined: "*.csv|*.txt;>1K" (semicolon for AND conditions)
                #
                # INPUT FORMATS TO HANDLE:
                # 1. List: ['csv', 'txt', 'pdf'] -> "*.csv|*.txt|*.pdf"
                # 2. Dictionary: {'extensions': ['csv'], 'size': '>1K'} -> "*.csv;>1K"
                # 3. String: "csv,txt" -> "*.csv|*.txt" (comma-separated to pipe-separated)
                # 4. None/Empty: -> "*" (all files)
                #
                # IMPLEMENTATION STEPS / RISK NOTES:
                # 1. normalize_filemask(filemask) exists but needs comprehensive tests (unit + on-box)
                #    to guarantee XP/legacy shells parse the resulting mask and to ensure we never
                #    silently skip remits. Guard with explicit logging when normalization falls back.
                # 2. Endpoint JSON sometimes stores dicts with extra keys (size, age); preserve those
                #    semantics by sorting AND/OR clauses deterministically before composing the mask.
                # 3. Add schema validation upfront (e.g., str/list/dict only) so automation pipelines
                #    fail fast instead of emitting malformed WinSCP commands.
                # 4. Document the supported structures in docs + example configs so endpoint owners
                #    can safely tune filters without touching Python.
                # 5. XP QUIRK: Prefer simple masks (e.g., *.csv|*.txt) and avoid complex AND/OR until
                #    verified on XP; consider feature flag to keep legacy behavior if issues arise.
                filemask_str = normalize_filemask(filemask)
            else:
                filemask_str = '*'  # Default to all files if filemask is None

            # Use synchronize command for efficient downloading
            if newer_than:
                command.append('synchronize local -filemask="{}" -newerthan={}'.format(filemask_str, newer_than))
            else:
                command.append('synchronize local -filemask="{}"'.format(filemask_str))

            # XP/WinSCP NOTE:
            # - If downloads still land elsewhere, introduce a 'winscp_download_path' override in config
            #   and use that here for lcd + listing. Keep default behavior unchanged for now.

        # Close and exit commands
        command += ['close', 'exit']
        MediLink_ConfigLoader.log("[Build Command] WinSCP command: {}".format(command))
        return command

    except Exception as e:
        MediLink_ConfigLoader.log("Error in build_command: {}. Reverting to original implementation.".format(e), level="ERROR")

        # Fallback to original implementation
        # Handle upload operation
        if operation_type == "upload":
            if not files:
                MediLink_ConfigLoader.log("Error: No files provided for upload operation.", level="ERROR")
                raise ValueError("No files provided for upload operation.")
            command.extend(["put {}".format(os.path.normpath(file_path)) for file_path in files])

        # Handle download operation
        else:
            command.append('get *')

        # Close and exit commands
        command.extend(['close', 'exit'])
        MediLink_ConfigLoader.log("[Build Command] Original WinSCP command: {}".format(command))
        return command

def simulate_operation(operation_type, files, config):
    MediLink_ConfigLoader.log("Test Mode is enabled! Simulating WinSCP {} operation.".format(operation_type))
    
    if operation_type == 'upload' and files:
        MediLink_ConfigLoader.log("Simulating 3 second delay for upload operation for files: {}".format(files))
        time.sleep(3)
        return [os.path.normpath(file) for file in files if os.path.exists(file)]
    elif operation_type == 'download':
        MediLink_ConfigLoader.log("Simulating 3 second delay for download operation. No files to download in test mode.")
        time.sleep(3)
        return []
    else:
        MediLink_ConfigLoader.log("Invalid operation type during simulation: {}".format(operation_type))
        return []

def execute_winscp_command(command, operation_type, files, local_storage_path):
    """
    Execute the WinSCP command for the specified operation type.
    """
    MediLink_ConfigLoader.log("Executing WinSCP command for operation type: {}".format(operation_type))
    
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        stdout, stderr = process.communicate()
    except Exception as e:
        MediLink_ConfigLoader.log("Error occurred while executing WinSCP command: {}".format(e), level="ERROR")
        return []  # Return an empty list instead of None

    if process.returncode == 0:
        MediLink_ConfigLoader.log("WinSCP {} operation completed successfully.".format(operation_type))

        if operation_type == 'download':
            # Prefer configured override if present
            winscp_download_path = None
            try:
                from MediCafe.core_utils import extract_medilink_config
                config, _ = MediLink_ConfigLoader.load_configuration()
                medi = extract_medilink_config(config)
                winscp_download_path = medi.get('winscp_download_path')
            except Exception:
                winscp_download_path = None

            target_dir = winscp_download_path or local_storage_path
            downloaded_files = list_downloaded_files(target_dir)
            MediLink_ConfigLoader.log("Files currently located in target directory ({}): {}".format(target_dir, downloaded_files), level="DEBUG")

            if not downloaded_files and winscp_download_path and winscp_download_path != local_storage_path:
                # Fallback to original path if override empty
                fallback_files = list_downloaded_files(local_storage_path)
                MediLink_ConfigLoader.log("Fallback to local_storage_path yielded: {}".format(fallback_files), level="DEBUG")
                downloaded_files = fallback_files

            if not downloaded_files:
                MediLink_ConfigLoader.log("No files were downloaded or an error occurred during the listing process.", level="WARNING")
            return downloaded_files

        elif operation_type == 'upload':
            uploaded_files = [os.path.normpath(file) for file in files if os.path.exists(file)]
            MediLink_ConfigLoader.log("Uploaded files: {}".format(uploaded_files), level="DEBUG")
            return uploaded_files
    else:
        error_message = stderr.decode('utf-8').strip()
        MediLink_ConfigLoader.log("Failed to {} files. Exit code: {}. Details: {}".format(
            operation_type, process.returncode, error_message), level="ERROR")
        return []  # Return an empty list instead of None

def list_downloaded_files(local_storage_path):

    MediLink_ConfigLoader.log("Listing downloaded files in local storage path: {}".format(local_storage_path))
    
    # Initialize an empty list to hold file paths
    downloaded_files = []

    try:
        # Walk through the directory and collect all file paths
        for root, _, files in os.walk(local_storage_path):
            for file in files:
                file_path = os.path.join(root, file)
                downloaded_files.append(file_path)
                MediLink_ConfigLoader.log("File found: {}".format(file_path), level="DEBUG")
        
        if not downloaded_files:
            MediLink_ConfigLoader.log("No files found in the directory: {}".format(local_storage_path), level="WARNING")

    except Exception as e:
        MediLink_ConfigLoader.log("Error occurred while listing files in {}: {}".format(local_storage_path, e), level="ERROR")

    # Normalize to basenames so downstream move logic in MediLink_Down works cross-platform
    try:
        basenames = [os.path.basename(p) for p in downloaded_files]
        return basenames
    except Exception:
        return downloaded_files

def detect_new_files(directory_path, file_extension='.DAT'):
    """
    Scans the specified directory for new files with a given extension and adds a timestamp if needed.
    
    :param directory_path: Path to the directory containing files to be detected.
    :param file_extension: Extension of the files to detect.
    :return: A tuple containing a list of paths to new files detected in the directory and a flag indicating if a new file was just renamed.
    """
    import time
    detect_start = time.time()
    if PERFORMANCE_LOGGING:
        MediLink_ConfigLoader.log("File detection started for directory: {}".format(directory_path), level="INFO")
    
    MediLink_ConfigLoader.log("Scanning directory: {}".format(directory_path), level="INFO")
    detected_file_paths = []
    file_flagged = False
    
    try:
        listdir_start = time.time()
        filenames = os.listdir(directory_path)
        listdir_end = time.time()
        if PERFORMANCE_LOGGING:
            print("Directory listing completed in {:.2f} seconds".format(listdir_end - listdir_start))
        
        # Batch log the files found instead of logging each one individually
        matching_files = []
        for filename in filenames:
            if filename.endswith(file_extension):
                matching_files.append(filename)
        
        if matching_files:
            MediLink_ConfigLoader.log("Found {} files with extension {}".format(
                len(matching_files), file_extension), level="INFO")
        
        file_check_start = time.time()
        for filename in filenames:
            if filename.endswith(file_extension):
                name, ext = os.path.splitext(filename)
                
                if not is_timestamped(name):
                    new_name = "{}_{}{}".format(name, datetime.now().strftime('%Y%m%d_%H%M%S'), ext)
                    os.rename(os.path.join(directory_path, filename), os.path.join(directory_path, new_name))
                    MediLink_ConfigLoader.log("Renamed file from {} to {}".format(filename, new_name), level="INFO")
                    file_flagged = True
                    filename = new_name
                
                file_path = os.path.join(directory_path, filename)
                detected_file_paths.append(file_path)
        
        file_check_end = time.time()
        if PERFORMANCE_LOGGING:
            print("File checking completed in {:.2f} seconds".format(file_check_end - file_check_start))
    
    except Exception as e:
        MediLink_ConfigLoader.log("Error occurred: {}".format(str(e)), level="INFO")
    
    detect_end = time.time()
    if PERFORMANCE_LOGGING:
        print("File detection completed in {:.2f} seconds".format(detect_end - detect_start))
    MediLink_ConfigLoader.log("Detected {} files, flagged: {}".format(len(detected_file_paths), file_flagged), level="INFO")
    
    return detected_file_paths, file_flagged

def is_timestamped(name):
    """
    Checks if the given filename has a timestamp in the expected format.
    
    :param name: The name of the file without extension.
    :return: True if the filename includes a timestamp, False otherwise.
    """
    # Regular expression to match timestamps in the format YYYYMMDD_HHMMSS
    timestamp_pattern = re.compile(r'.*_\d{8}_\d{6}$')
    return bool(timestamp_pattern.match(name))

def organize_patient_data_by_endpoint(detailed_patient_data):
    """
    Organizes detailed patient data by their confirmed endpoints.
    This simplifies processing and conversion per endpoint basis, ensuring that claims are generated and submitted
    according to the endpoint-specific requirements.

    :param detailed_patient_data: A list of dictionaries, each containing detailed patient data including confirmed endpoint.
    :return: A dictionary with endpoints as keys and lists of detailed patient data as values for processing.
    """
    organized = {}
    for data in detailed_patient_data:
        # Retrieve endpoint in priority order: confirmed -> user_preferred -> suggested
        endpoint = (data.get('confirmed_endpoint') or 
                   data.get('user_preferred_endpoint') or 
                   data.get('suggested_endpoint', 'AVAILITY'))
        # Initialize a list for the endpoint if it doesn't exist
        if endpoint not in organized:
            organized[endpoint] = []
        organized[endpoint].append(data)
    return organized

def confirm_all_suggested_endpoints(detailed_patient_data):
    """
    Confirms all suggested endpoints for each patient's detailed data.
    """
    for data in detailed_patient_data:
        if 'confirmed_endpoint' not in data:
            data['confirmed_endpoint'] = data['suggested_endpoint']
    return detailed_patient_data

# Bulk edit + crosswalk NOTE:
# - These functions currently blend CLI prompts, validation, and persistence. They work for
#   interactive MediLink runs but block automation and make unit testing hard.
# - Implementation plan: extract a non-interactive service layer (e.g., validate_and_mutate_insurance,
#   apply_endpoint_override) that receives dependencies (validators, crosswalk saver) via parameters.
#   Keep thin CLI wrappers here that just format prompts.
# - Value: enables UI reuse, background automation, and makes `SKIP_API_SOURCED_INSURANCE_EDIT`
#   configurable instead of hard-coded. Also clarifies when crosswalk writes happen.
# - Risk / latent complexity: High-touch UX path. Need to preserve existing prompt order, handle
#   allow_unknown flows, and ensure crosswalk save failures do not corrupt in-memory state.
#   Coordinate with MediLink UI and MediBot teams before changing behavior; add tests that simulate
#   API-sourced + manual codes plus crosswalk updates.
def bulk_edit_insurance_types(detailed_patient_data, insurance_options):
    """Allow user to edit insurance types in a table-like format with validation"""
    print("\nEdit Insurance Type (Enter the code). Enter 'LIST' to display available insurance types.")

    for data in detailed_patient_data:
        patient_id = data.get('patient_id', 'Unknown')
        patient_name = data.get('patient_name', 'Unknown')
        current_insurance_type = data.get('insurance_type', '12')
        source = data.get('insurance_type_source', '')
        src_disp = 'API' if source == 'API' else ('MAN' if source == 'MANUAL' else 'DEF')
        
        # Validate current insurance type to determine status indicator
        validation_status = "[VALID]"
        show_warning = False
        
        # Use centralized validation if available
        if validate_insurance_type_from_config:
            try:
                validated_code, is_valid = validate_insurance_type_from_config(
                    current_insurance_type,
                    payer_id=patient_id,
                    source=source,
                    strict_mode=True,
                    allow_unknown=False
                )
                if is_valid:
                    validation_status = "[VALID]"
                else:
                    # Determine if format is valid or invalid
                    # Check format of original code to distinguish invalid format vs. not in config
                    format_valid = current_insurance_type and len(current_insurance_type) <= 3 and current_insurance_type.isalnum()
                    if not format_valid:
                        # Format was invalid
                        validation_status = "[INVALID]"
                    else:
                        # Format valid but not in config
                        validation_status = "[NOT IN CONFIG]"
                        if source == 'API':
                            show_warning = True
            except Exception as e:
                MediLink_ConfigLoader.log("Error validating insurance type in bulk edit display: {}".format(str(e)), level="WARNING")
                # Fallback to simple check
                if current_insurance_type in insurance_options:
                    validation_status = "[VALID]"
                elif current_insurance_type and len(current_insurance_type) <= 3 and current_insurance_type.isalnum():
                    validation_status = "[NOT IN CONFIG]"
                    if source == 'API':
                        show_warning = True
                else:
                    validation_status = "[INVALID]"
        else:
            # Fallback validation if function not available
            if current_insurance_type in insurance_options:
                validation_status = "[VALID]"
            elif current_insurance_type and len(current_insurance_type) <= 3 and current_insurance_type.isalnum():
                validation_status = "[NOT IN CONFIG]"
                if source == 'API':
                    show_warning = True
            else:
                validation_status = "[INVALID]"
        
        current_insurance_description = insurance_options.get(current_insurance_type, "Unknown")
        
        # Display with validation status
        print("({}) {:<25} | Src:{} | Current Ins. Type: {} {} - {}".format(
            patient_id, patient_name, src_disp, current_insurance_type, validation_status, current_insurance_description))
        
        # Show warning for API-sourced codes not in config
        if show_warning:
            print("  WARNING: API code '{}' not found in insurance_options. Please verify or edit.".format(current_insurance_type))

        # Determine if we should skip this patient
        # Always show API-sourced codes that are not in config, regardless of flag
        should_skip = False
        if source == 'API' and SKIP_API_SOURCED_INSURANCE_EDIT:
            # Only skip if code is valid in config
            if validation_status == "[VALID]":
                print("  -> Skipped (API-sourced, valid in config)")
                MediLink_ConfigLoader.log("Skipped editing insurance type for API-sourced patient: patient_id='{}'".format(patient_id), level="DEBUG")
                should_skip = True
            # Otherwise, always show for editing

        if should_skip:
            continue

        while True:
            new_insurance_type = input("Enter new insurance type (or press Enter to keep current): ").strip().upper()
            
            if new_insurance_type == 'LIST':
                MediLink_Display_Utils.display_insurance_options(insurance_options)
                continue
                
            elif not new_insurance_type:
                # Keep current insurance type
                break
            
            # Use centralized validation function
            if validate_insurance_type_from_config:
                try:
                    validated_code, is_valid = validate_insurance_type_from_config(
                        new_insurance_type,
                        payer_id=patient_id,
                        source='MANUAL',
                        strict_mode=True,
                        allow_unknown=False
                    )
                    
                    if is_valid:
                        # Valid code in config
                        data['insurance_type'] = validated_code
                        data['insurance_type_source'] = 'MANUAL'
                        print("Updated to: {} - {}".format(validated_code, insurance_options.get(validated_code, "Unknown")))
                        break
                    elif validated_code == '12':
                        # Either format invalid or not in config - check format manually
                        if new_insurance_type and len(new_insurance_type) <= 3 and new_insurance_type.isalnum():
                            # Format is valid but not in config - ask user
                            confirm = input("Code '{}' not found in configuration. Use it anyway? (y/n): ".format(new_insurance_type)).strip().lower()
                            if confirm in ['y', 'yes']:
                                validated_code, _ = validate_insurance_type_from_config(
                                    new_insurance_type,
                                    payer_id=patient_id,
                                    source='MANUAL',
                                    strict_mode=True,
                                    allow_unknown=True
                                )
                                data['insurance_type'] = validated_code
                                data['insurance_type_source'] = 'MANUAL'
                                print("Updated to: {} (not in config, but format valid)".format(validated_code))
                                break
                            else:
                                print("Please enter a valid code or type 'LIST' to see options.")
                                continue
                        else:
                            # Format invalid, fallback to PPO
                            print("Invalid format. Using default PPO (12).")
                            data['insurance_type'] = '12'
                            data['insurance_type_source'] = 'MANUAL'
                            break
                    else:
                        # validated_code is not '12' and not in config - format valid but not in config
                        # This case should not happen with allow_unknown=False, but handle it anyway
                        confirm = input("Code '{}' not found in configuration. Use it anyway? (y/n): ".format(new_insurance_type)).strip().lower()
                        if confirm in ['y', 'yes']:
                            # Re-validate with allow_unknown=True
                            validated_code, _ = validate_insurance_type_from_config(
                                new_insurance_type,
                                payer_id=patient_id,
                                source='MANUAL',
                                strict_mode=True,
                                allow_unknown=True
                            )
                            data['insurance_type'] = validated_code
                            data['insurance_type_source'] = 'MANUAL'
                            print("Updated to: {} (not in config, but format valid)".format(validated_code))
                            break
                        else:
                            print("Please enter a valid code or type 'LIST' to see options.")
                            continue
                except Exception as e:
                    MediLink_ConfigLoader.log("Error validating insurance type in bulk edit: {}".format(str(e)), level="WARNING")
                    # Fall through to legacy validation
                    if new_insurance_type in insurance_options:
                        data['insurance_type'] = new_insurance_type
                        data['insurance_type_source'] = 'MANUAL'
                        break
                    else:
                        confirm = input("Code '{}' not found in configuration. Use it anyway? (y/n): ".format(new_insurance_type)).strip().lower()
                        if confirm in ['y', 'yes']:
                            data['insurance_type'] = new_insurance_type
                            data['insurance_type_source'] = 'MANUAL'
                            break
                        else:
                            print("Invalid insurance type. Please enter a valid code or type 'LIST' to see options.")
                            continue
            else:
                # Fallback to legacy validation if function not available
                if new_insurance_type in insurance_options:
                    data['insurance_type'] = new_insurance_type
                    data['insurance_type_source'] = 'MANUAL'
                    break
                else:
                    confirm = input("Code '{}' not found in configuration. Use it anyway? (y/n): ".format(new_insurance_type)).strip().lower()
                    if confirm in ['y', 'yes']:
                        data['insurance_type'] = new_insurance_type
                        data['insurance_type_source'] = 'MANUAL'
                        break
                    else:
                        print("Invalid insurance type. Please enter a valid code or type 'LIST' to see options.")
                        continue


def review_and_confirm_changes(detailed_patient_data, insurance_options):
    # Review and confirm changes
    print("\nReview changes:")
    print("{:<20} {:<10} {:<30}".format("Patient Name", "Ins. Type", "Description"))
    print("="*65)
    for data in detailed_patient_data:
        # Fix: Add null checks to prevent AttributeError
        if data is None:
            continue
            
        insurance_type = data.get('insurance_type', 'Unknown')
        insurance_description = insurance_options.get(insurance_type, "Unknown")
        patient_name = data.get('patient_name', 'Unknown')
        print("{:<20} {:<10} {:<30}".format(patient_name, insurance_type, insurance_description))
    confirm = input("\nConfirm changes? (y/n): ").strip().lower()
    return confirm in ['y', 'yes', '']


def update_suggested_endpoint_with_user_preference(detailed_patient_data, patient_index, new_endpoint, config, crosswalk):
    """
    Updates the suggested endpoint for a patient and optionally updates the crosswalk 
    for future patients with the same insurance.
    
    :param detailed_patient_data: List of patient data dictionaries
    :param patient_index: Index of the patient being updated
    :param new_endpoint: The new endpoint selected by the user
    :param config: Configuration settings
    :param crosswalk: Crosswalk data for in-memory updates
    :return: Updated crosswalk if changes were made, None otherwise
    """
    # Note: load_insurance_data_from_mains is now imported at module level
    
    data = detailed_patient_data[patient_index]
    original_suggested = data.get('suggested_endpoint')
    
    # Update the patient's endpoint preference
    data['user_preferred_endpoint'] = new_endpoint
    data['confirmed_endpoint'] = new_endpoint
    
    # If user changed from the original suggestion, offer to update crosswalk
    if original_suggested != new_endpoint:
        primary_insurance = data.get('primary_insurance')
        patient_name = data.get('patient_name')
        
        print("\nYou changed the endpoint for {} from {} to {}.".format(patient_name, original_suggested, new_endpoint))
        update_future = input("Would you like to use {} as the default endpoint for future patients with {}? (Y/N): ".format(new_endpoint, primary_insurance)).strip().lower()
        
        if update_future in ['y', 'yes']:
            # Find the payer ID associated with this insurance
            load_insurance_data_from_mains = _get_medibot_function('MediBot_Preprocessor_lib', 'load_insurance_data_from_mains')
            insurance_to_id = load_insurance_data_from_mains(config) if load_insurance_data_from_mains else {}
            insurance_id = insurance_to_id.get(primary_insurance)
            
            if insurance_id:
                # Find the payer ID in crosswalk and update it
                updated = False
                for payer_id, payer_data in crosswalk.get('payer_id', {}).items():
                    medisoft_ids = [str(id) for id in payer_data.get('medisoft_id', [])]
                    if str(insurance_id) in medisoft_ids:
                        # Update the crosswalk in memory
                        crosswalk['payer_id'][payer_id]['endpoint'] = new_endpoint
                        MediLink_ConfigLoader.log("Updated crosswalk in memory: Payer ID {} ({}) now defaults to {}".format(payer_id, primary_insurance, new_endpoint), level="INFO")
                        
                        # Update suggested_endpoint for other patients with same insurance in current batch
                        for other_data in detailed_patient_data:
                            if (other_data.get('primary_insurance') == primary_insurance and 
                                'user_preferred_endpoint' not in other_data):
                                other_data['suggested_endpoint'] = new_endpoint
                        
                        updated = True
                        break
                
                if updated:
                    # Save the updated crosswalk to disk immediately using API bypass mode
                    if save_crosswalk_immediately(config, crosswalk):
                        print("Updated default endpoint for {} to {}".format(primary_insurance, new_endpoint))
                    else:
                        print("Updated endpoint preference (will be saved during next crosswalk update)")
                    return crosswalk
                else:
                    MediLink_ConfigLoader.log("Could not find payer ID in crosswalk for insurance {}".format(primary_insurance), level="WARNING")
            else:
                MediLink_ConfigLoader.log("Could not find insurance ID for {} to update crosswalk".format(primary_insurance), level="WARNING")
    
    return None


def save_crosswalk_immediately(config, crosswalk):
    """
    Saves the crosswalk to disk immediately using API bypass mode.
    
    :param config: Configuration settings
    :param crosswalk: Crosswalk data to save
    :return: True if saved successfully, False otherwise
    """
    try:
        # Import and use the existing save_crosswalk function directly
        from MediBot.MediBot_Crosswalk_Utils import save_crosswalk
        
        # Save using API bypass mode (no client needed, skip API operations)
        success = save_crosswalk(None, config, crosswalk, skip_api_operations=True)
        
        if success:
            MediLink_ConfigLoader.log("Successfully saved crosswalk with updated endpoint preferences", level="INFO")
        else:
            MediLink_ConfigLoader.log("Failed to save crosswalk - preferences will be saved during next crosswalk update", level="WARNING")
            
        return success
        
    except ImportError:
        MediLink_ConfigLoader.log("Could not import MediBot_Crosswalk_Utils for saving crosswalk", level="ERROR")
        return False
    except Exception as e:
        MediLink_ConfigLoader.log("Error saving crosswalk: {}".format(e), level="ERROR")
        return False