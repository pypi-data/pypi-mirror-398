#MediBot.py
import os, sys  # Must be imported first

# Add parent directory of the project to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    # Ensure project root is at the front of sys.path to avoid site-packages shadowing
    sys.path.insert(0, project_dir)
else:
    # Ensure it's at the front to avoid site-packages shadowing even if already present
    try:
        if sys.path[0] != project_dir:
            sys.path.remove(project_dir)
            sys.path.insert(0, project_dir)
    except Exception:
        pass

import subprocess, tempfile, traceback, re, time
try:
    import msvcrt  # Windows-specific module
except ImportError:
    msvcrt = None  # Not available on non-Windows systems
from collections import OrderedDict
from datetime import datetime # Added for primary surgery date logic
import MediBot_Notepad_Utils  # For generating notepad files
try:
    # Python 3.4.4 on XP does not have typing enhancements; avoid heavy typing usage
    from collections import namedtuple
except Exception:
    namedtuple = None

# Error reporting imports for automated crash reporting
try:
    from MediCafe.error_reporter import capture_unhandled_traceback, submit_support_bundle_email
except ImportError:
    capture_unhandled_traceback = None
    submit_support_bundle_email = None

# ============================================================================
# MINIMAL PROTECTION: Import State Validation
# ============================================================================

def validate_critical_imports():
    """Validate that critical imports are in expected state before proceeding"""
    critical_modules = {
        'MediBot_Preprocessor': None,
        'MediBot_Preprocessor_lib': None,
        'MediBot_UI': None,
        'MediBot_Crosswalk_Library': None
    }
    
    # Test imports and capture state
    try:
        print("Testing MediCafe.core_utils import...")
        from MediCafe.core_utils import import_medibot_module_with_debug
        print("MediCafe.core_utils import successful")
        
        for module_name in critical_modules.keys():
            print("Testing {} import...".format(module_name))
            try:
                module = import_medibot_module_with_debug(module_name)
                critical_modules[module_name] = module
                if module is None:
                    print("  WARNING: {} import returned None".format(module_name))
                else:
                    print("  SUCCESS: {} import successful".format(module_name))
            except Exception as e:
                print("  ERROR: {} import failed with exception: {}".format(module_name, e))
                critical_modules[module_name] = None
    except Exception as e:
        print("CRITICAL: Failed to import core utilities: {}".format(e))
        return False, critical_modules
    
    # Check for None imports (the specific failure pattern)
    failed_imports = []
    for module_name, module in critical_modules.items():
        if module is None:
            failed_imports.append(module_name)
    
    if failed_imports:
        print("CRITICAL: Import failures detected:")
        for failed in failed_imports:
            print("  - {}: Import returned None".format(failed))
        return False, critical_modules
    
    return True, critical_modules

# Use core utilities for standardized imports
from MediCafe.core_utils import (
    import_medibot_module_with_debug, 
    get_config_loader_with_fallback,
    get_api_client_factory
)

# Initialize configuration loader with fallback
MediLink_ConfigLoader = get_config_loader_with_fallback()

# Import MediBot modules using centralized import functions with debugging
MediBot_dataformat_library = import_medibot_module_with_debug('MediBot_dataformat_library')
MediBot_Preprocessor = import_medibot_module_with_debug('MediBot_Preprocessor')
MediBot_Preprocessor_lib = import_medibot_module_with_debug('MediBot_Preprocessor_lib')

# Import UI components with function extraction
MediBot_UI = import_medibot_module_with_debug('MediBot_UI')
if MediBot_UI:
    app_control = getattr(MediBot_UI, 'app_control', None)
    manage_script_pause = getattr(MediBot_UI, 'manage_script_pause', None)
    user_interaction = getattr(MediBot_UI, 'user_interaction', None)
    get_app_control = getattr(MediBot_UI, '_get_app_control', None)
    def _ac():
        try:
            return get_app_control() if get_app_control else getattr(MediBot_UI, 'app_control', None)
        except Exception:
            return getattr(MediBot_UI, 'app_control', None)
else:
    app_control = None
    manage_script_pause = None
    user_interaction = None

# Import crosswalk library
MediBot_Crosswalk_Library = import_medibot_module_with_debug('MediBot_Crosswalk_Library')
if MediBot_Crosswalk_Library:
    crosswalk_update = getattr(MediBot_Crosswalk_Library, 'crosswalk_update', None)
else:
    crosswalk_update = None

# Initialize API client variables
api_client = None
factory = None

try:
    # Try to get API client factory
    factory = get_api_client_factory()
    if factory:
        api_client = factory.get_shared_client()  # Use shared client for token caching benefits
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("MediBot using API Factory with shared client", level="INFO")
except ImportError as e:
    # Fallback to basic API client
    try:
        from MediCafe.core_utils import get_api_client
        api_client = get_api_client()
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("MediBot using fallback API client", level="WARNING")
    except ImportError as e2:
        # Make API client optional - don't log warning for now
        pass

# Buffer for startup warnings/errors so we can re-display them after clearing the console
STARTUP_NOTICES = []

def _record_startup_notice(level, message):
    """Record a startup notice, log it, and print it immediately.
    Stored notices will be reprinted after the screen is cleared.
    """
    try:
        STARTUP_NOTICES.append((level, message))
    except Exception:
        pass
    try:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log(message, level=level)
    except Exception:
        pass
    try:
        print(message)
    except Exception:
        pass

def record_startup_warning(message):
    """Record a startup warning."""
    _record_startup_notice('WARNING', message)

def record_startup_error(message):
    """Record a startup error."""
    _record_startup_notice('ERROR', message)

def identify_field(header, field_mapping):
    for medisoft_field, patterns in field_mapping.items():
        for pattern in patterns:
            if re.search(pattern, header, re.IGNORECASE):
                return medisoft_field
    return None

    # Add this print to a function that is calling identify_field
    #print("Warning: No matching field found for CSV header '{}'".format(header))

def create_patient_entries_from_row(row, reverse_mapping):
    """
    Helper function to create patient entries from a row with surgery date handling.
    
    Args:
        row: The CSV row containing patient data
        reverse_mapping: The reverse mapping for field lookups
        
    Returns:
        list: List of tuples (surgery_date, patient_name, patient_id, diagnosis_code, row)
    """
    patient_id = row.get(reverse_mapping['Patient ID #2'])
    patient_name = row.get(reverse_mapping['Patient Name'])
    
    # Get all surgery dates for this patient
    all_surgery_dates = row.get('_all_surgery_dates', [row.get('Surgery Date')])
    surgery_date_to_diagnosis = row.get('_surgery_date_to_diagnosis', {})
    
    patient_entries = []
    
    # Sort surgery dates chronologically to ensure proper ordering
    sorted_surgery_dates = []
    for surgery_date in all_surgery_dates:
        try:
            if hasattr(surgery_date, 'strftime'):
                # Already a datetime object
                sorted_surgery_dates.append(surgery_date)
            elif isinstance(surgery_date, str):
                # Convert string to datetime for sorting
                surgery_date_dt = datetime.strptime(surgery_date, '%m-%d-%Y')
                sorted_surgery_dates.append(surgery_date_dt)
            else:
                # Fallback - use as is
                sorted_surgery_dates.append(surgery_date)
        except (ValueError, TypeError):
            # If parsing fails, use the original value
            sorted_surgery_dates.append(surgery_date)
    
    # Sort the dates chronologically
    sorted_surgery_dates.sort()
    
    # Create entries for each surgery date in chronological order
    # The enhanced table display will group by patient_id and show dashed lines for secondary dates
    for surgery_date in sorted_surgery_dates:
        try:
            if hasattr(surgery_date, 'strftime'):
                surgery_date_str = surgery_date.strftime('%m-%d-%Y')
            elif isinstance(surgery_date, str):
                surgery_date_str = surgery_date
            else:
                surgery_date_str = str(surgery_date)
        except Exception:
            surgery_date_str = str(surgery_date)
        
        # Get the diagnosis code for this surgery date
        diagnosis_code = surgery_date_to_diagnosis.get(surgery_date_str, 'N/A')
        
        # Add entry for this surgery date
        patient_entries.append((surgery_date, patient_name, patient_id, diagnosis_code, row))
    
    return patient_entries

# Global flag to control AHK execution method - set to True to use optimized stdin method
USE_AHK_STDIN_OPTIMIZATION = True

def _get_ahk_timing_settings():
    """Fetch AHK timing settings from config with safe defaults.
    Returns (key_delay_ms, key_press_ms, post_send_sleep_ms).
    """
    key_delay_ms = 0 
    key_press_ms = 0
    post_send_sleep_ms = 0
    try:
        config, _ = MediBot_Preprocessor_lib.get_cached_configuration()
        # Allow flat keys in config for simplicity/XP safety
        key_delay_ms = int(config.get('AHK_KEY_DELAY_MS', key_delay_ms))
        key_press_ms = int(config.get('AHK_KEY_PRESS_MS', key_press_ms))
        post_send_sleep_ms = int(config.get('AHK_POST_SEND_SLEEP_MS', post_send_sleep_ms))
    except Exception:
        # Use defaults on any error
        pass
    return key_delay_ms, key_press_ms, post_send_sleep_ms

def _build_ahk_script_with_handshake(core_send_command, done_token):
    """Build a complete AHK script that:
    - Sets stable, slightly slowed input timing (prevents UI overrun)
    - Executes the provided send command (expected to include {Enter} as field advance)
    - Sleeps briefly to allow UI to settle
    - Emits a completion token to stdout (so Python can block until completion)

    NOTE (future option - burst mode): To reduce process spawn overhead, we can batch
    multiple send commands into a single AHK script by concatenating several
    `SendInput, ...{Enter}` lines separated by short `Sleep` calls, then append a single
    `FileAppend, DONE, *` at the end. Python would then wait for "DONE" once per burst
    (e.g., 3–5 fields), instead of once per field.
    """
    # Keep delays configurable; defaults are tuned for responsiveness while avoiding overruns
    key_delay_ms, key_press_ms, post_send_sleep_ms = _get_ahk_timing_settings()
    # SetKeyDelay, DelayBetweenKeysMs, KeyPressDurationMs
    preamble = (
        "#NoEnv\r\n"
        "#NoTrayIcon\r\n"
        "SendMode, Input\r\n"
        "SetKeyDelay, {0}, {1}\r\n".format(key_delay_ms, key_press_ms)
    )
    # After each send, give UI a short moment before declaring done
    epilogue = (
        "\r\nSleep, {sleep}\r\n"
        "FileAppend, {done}, *\r\n"
        "ExitApp\r\n"
    ).format(sleep=post_send_sleep_ms, done=done_token)
    return preamble + core_send_command + epilogue

# Function to execute an AutoHotkey script
def run_ahk_script(script_content):
    """
    Execute an AutoHotkey script using either optimized stdin method or traditional file method.
    Blocks until AHK confirms completion by writing a token to stdout.
    Automatically falls back to file method if stdin method fails.

    Future: Add optional burst mode to submit several send commands in one script, reducing
    process overhead while keeping a single completion token per burst.
    """
    done_token = "OK"
    full_script = _build_ahk_script_with_handshake(script_content + "\r\n", done_token)
    if USE_AHK_STDIN_OPTIMIZATION:
        try:
            # Optimized method: Execute AHK script via stdin pipe - eliminates temporary file creation
            # Compatible with Windows XP and AutoHotkey v1.x. In AHK v1, '*' tells AHK to read the script from stdin.
            process = subprocess.Popen(
                [
                    MediBot_Preprocessor_lib.AHK_EXECUTABLE,
                    '/ErrorStdOut',  # Route script errors to stderr for capture
                    '/CP65001',      # Treat incoming script as UTF-8 (robust with minimal overhead)
                    '*'
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )

            # Send script content via stdin
            stdout, stderr = process.communicate(input=full_script.encode('utf-8'))

            if process.returncode == 0:
                try:
                    decoded_out = stdout.decode('utf-8', errors='ignore') if stdout else ''
                except Exception:
                    decoded_out = str(stdout)
                # Require the done token to ensure UI is ready before proceeding
                if done_token in decoded_out:
                    return  # Success
                # If we got here, AHK exited 0 but no token was seen; fall through to log and fallback
                MediLink_ConfigLoader.log("AHK completed without handshake token; attempting fallback.", level="WARNING")

            # Non-zero exit code: log details and fall back to file-based method
            print("AHK script failed with exit status: {}".format(process.returncode))
            MediLink_ConfigLoader.log("AHK script failed with exit status: {}".format(process.returncode), level="ERROR")
            if stderr:
                try:
                    decoded_err = stderr.decode('utf-8', errors='ignore')
                except Exception:
                    decoded_err = str(stderr)
                print("AHK Error: {}".format(decoded_err))
                MediLink_ConfigLoader.log("AHK Error: {}".format(decoded_err), level="ERROR")

        except Exception as e:
            # If stdin method fails, fall back to traditional file method
            print("AHK stdin execution failed, falling back to file method: {}".format(e))
            MediLink_ConfigLoader.log("AHK stdin execution failed, falling back to file method: {}".format(e), level="ERROR")
            # Continue to fallback implementation below
    
    # Traditional file-based method (fallback or when optimization disabled)
    temp_script_name = None  # Initialize variable to hold the name of the temporary script file
    try:
        # Create a temporary AHK script file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ahk', encoding='utf-8') as temp_script:
            temp_script_name = temp_script.name  # Store the name of the temporary script file
            temp_script.write(full_script)  # Write the script content to the temporary file
            temp_script.flush()  # Ensure the file is written to disk
        # Attempt to run the AHK script and capture stdout to verify handshake
        process = subprocess.Popen(
            [MediBot_Preprocessor_lib.AHK_EXECUTABLE, temp_script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, 'AutoHotkey', output=stderr)
        try:
            decoded_out = stdout.decode('utf-8', errors='ignore') if stdout else ''
        except Exception:
            decoded_out = str(stdout)
        if done_token not in decoded_out:
            MediLink_ConfigLoader.log("AHK file-exec completed without handshake token.", level="WARNING")
            # Proceed, but warn; on older systems stdout may be suppressed
    except subprocess.CalledProcessError as e:
        print("AHK script failed with exit status: {}".format(e.returncode))  # Log the exit status of the failed script
        MediLink_ConfigLoader.log("AHK script failed with exit status: {}".format(e.returncode), level="ERROR")
        print("Output from AHK script: {}".format(e.output))  # Log the output from the failed script
        MediLink_ConfigLoader.log("Output from AHK script: {}".format(e.output), level="ERROR")
    except Exception as e:
        print("An unexpected error occurred while running the AHK script: {}".format(e))  # Log any unexpected errors
        MediLink_ConfigLoader.log("An unexpected error occurred while running the AHK script: {}".format(e), level="ERROR")
        traceback.print_exc()  # Print the full traceback for debugging purposes
    finally:
        # Delete the temporary script file
        if temp_script_name:
            try:
                os.unlink(temp_script_name)  # Attempt to delete the temporary script file
            except OSError as e:
                print("Error deleting temporary script file: {}".format(e))  # Log any errors encountered while deleting the file
                MediLink_ConfigLoader.log("Error deleting temporary script file: {}".format(e), level="ERROR")
                # Future Improvement: Implement a cleanup mechanism to handle orphaned temporary files

# Module-scope context container for cross-callback state (XP/3.4.4 compatible)
try:
    # Avoid dataclasses to maintain 3.4.4 compatibility without external deps
    class MediBotContext(object):
        def __init__(self):
            self.last_processed_entry = None
            self.parsed_address_components = {}
            self.current_patient_context = None
    CTX = MediBotContext()
except Exception:
    # Fallback simple dict if class definition fails for any reason
    CTX = {
        'last_processed_entry': None,
        'parsed_address_components': {},
        'current_patient_context': None,
    }

# Backwards-compatible globals (maintain import contract for MediBot_UI and hotkeys)
last_processed_entry = None
parsed_address_components = {}
current_patient_context = None

def process_field(medisoft_field, csv_row, parsed_address_components, reverse_mapping, csv_data, fixed_values):
    global last_processed_entry
    
    try:
        # Attempt to retrieve the value for the current medisoft_field from parsed_address_components
        value = parsed_address_components.get(medisoft_field, '') if medisoft_field in parsed_address_components else ''
        
        # If no value is found, check if there is a fixed value available for this field
        if not value:
            if medisoft_field in fixed_values:
                value = fixed_values[medisoft_field][0]  # Use the fixed value if available
        
        # If still no value, check if the field is present in the reverse mapping
        if not value and medisoft_field in reverse_mapping:
            # Retrieve the corresponding CSV header from the reverse mapping
            csv_header = reverse_mapping[medisoft_field]
            value = csv_row.get(csv_header, '')  # Get the value from the CSV row using the header
            
            # Log the detected field and its value after assignment
            MediLink_ConfigLoader.log("Detected {}: {}".format(medisoft_field, value), level="DEBUG")

        # Format the value for the AutoHotkey script, or default to sending an Enter key if no value is found
        formatted_value = (MediBot_dataformat_library.format_data(medisoft_field, value, csv_data, reverse_mapping, parsed_address_components)
                           if value else 'Send, {Enter}')
        
        # Execute the AutoHotkey script with the formatted value
        run_ahk_script(formatted_value)

        # Update the last processed entry with the current field and its value
        last_processed_entry = (medisoft_field, value)
        try:
            # Keep CTX in sync for consumers that adopt CTX
            if hasattr(CTX, 'last_processed_entry'):
                CTX.last_processed_entry = last_processed_entry
            else:
                CTX['last_processed_entry'] = last_processed_entry
        except Exception:
            pass
        return 'continue', last_processed_entry  # Indicate to continue processing
    except Exception as e:
        # Handle any exceptions that occur during processing
        return handle_error(e, medisoft_field, last_processed_entry, csv_data, reverse_mapping)

def handle_error(error, medisoft_field, last_processed_entry, csv_data, reverse_mapping):
    global current_patient_context
    try:
        MediLink_ConfigLoader.log("Error in process_field: {}".format(error), level="ERROR")
    except Exception:
        pass
    print("An error occurred while processing {0}: {1}".format(medisoft_field, error))
    
    # Update patient context with current error information for F11 menu
    if current_patient_context is None:
        current_patient_context = {}
    current_patient_context.update({
        'last_field': medisoft_field,
        'error_occurred': True,
        'error_message': str(error)
    })
    try:
        if hasattr(CTX, 'current_patient_context'):
            CTX.current_patient_context = current_patient_context
        else:
            CTX['current_patient_context'] = current_patient_context
    except Exception:
        pass
    
    # Assuming the interaction mode is 'error' in this case
    interaction_mode = 'error'
    response = user_interaction(csv_data, interaction_mode, str(error), reverse_mapping)
    return response, last_processed_entry

# iterating through each field defined in the field_mapping.
def iterate_fields(csv_row, field_mapping, parsed_address_components, reverse_mapping, csv_data, fixed_values):
    global last_processed_entry
    # Check for user action at the start of each field processing
    for medisoft_field in field_mapping.keys():
        action = manage_script_pause(csv_data,'',reverse_mapping) # per-field pause availability. Necessary to provide frequent opportunities for the user to pause the script.
        if action != 0:  # If action is either 'Retry' (-1) or 'Skip' (1)
            return action  # Break out and pass the action up
        
        # Process each field in the row
        _, last_processed_entry = process_field(medisoft_field, csv_row, parsed_address_components, reverse_mapping, csv_data, fixed_values)
        try:
            if hasattr(CTX, 'last_processed_entry'):
                CTX.last_processed_entry = last_processed_entry
            else:
                CTX['last_processed_entry'] = last_processed_entry
        except Exception:
            pass
        
    return 0 # Default action to continue

def data_entry_loop(csv_data, field_mapping, reverse_mapping, fixed_values):
    global last_processed_entry, parsed_address_components, current_patient_context
    # Do NOT convert these to locals. The F11 pause/retry menu and MediBot_UI depend on
    # these globals to reflect real-time state across callbacks and hotkey handlers.
    # last_processed_entry, parsed_address_components = None, {}  # This would break F11 context.
    error_message = ''  # Initialize error_message once
    current_row_index = 0
    # PERFORMANCE FIX: Cache list length to avoid repeated len() calls
    csv_data_length = len(csv_data)

    while current_row_index < csv_data_length:
        row = csv_data[current_row_index]
        
        # PERFORMANCE FIX: Clear accumulating memory while preserving F11 menu context
        # Store patient context before clearing last_processed_entry for F11 "Retry last entry" functionality
        if last_processed_entry is not None:
            patient_name = row.get(reverse_mapping.get('Patient Name', ''), 'Unknown Patient')
            surgery_date = row.get('Surgery Date', 'Unknown Date')
            current_patient_context = {
                'patient_name': patient_name,
                'surgery_date': surgery_date,
                'last_field': last_processed_entry[0] if last_processed_entry else None,
                'last_value': last_processed_entry[1] if last_processed_entry else None,
                'row_index': current_row_index
            }
            try:
                if hasattr(CTX, 'current_patient_context'):
                    CTX.current_patient_context = current_patient_context
                else:
                    CTX['current_patient_context'] = current_patient_context
            except Exception:
                pass
        
        # Clear memory-accumulating structures while preserving F11 context above
        last_processed_entry = None
        parsed_address_components = {}
        try:
            if hasattr(CTX, 'last_processed_entry'):
                CTX.last_processed_entry = None
                CTX.parsed_address_components = {}
            else:
                CTX['last_processed_entry'] = None
                CTX['parsed_address_components'] = {}
        except Exception:
            pass
        
        # Handle script pause at the start of each row (patient record). 
        manage_script_pause(csv_data, error_message, reverse_mapping)
        error_message = ''  # Clear error message for the next iteration
        
        if _ac() and _ac().get_pause_status():
            continue  # Skip processing this row if the script is paused

        # I feel like this is overwriting what would have already been idenfitied in the mapping. 
        # This probably needs to be initialized differently.
        # Note: parsed_address_components is now explicitly cleared above for performance
        # parsed_address_components = {'City': '', 'State': '', 'Zip Code': ''}
        # parsed_address_components = {}  # Moved to top of loop for memory management

        # Process each field in the row
        action = iterate_fields(row, field_mapping, parsed_address_components, reverse_mapping, csv_data, fixed_values)
        # TODO (Low) add a feature here where if you accidentally started overwriting a patient that you could go back 2 patients.
        # Need to tell the user which patient we're talking about because it won't be obvious anymore.
        if action == -1:  # Retry
            continue  # Remain on the current row. 
        elif action == 1:  # Skip
            if current_row_index == len(csv_data) - 1:  # If it's the last row
                MediLink_ConfigLoader.log("Reached the end of the patient list.")
                print("Reached the end of the patient list. Looping back to the beginning.")
                current_row_index = 0  # Reset to the first row
            else:
                current_row_index += 1 # Move to the next row
            continue
        elif action == -2:  # Go back two patients and redo
            current_row_index = max(0, current_row_index - 2)  # Go back two rows, but not below 0
            continue

        # Code to handle the end of a patient record
        # TODO One day this can just not pause...
        if _ac():
            _ac().set_pause_status(True)  # Pause at the end of processing each patient record
        
        # PERFORMANCE FIX: Explicit cleanup at end of patient processing
        # Clear global state to prevent accumulation over processing sessions
        # Note: current_patient_context is preserved for F11 menu functionality
        if current_row_index != len(csv_data) - 1:  # Not the last patient
            last_processed_entry = None
            parsed_address_components.clear()
            try:
                if hasattr(CTX, 'last_processed_entry'):
                    CTX.last_processed_entry = None
                    CTX.parsed_address_components = {}
                else:
                    CTX['last_processed_entry'] = None
                    CTX['parsed_address_components'] = {}
            except Exception:
                pass
            
        current_row_index += 1  # Move to the next row by default

def open_medisoft(shortcut_path):
    try:
        os.startfile(shortcut_path)
        print("Medisoft is being opened...\n")
    except subprocess.CalledProcessError as e:
        print("Failed to open Medisoft:", e)
        print("Please manually open Medisoft.")
    except Exception as e:
        print("An unexpected error occurred:", e)
        print("Please manually open Medisoft.")
    finally:
        print("Press 'F12' to begin data entry.")

# Placeholder for any cleanup
def cleanup():
    print("\n**** Medibot Finished! ****\n")
    # THis might need to delete the staging stuff that gets set up by mostly MediLink but maybe other stuff too.
    pass 

class ExecutionState:
    def __init__(self, config_path, crosswalk_path, preloaded_config=None, preloaded_crosswalk=None):
        """
        Initialize execution state with configuration.
        
        Args:
            config_path: Path to config file (used if preloaded_config is None)
            crosswalk_path: Path to crosswalk file (used if preloaded_crosswalk is None)
            preloaded_config: Optional pre-loaded config dict to avoid double-loading
            preloaded_crosswalk: Optional pre-loaded crosswalk dict to avoid double-loading
        """
        try:
            # Use pre-loaded values if provided, otherwise load from paths
            if preloaded_config is not None and preloaded_crosswalk is not None:
                config, crosswalk = preloaded_config, preloaded_crosswalk
                MediLink_ConfigLoader.log("Using pre-loaded configuration", level="DEBUG")
            else:
                config, crosswalk = MediLink_ConfigLoader.load_configuration(config_path, crosswalk_path)
                MediLink_ConfigLoader.log("Loaded configuration from paths", level="DEBUG")
            
            MediLink_ConfigLoader.log("Configuration type: {}".format(type(config)), level="DEBUG")
            self.verify_config_type(config)
            self.crosswalk = crosswalk
            self.config = config
            MediLink_ConfigLoader.log("Config loaded successfully...")

            # Get APIClient via factory
            try:
                from MediCafe.api_factory import APIClientFactory
                factory = APIClientFactory()
                self.api_client = factory.get_shared_client()  # Use shared client for token caching benefits
                MediLink_ConfigLoader.log("ExecutionState using API Factory with shared client", level="INFO")
            except ImportError as e:
                # Fallback to basic API client
                try:
                    from MediCafe.core_utils import get_api_client
                    self.api_client = get_api_client()
                    MediLink_ConfigLoader.log("ExecutionState using fallback API client", level="WARNING")
                except ImportError as e2:
                    self.api_client = None
            
            # Log before calling crosswalk_update
            if self.api_client is not None:
                MediLink_ConfigLoader.log("Updating crosswalk with client and config...", level="INFO")
                update_successful = crosswalk_update(self.api_client, config, crosswalk)
            else:
                MediLink_ConfigLoader.log("Skipping crosswalk update - API client not available", level="WARNING")
                update_successful = False
            if update_successful:
                MediLink_ConfigLoader.log("Crosswalk update completed successfully.", level="INFO")
                print("Crosswalk update completed successfully.")
            else:
                record_startup_error("Crosswalk update failed.")

        except Exception as e:
            record_startup_error("MediBot: Failed to load or update configuration: {}".format(e))
            raise  # Re-throwing the exception or using a more sophisticated error handling mechanism might be needed
            # Handle the exception somehow (e.g., retry, halt, log)??
        
    def verify_config_type(self, config):
        MediLink_ConfigLoader.log("Verifying configuration type: {}".format(type(config)), level="DEBUG")
        if not isinstance(config, (dict, OrderedDict)):
            raise TypeError("Error: Configuration must be a dictionary or an OrderedDict. Check unpacking.")

# Import centralized logging configuration
try:
    from MediCafe.logging_config import PERFORMANCE_LOGGING
except ImportError:
    # Fallback to local flag if centralized config is not available
    PERFORMANCE_LOGGING = False

# Main script execution wrapped in try-except for error handling
if __name__ == "__main__":
    # Install unhandled exception hook to capture tracebacks
    try:
        if capture_unhandled_traceback is not None:
            sys.excepthook = capture_unhandled_traceback
    except Exception:
        pass

    e_state = None
    try:
        if PERFORMANCE_LOGGING:
            print("Initializing. Loading configuration and preparing environment...")
        
        # PROTECTION: Validate critical imports before proceeding
        print("Validating critical imports...")
        import_valid, import_state = validate_critical_imports()
        if not import_valid:
            print("CRITICAL: Import validation failed. Cannot continue.")
            print("This indicates a fundamental system configuration issue.")
            print("Please check:")
            print("  1. All MediBot modules exist in the MediBot directory")
            print("  2. Python path is correctly configured")
            print("  3. No syntax errors in MediBot modules")
            sys.exit(1)
        
        # Default configuration paths
        json_dir = os.path.join(os.path.dirname(__file__), '..', 'json')
        default_config_path = os.path.join(json_dir, 'config.json')
        default_crosswalk_path = os.path.join(json_dir, 'crosswalk.json')
        
        # Use MediCafe configuration system
        preloaded_config, preloaded_crosswalk = None, None
        config_path, crosswalk_path = None, None
        
        try:
            config_loader = get_config_loader_with_fallback()
            if config_loader and len(sys.argv) <= 1:
                preloaded_config, preloaded_crosswalk = config_loader.load_configuration()
            else:
                config_path = sys.argv[1] if len(sys.argv) > 1 else default_config_path
        except Exception:
            config_path = sys.argv[1] if len(sys.argv) > 1 else default_config_path
        
        # Define crosswalk path if not pre-loaded
        if preloaded_crosswalk is None:
            crosswalk_path = sys.argv[2] if len(sys.argv) > 2 else default_crosswalk_path
        
        e_state = ExecutionState(config_path, crosswalk_path, preloaded_config, preloaded_crosswalk)
        
        # Initialize constants from config
        MediBot_Preprocessor_lib.initialize(e_state.config)
        
        # PERFORMANCE OPTIMIZATION: Load both Medicare and Private patient databases during startup
        # Files are small (10K-20K rows each) so memory usage is minimal (~4MB total)
        # This eliminates the 1-2 second delay from user workflow entirely
        print("Loading patient databases...")
        MediLink_ConfigLoader.log("Loading patient databases...", level="INFO")
        
        try:
            medicare_path = e_state.config.get('MEDICARE_MAPAT_MED_PATH', "")
            private_path = e_state.config.get('MAPAT_MED_PATH', "")
            
            # Load both databases into separate caches
            medicare_cache = MediBot_Preprocessor.load_existing_patient_ids(medicare_path) if medicare_path else {}
            private_cache = MediBot_Preprocessor.load_existing_patient_ids(private_path) if private_path else {}
            
            # Store both caches for later use
            MediBot_Preprocessor.set_patient_caches(medicare_cache, private_cache)
            
            if PERFORMANCE_LOGGING:
                print("Patient databases loaded: {} Medicare, {} Private patients".format(
                    len(medicare_cache), len(private_cache)))
            MediLink_ConfigLoader.log("Patient databases loaded: {} Medicare, {} Private patients".format(
                len(medicare_cache), len(private_cache)), level="INFO")
                
        except Exception as e:
            MediLink_ConfigLoader.log("Warning: Could not load patient databases: {}".format(e), level="WARNING")
            if PERFORMANCE_LOGGING:
                print("Warning: Could not load patient databases - will load on demand")
        
        if PERFORMANCE_LOGGING:
            print("Loading CSV Data...")
        MediLink_ConfigLoader.log("Loading CSV Data...", level="INFO")
        csv_data = MediBot_Preprocessor_lib.load_csv_data(MediBot_Preprocessor_lib.CSV_FILE_PATH)
        
        # Pre-process CSV data to add combined fields & crosswalk values
        if PERFORMANCE_LOGGING:
            print("Pre-Processing CSV...")
        MediLink_ConfigLoader.log("Pre-processing CSV Data...", level="INFO")
        
        # TIMING: Start CSV preprocessing timing
        preprocessing_start_time = time.time()
        if PERFORMANCE_LOGGING:
            print("Starting CSV preprocessing at: {}".format(time.strftime("%H:%M:%S")))
        MediLink_ConfigLoader.log("Starting CSV preprocessing at: {}".format(time.strftime("%H:%M:%S")), level="INFO")
        
        # PROTECTION: Validate MediBot_Preprocessor before calling preprocess_csv_data
        if MediBot_Preprocessor is None:
            print("CRITICAL: MediBot_Preprocessor is None when trying to call preprocess_csv_data")
            print("This indicates the import failed silently during execution.")
            print("Import state at failure:")
            for module_name, module in import_state.items():
                status = "None" if module is None else "OK"
                print("  - {}: {}".format(module_name, status))
            print("Please check for syntax errors or missing dependencies in MediBot modules.")
            sys.exit(1)
        
        if not hasattr(MediBot_Preprocessor, 'preprocess_csv_data'):
            print("CRITICAL: MediBot_Preprocessor missing preprocess_csv_data function")
            print("Available functions: {}".format([attr for attr in dir(MediBot_Preprocessor) if not attr.startswith('_')]))
            sys.exit(1)
        
        MediBot_Preprocessor.preprocess_csv_data(csv_data, e_state.crosswalk)  
        
        # TIMING: End CSV preprocessing timing
        preprocessing_end_time = time.time()
        preprocessing_duration = preprocessing_end_time - preprocessing_start_time
        if PERFORMANCE_LOGGING:
            print("CSV preprocessing completed at: {} (Duration: {:.2f} seconds)".format(
                time.strftime("%H:%M:%S"), preprocessing_duration))
        MediLink_ConfigLoader.log("CSV preprocessing completed at: {} (Duration: {:.2f} seconds)".format(
            time.strftime("%H:%M:%S"), preprocessing_duration), level="INFO")
        
        headers = csv_data[0].keys()  # Ensure all headers are in place
        
        print("Performing Intake Scan...")
        MediLink_ConfigLoader.log("Performing Intake Scan...", level="INFO")
        identified_fields = MediBot_Preprocessor.intake_scan(headers, MediBot_Preprocessor_lib.field_mapping)
        
        # Reverse the identified_fields mapping for lookup
        reverse_mapping = {v: k for k, v in identified_fields.items()}
        
        # CSV Patient Triage
        interaction_mode = 'triage'  # Start in triage mode
        error_message = ""  # This will be filled if an error has occurred
        
        print("Load Complete...")
        MediLink_ConfigLoader.log("Load Complete event triggered. Clearing console. Displaying Menu...", level="INFO")
        # Windows XP console buffer fix: Use cls with echo to reset buffer state
        # Add a debug switch to optionally skip clearing the console for debugging purposes
        CLEAR_CONSOLE_ON_LOAD = True  # Clear screen before menu for cleaner UI
        if CLEAR_CONSOLE_ON_LOAD:
            _ = os.system('cls && echo.')
            # Re-display critical startup notices so the user still sees them
            if STARTUP_NOTICES:
                print("Important notices from startup:")
                for lvl, msg in STARTUP_NOTICES:
                    try:
                        print("[{}] {}".format(lvl, msg))
                    except Exception:
                        print(msg)
                print("-" * 60)
        
        proceed, selected_patient_ids, selected_indices, fixed_values, is_medicare = user_interaction(csv_data, interaction_mode, error_message, reverse_mapping)

        if proceed:
            # Filter csv_data for selected patients from Triage mode
            csv_data = [row for index, row in enumerate(csv_data) if index in selected_indices]
            
            # Check if MAPAT_MED_PATH is missing or invalid
            if (not _ac()) or (not _ac().get_mapat_med_path()) or (not os.path.exists(_ac().get_mapat_med_path())):
                record_startup_warning("Warning: MAPAT.MED PATH is missing or invalid. Please check the path configuration.")

            # PERFORMANCE OPTIMIZATION: Select the appropriate pre-loaded patient cache
            # Both caches were loaded during startup, now we just select the right one
            MediBot_Preprocessor.select_active_cache(is_medicare)
            if PERFORMANCE_LOGGING:
                print("Using {} patient cache for existing patient check".format("Medicare" if is_medicare else "Private"))

            # Perform the existing patients check (now uses cached data)
            existing_patients, patients_to_process = MediBot_Preprocessor.check_existing_patients(selected_patient_ids, _ac().get_mapat_med_path() if _ac() else '')
            
            # Initialize patient_info and table_title for notepad generation
            # These may be populated by existing_patients or remain empty
            patient_type = "MEDICARE" if is_medicare else "PRIVATE"
            patient_info = []
            table_title = "{} PATIENTS - EXISTING: No existing patients in this batch.".format(patient_type)
            
            if existing_patients:
                # Collect surgery dates and patient info for existing patients
                for patient_id, patient_name in existing_patients:
                    try:
                        # Find the row for this patient
                        patient_row = next((row for row in csv_data if row.get(reverse_mapping['Patient ID #2']) == patient_id), None)
                        if patient_row is None:
                            raise ValueError("Patient row not found for patient ID: {}".format(patient_id))
                        
                        # Use helper function to create patient entries
                        patient_entries = create_patient_entries_from_row(patient_row, reverse_mapping)
                        patient_info.extend(patient_entries)
                            
                    except Exception as e:
                        MediLink_ConfigLoader.log("Warning: Error retrieving data for patient ID '{}': {}".format(patient_id, e), level="WARNING")
                        patient_info.append(('Unknown Date', patient_name, patient_id, 'N/A', None))  # Append with 'Unknown Date' if there's an error

                # Display existing patients table using the enhanced display function
                table_title = "{} PATIENTS - EXISTING: The following patient(s) already EXIST in the system but may have new dates of service.\n      Their diagnosis codes may need to be updated manually by the user to the following list:".format(patient_type)
                MediBot_UI.display_enhanced_patient_table(
                    patient_info, 
                    table_title,
                    show_line_numbers=False,
                    config=e_state.config
                )
                
                # Update csv_data to exclude existing patients
                # TODO: Update this logic to handle patients that exist but need new charges added.
                csv_data = [row for row in csv_data if row[reverse_mapping['Patient ID #2']] in patients_to_process]

            # Identify dual-date NEW patients for anticipatory display
            dual_date_new_patients = []
            for row in csv_data:
                if len(row.get('_all_surgery_dates', [])) > 1:
                    patient_entries = create_patient_entries_from_row(row, reverse_mapping)
                    dual_date_new_patients.extend(patient_entries)
            
            # Define dual-date title once if needed
            dual_date_title = "{} PATIENTS - DUAL DATE-OF-SERVICE (ANTICIPATORY): These patients have multiple dates of service.\n      After the first date is entered via AHK, they will become EXISTING patients and may need manual diagnosis updates:".format(patient_type) if dual_date_new_patients else None

            # Generate notepad file if there's content to display
            if patient_info or dual_date_new_patients:
                try:
                    if dual_date_new_patients:
                        notepad_file_path = MediBot_Notepad_Utils.generate_combined_patients_notepad(
                            patient_info, table_title, dual_date_new_patients, dual_date_title
                        )
                    elif patient_info:
                        notepad_file_path = MediBot_Notepad_Utils.generate_existing_patients_notepad(patient_info, table_title)
                    else:
                        notepad_file_path = None

                    if notepad_file_path:
                        print("Patient reference table saved and opened in notepad: {}".format(notepad_file_path))
                except Exception as e:
                    print("Warning: Error creating notepad file: {}".format(e))

            # Display dual-date patients table on screen
            if dual_date_new_patients:
                MediBot_UI.display_enhanced_patient_table(
                    dual_date_new_patients,
                    dual_date_title,
                    show_line_numbers=False,
                    config=e_state.config
                )

            # Show NEW patients that will be processed (if any)
            if patients_to_process:
                # Collect surgery dates and patient info for NEW patients
                new_patient_info = []
                for row in csv_data:
                    # Use helper function to create patient entries
                    patient_entries = create_patient_entries_from_row(row, reverse_mapping)
                    new_patient_info.extend(patient_entries)

                # Display new patients table using the enhanced display function
                MediBot_UI.display_enhanced_patient_table(
                    new_patient_info, 
                    "{} PATIENTS - NEW: The following patient(s) will be automatically entered into Medisoft:".format(patient_type),
                    show_line_numbers=True,
                    config=e_state.config
                )

            # Check if there are patients left to process
            if len(patients_to_process) == 0:
                proceed = input("\nAll patients have been processed. Continue anyway?: ").lower().strip() in ['yes', 'y']
            else:
                proceed = input("\nDo you want to proceed with entering {} new patient(s) into Medisoft? (yes/no): ".format(len(patients_to_process))).lower().strip() in ['yes', 'y']

            # IMPLEMENTED: MediBot_Charges integration is complete (see lines 867-881)
            # The charge enrichment step is implemented below with proper error handling
            # and can be enabled via ENABLE_CHARGES_ENRICHMENT config flag.

            if proceed:
                print("\nRemember, when in Medisoft:")
                print("  Press 'F8'  to create a New Patient.")
                print("  Press 'F12' to begin data entry.")
                print("  Press 'F11' at any time to Pause.")
                print("\n*** Press [Enter] when ready to begin! ***")
                input()
                MediLink_ConfigLoader.log("Opening Medisoft...")
                open_medisoft(_ac().get_medisoft_shortcut() if _ac() else '')
                if _ac():
                    _ac().set_pause_status(True)
                _ = manage_script_pause(csv_data, error_message, reverse_mapping)
                # IMPLEMENTED: Charges enrichment with complete error handling and fallback
                # STRATEGIC NOTE: This integration is production-ready with the following features:
                # - Complete charge calculation and bundling logic (MediLink_Charges.py)
                # - Bilateral procedure bundling with 30-day expiration
                # - Tiered pricing for private insurance and Medicare
                # - Read-only historical lookups with user notifications
                # - Deductible flagging (pending OptumAI integration)
                # - XP SP3 + Python 3.4.4 compatible implementation
                if e_state.config.get('ENABLE_CHARGES_ENRICHMENT', False):
                    try:
                        from MediCafe.smart_import import get_components
                        MediBot_Charges = get_components('medibot_charges')

                        field_mapping = MediBot_Preprocessor_lib.field_mapping  # Ensure defined for enrichment

                        csv_data, field_mapping, reverse_mapping, fixed_values = MediBot_Charges.enrich_with_charges(
                            csv_data, field_mapping, reverse_mapping, fixed_values
                        )
                    except Exception as e:
                        MediLink_ConfigLoader.log("Charges enrichment failed (prototype): {}. Continuing without enrichment.".format(e), level="WARNING")
                        print("Warning: Charges feature skipped due to error. Proceeding with standard flow.")
                else:
                    MediLink_ConfigLoader.log("Charges enrichment disabled in config. Skipping.", level="INFO")
                data_entry_loop(csv_data, MediBot_Preprocessor_lib.field_mapping, reverse_mapping, fixed_values)
                cleanup()                
            else:
                print("Data entry canceled by user. Exiting MediBot.")
    except Exception as e:
        if e_state:
            interaction_mode = 'error'  # Switch to error mode
            error_message = str(e)  # Capture the error message
        
        # ENHANCED ERROR DIAGNOSTICS
        print("=" * 60)
        print("MEDIBOT EXECUTION FAILURE")
        print("=" * 60)
        print("Error: {}".format(e))
        print("Error type: {}".format(type(e).__name__))
        
        # Check for the specific failure pattern
        if "'NoneType' object has no attribute" in str(e):
            print("DIAGNOSIS: This is the import failure pattern.")
            print("A module import returned None, causing a method call to fail.")
            print("This typically indicates:")
            print("  1. Syntax error in a MediBot module")
            print("  2. Missing dependency")
            print("  3. Import path issue")
            print("  4. Circular import problem")
            
            # Show current import state
            print("Current import state:")
            try:
                import_state = {
                    'MediBot_Preprocessor': MediBot_Preprocessor,
                    'MediBot_Preprocessor_lib': MediBot_Preprocessor_lib,
                    'MediBot_UI': MediBot_UI,
                    'MediBot_Crosswalk_Library': MediBot_Crosswalk_Library
                }
                for module_name, module in import_state.items():
                    status = "None" if module is None else "OK"
                    print("  - {}: {}".format(module_name, status))
            except Exception as diag_e:
                print("  - Unable to diagnose import state: {}".format(diag_e))
        
        print("=" * 60)

        # Collect and submit error report
        try:
            if submit_support_bundle_email is not None:
                from MediCafe.error_reporter import collect_support_bundle
                zip_path = collect_support_bundle(include_traceback=True)
                if zip_path:
                    try:
                        from MediCafe.core_utils import check_internet_connection
                        online = check_internet_connection()
                    except ImportError:
                        # If we can't check connectivity during error reporting, assume offline
                        # to preserve the error bundle for later
                        online = False
                        print("Warning: Could not check internet connectivity - preserving error bundle.")
                    if online:
                        success = submit_support_bundle_email(zip_path)
                        if success:
                            # On success, remove the bundle
                            try:
                                os.remove(zip_path)
                            except Exception:
                                pass
                        else:
                            # Preserve bundle for manual retry
                            print("Error report send failed - bundle preserved at {} for retry.".format(zip_path))
                    else:
                        print("Offline - error bundle queued at {} for retry when online.".format(zip_path))
                else:
                    print("Failed to create error report bundle.")
            else:
                print("Error reporting not available - check MediCafe installation.")
        except Exception as report_e:
            print("Error report collection failed: {}".format(report_e))

        # Handle the error by calling user interaction with the error information
        if 'identified_fields' in locals():
            _ = user_interaction(csv_data, interaction_mode, error_message, reverse_mapping)
        else:
            print("Please ensure CSV headers match expected field names in config file, then re-run Medibot.")