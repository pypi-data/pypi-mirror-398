#MediBot_UI.py
import ctypes, time, re
from ctypes import wintypes
from sys import exit
from datetime import datetime

# Set up paths using core utilities

from MediCafe.core_utils import get_shared_config_loader
MediLink_ConfigLoader = get_shared_config_loader()
if MediLink_ConfigLoader is None:
    raise ImportError(
        "[MediBot_UI] CRITICAL: MediLink_ConfigLoader module import failed. "
        "This module requires MediLink_ConfigLoader to function. "
        "Check PYTHONPATH, module dependencies, and ensure MediCafe package is properly installed."
    )

# Import current_patient_context with fallback
try:
    from MediBot import current_patient_context
except ImportError:
    current_patient_context = None
    
# Set up lazy configuration loading using core utilities
from MediCafe.core_utils import create_config_cache
_get_config, (_config_cache, _crosswalk_cache) = create_config_cache()

# Import cache lookup functions for deductible remaining amount
try:
    from MediLink.insurance_type_cache import lookup as cache_lookup, get_csv_dir_from_config
except ImportError:
    cache_lookup = None
    get_csv_dir_from_config = None

def display_enhanced_patient_table(patient_info, title, show_line_numbers=True, interactive=False, config=None):
    """
    Display an enhanced patient table with multiple surgery dates and diagnosis codes.
    
    Args:
        patient_info: List of tuples (surgery_date, patient_name, patient_id, diagnosis_code, patient_row)
        title: Title for the table section
        show_line_numbers: Whether to show line numbers (True for new patients, False for existing)
        interactive: Whether to use interactive mode (deprecated)
        config: Optional config dictionary for cache lookup (if None, cache lookups will be skipped)
    """
    if not patient_info:
        return
    
    print(title)
    print()
    
    # Get csv_dir for cache lookup
    csv_dir = ''
    if get_csv_dir_from_config and config:
        try:
            csv_dir = get_csv_dir_from_config(config) or ''
        except Exception:
            csv_dir = ''
    
    # Helper function to format remaining amount for display (duplicated from MediLink_Display_Utils for module independence)
    def _format_remaining_amount(remaining_amount_str):
        """Format remaining amount for display"""
        if not remaining_amount_str or remaining_amount_str.strip() == '':
            return 'N/A'
        try:
            # Try to parse as float and format
            amount = float(remaining_amount_str)
            if amount == 0:
                return '0.00'
            return '{:.2f}'.format(amount)  # Format as decimal without $ prefix
        except (ValueError, TypeError):
            return str(remaining_amount_str) if remaining_amount_str else 'N/A'
    
    # Normalize data to avoid None and unexpected container types in sort key
    normalized_info = []
    for surgery_date, patient_name, patient_id, diagnosis_code, patient_row in patient_info:
        # Normalize date into comparable key and display string
        display_date = None
        current_date_dt = None
        try:
            if hasattr(surgery_date, 'strftime'):
                display_date = surgery_date.strftime('%m-%d')
                current_date_dt = surgery_date
            elif isinstance(surgery_date, str):
                # Date strings may be MM-DD-YYYY or already MM-DD
                parts = surgery_date.split('-') if surgery_date else []
                if len(parts) == 3 and all(parts):
                    display_date = "{}-{}".format(parts[0], parts[1])
                    try:
                        current_date_dt = datetime.strptime(surgery_date, '%m-%d-%Y')
                    except Exception:
                        current_date_dt = None
                else:
                    display_date = surgery_date or 'Unknown Date'
                    current_date_dt = None
            else:
                display_date = str(surgery_date) if surgery_date is not None else 'Unknown Date'
                current_date_dt = None
        except Exception:
            display_date = str(surgery_date) if surgery_date is not None else 'Unknown Date'
            current_date_dt = None
        
        # Normalize diagnosis display: only show "-Not Found-" when explicitly flagged as N/A
        # XP SP3 + Py3.4.4 compatible error handling
        display_diagnosis = diagnosis_code
        try:
            if diagnosis_code == "N/A":
                display_diagnosis = "-Not Found-"
            elif diagnosis_code is None:
                display_diagnosis = "-Not Found-"
            elif isinstance(diagnosis_code, str) and diagnosis_code.strip() == "":
                display_diagnosis = "-Not Found-"
            else:
                display_diagnosis = str(diagnosis_code)
        except (TypeError, ValueError) as e:
            # Log the specific error for debugging (ASCII-only compatible)
            try:
                error_msg = "Error converting diagnosis code to string: {}".format(str(e))
                MediLink_ConfigLoader.log(error_msg, level="WARNING")
            except Exception:
                # Fallback logging if string formatting fails
                MediLink_ConfigLoader.log("Error converting diagnosis code to string", level="WARNING")
            display_diagnosis = "-Not Found-"

        # Grouping: place all dates for a patient together under their earliest date
        primary_date_dt = None
        within_index = 0
        last_name_key = ''
        first_name_key = ''
        try:
            all_dates = []
            if patient_row is not None:
                raw_dates = patient_row.get('_all_surgery_dates', [])
                # Convert to datetime list and find primary
                for d in raw_dates:
                    try:
                        if hasattr(d, 'strftime'):
                            all_dates.append(d)
                        elif isinstance(d, str):
                            all_dates.append(datetime.strptime(d, '%m-%d-%Y'))
                    except Exception:
                        pass
                if all_dates:
                    all_dates.sort()
                    primary_date_dt = all_dates[0]
                    # Determine within-patient index of current date
                    if current_date_dt is not None:
                        # Find matching index by exact date
                        for idx, ad in enumerate(all_dates):
                            if current_date_dt == ad:
                                within_index = idx
                                break
                # Prefer explicit last/first from row for sorting
                try:
                    ln = patient_row.get('Patient Last')
                    fn = patient_row.get('Patient First')
                    if isinstance(ln, str):
                        last_name_key = ln.strip().upper()
                    if isinstance(fn, str):
                        first_name_key = fn.strip().upper()
                except Exception:
                    pass
        except Exception:
            primary_date_dt = None
            within_index = 0

        # Fallbacks if parsing failed
        if primary_date_dt is None:
            primary_date_dt = current_date_dt
        # If last/first not available from row, parse from display name "LAST, FIRST ..."
        if not last_name_key and isinstance(patient_name, str):
            try:
                parts = [p.strip() for p in patient_name.split(',')]
                if len(parts) >= 1:
                    last_name_key = parts[0].upper()
                if len(parts) >= 2:
                    first_name_key = parts[1].split()[0].upper() if parts[1] else ''
            except Exception:
                last_name_key = ''
                first_name_key = ''

        # Build composite sort key per requirement: by earliest date, then last name within date,
        # while keeping same patient's additional dates directly under the first line
        composite_sort_key = (primary_date_dt, last_name_key, first_name_key, str(patient_id or ''), within_index)
        
        # Perform cache lookup for deductible remaining amount
        remaining_amount_display = 'N/A'
        if cache_lookup and csv_dir and current_date_dt:
            try:
                # Extract patient_id from tuple or patient_row
                lookup_patient_id = str(patient_id or '')
                if not lookup_patient_id and patient_row:
                    lookup_patient_id = str(patient_row.get('Patient ID #2', ''))
                
                if lookup_patient_id:
                    # Convert surgery_date to YYYY-MM-DD format for cache lookup
                    service_date_iso = current_date_dt.strftime('%Y-%m-%d')
                    # Lookup cache with return_full=True to get remaining_amount
                    cache_result = cache_lookup(patient_id=lookup_patient_id, csv_dir=csv_dir, return_full=True, service_date=service_date_iso)
                    if cache_result:
                        remaining_amount = cache_result.get('remaining_amount', '')
                        remaining_amount_display = _format_remaining_amount(remaining_amount)
            except Exception as e:
                # Fail gracefully - log at DEBUG level only (avoid HIPAA data in logs)
                try:
                    MediLink_ConfigLoader.log("Cache lookup error in display_enhanced_patient_table: {}".format(str(e)), level="DEBUG")
                except Exception:
                    pass  # Silently fail if logging unavailable
        
        # Append with remaining_amount as 6th element
        normalized_info.append((composite_sort_key, display_date, str(patient_name or ''), str(patient_id or ''), display_diagnosis, remaining_amount_display))
    
    # Sort so that all entries for a patient are grouped under their earliest date
    normalized_info.sort(key=lambda x: x[0])
    
    # Calculate column widths for proper alignment
    max_patient_id_len = max(len(pid) for _, _, _, pid, _, _ in normalized_info)
    max_patient_name_len = max(len(pname) for _, _, pname, _, _, _ in normalized_info)
    max_diagnosis_len = max(len(dcode) for _, _, _, _, dcode, _ in normalized_info)
    max_remaining_amount_len = max(len(ramt) for _, _, _, _, _, ramt in normalized_info)
    
    # Ensure minimum widths for readability
    max_patient_id_len = max(max_patient_id_len, 5)  # 5-digit ID max
    max_patient_name_len = max(max_patient_name_len, 12)  # "Patient Name" header
    max_diagnosis_len = max(max_diagnosis_len, 10)  # "Diagnosis" header
    max_remaining_amount_len = max(max_remaining_amount_len, 12)  # "Rem Amt" header
    
    # Display header row
    header_format = "{:<3} {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "} | {:<" + str(max_remaining_amount_len) + "}"
    print(header_format.format("No.", "Date", "ID", "Name", "Diagnosis", "Rem Amt"))
    # Calculate separator width: column widths + padding between columns (| + spaces = ~3 per separator * 5 columns = 15)
    print("-" * (10 + max_patient_id_len + max_patient_name_len + max_diagnosis_len + max_remaining_amount_len + 15))
    
    current_patient = None
    line_number = 1
    
    for sort_key, formatted_date, patient_name, patient_id, display_diagnosis, remaining_amount_display in normalized_info:
        if current_patient == patient_id:
            patient_id_dashes = '-' * len(patient_id)
            patient_name_dashes = '-' * len(patient_name)
            remaining_amount_dashes = '-' * len(remaining_amount_display)
            secondary_format = "     {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "} | {:<" + str(max_remaining_amount_len) + "}"
            print(secondary_format.format(formatted_date, patient_id_dashes, patient_name_dashes, display_diagnosis, remaining_amount_dashes))
        else:
            current_patient = patient_id
            if show_line_numbers:
                primary_format = "{:03d}: {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "} | {:<" + str(max_remaining_amount_len) + "}"
                print(primary_format.format(line_number, formatted_date, patient_id, patient_name, display_diagnosis, remaining_amount_display))
                line_number += 1
            else:
                primary_format = "     {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "} | {:<" + str(max_remaining_amount_len) + "}"
                print(primary_format.format(formatted_date, patient_id, patient_name, display_diagnosis, remaining_amount_display))

    if interactive:
        for i in range(len(patient_info)):
            # Redraw table up to current row (prototype: simple print)
            print("\n" + title)
            print("|" + "-" * 80 + "|")  # ASCII table border
            print("| Date | Name | ID | Diagnosis | Minutes | Deductible | Charge | Flags |")
            print("|" + "-" * 80 + "|")

            # Print previous rows (enriched)
            for j in range(i):
                r = patient_info[j]
                print("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                    r[0], r[1][:10], r[2], r[3], r.get('Minutes', ''), r.get('Deductible', 'N/A'), r.get('Charge', ''), r.get('Flags', '')))

            # Prompt for current row
            current = patient_info[i]
            print("| {} | {} | {} | {} | [Input] | {} |        |               |".format(
                current[0], current[1][:10], current[2], current[3], current.get('Deductible', 'N/A')))  # Highlight Minutes column

            while True:
                try:
                    minutes_str = raw_input("Enter Minutes (1-59): ")
                    minutes = int(minutes_str)
                    if minutes > 59:
                        minutes = 59
                        confirm = raw_input("Capped to 59. Proceed? (Y/N): ").upper()
                        if confirm != 'Y': continue
                    if 1 <= minutes <= 59: break
                    print("Invalid: 1-59 only.")
                except ValueError:
                    print("Invalid: Enter number.")

            # Enrich and update row
            enriched_row = enrich_single_row(current, minutes, patient_info[i][4])  # Pass original row dict
            patient_info[i] = (enriched_row['Surgery Date'], enriched_row['Patient Name'], enriched_row['Patient ID #2'], enriched_row['Diagnosis Code'], enriched_row)  # Update tuple

            # Redraw full table after update
            # (Repeat print logic above with all rows up to i)

        return patient_info  # Enriched

# Function to check if a specific key is pressed
def _get_vk_codes():
    """Get VK codes from config."""
    config, _ = _get_config()
    VK_END = int(config.get('VK_END', "23"), 16)  # Default to 23 if not in config
    VK_PAUSE = int(config.get('VK_PAUSE', "24"), 16)  # Default to 24 if not in config
    return VK_END, VK_PAUSE



class AppControl:
    def __init__(self):
        self.script_paused = False
        self.mapat_med_path = ''
        self.medisoft_shortcut = ''
        # PERFORMANCE FIX: Add configuration caching to reduce lookup overhead
        self._config_cache = {}  # Cache for Medicare vs Private configuration lookups
        # Load initial paths from config when instance is created
        try:
            self.load_paths_from_config()
        except Exception:
            # Defer configuration loading until first access if config is unavailable
            self._deferred_load = True
        else:
            self._deferred_load = False

    def get_pause_status(self):
        return self.script_paused

    def set_pause_status(self, status):
        self.script_paused = status

    def get_mapat_med_path(self):
        return self.mapat_med_path

    def set_mapat_med_path(self, path):
        self.mapat_med_path = path

    def get_medisoft_shortcut(self):
        return self.medisoft_shortcut

    def set_medisoft_shortcut(self, path):
        self.medisoft_shortcut = path

    def load_paths_from_config(self, medicare=False):
        # Load configuration when needed
        config, _ = _get_config()
        
        # PERFORMANCE FIX: Cache configuration lookups to reduce Medicare vs Private overhead
        cache_key = 'medicare' if medicare else 'private'
        
        if cache_key not in self._config_cache:
            # Build cache entry for this configuration type
            if medicare:
                cached_config = {
                    'mapat_path': config.get('MEDICARE_MAPAT_MED_PATH', ""),
                    'shortcut': config.get('MEDICARE_SHORTCUT', "")
                }
            else:
                cached_config = {
                    'mapat_path': config.get('MAPAT_MED_PATH', ""),
                    'shortcut': config.get('PRIVATE_SHORTCUT', "")
                }
            self._config_cache[cache_key] = cached_config
        
        # Use cached values to avoid repeated config lookups
        cached = self._config_cache[cache_key]
        self.mapat_med_path = cached['mapat_path']
        self.medisoft_shortcut = cached['shortcut']

def _get_app_control():
    global app_control
    try:
        ac = app_control
    except NameError:
        ac = None
    if ac is None:
        ac = AppControl()
    # If deferred, attempt first load now
    try:
        if getattr(ac, '_deferred_load', False):
            ac.load_paths_from_config()
            ac._deferred_load = False
    except Exception:
        pass
    globals()['app_control'] = ac
    return ac

# Lazily initialize app_control to avoid config load at import time
try:
    app_control
except NameError:
    app_control = None


def is_key_pressed(key_code):
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    user32.GetAsyncKeyState.restype = wintypes.SHORT
    user32.GetAsyncKeyState.argtypes = [wintypes.INT]
    return user32.GetAsyncKeyState(key_code) & 0x8000 != 0

def manage_script_pause(csv_data, error_message, reverse_mapping):
    user_action = 0 # initialize as 'continue'
    VK_END, VK_PAUSE = _get_vk_codes()
    
    ac = _get_app_control()
    if not ac.get_pause_status() and is_key_pressed(VK_PAUSE):
        ac.set_pause_status(True)
        print("Script paused. Opening menu...")
        interaction_mode = 'normal'  # Assuming normal interaction mode for script pause
        user_action = user_interaction(csv_data, interaction_mode, error_message, reverse_mapping)
    
    while ac.get_pause_status():
        if is_key_pressed(VK_END):
            ac.set_pause_status(False)
            print("Continuing...")
        elif is_key_pressed(VK_PAUSE):
            user_action = user_interaction(csv_data, 'normal', error_message, reverse_mapping)
        time.sleep(0.1)
    
    return user_action

# Menu Display & User Interaction
def display_patient_selection_menu(csv_data, reverse_mapping, proceed_as_medicare):
    selected_patient_ids = []
    selected_indices = []

    # TODO: Future enhancement - make this configurable via config file
    # Example: config.get('silent_initial_selection', True)
    SILENT_INITIAL_SELECTION = True  # Set to False to restore original interactive behavior

    def display_menu_header(title):
        print("\n" + "-" * 60)
        print(title)
        print("-" * 60)

    def display_patient_list(csv_data, reverse_mapping, medicare_filter=False, exclude_medicare=False):
        medicare_policy_pattern = r"^[a-zA-Z0-9]{11}$"  # Regex pattern for 11 alpha-numeric characters
        primary_policy_number_header = reverse_mapping.get('Primary Policy Number', 'Primary Policy Number')
        primary_insurance_header = reverse_mapping.get('Primary Insurance', 'Primary Insurance')  # Adjust field name as needed
        
        displayed_indices = []
        displayed_patient_ids = []

        for index, row in enumerate(csv_data):
            policy_number = row.get(primary_policy_number_header, "")
            primary_insurance = row.get(primary_insurance_header, "").upper()
            
            if medicare_filter and (not re.match(medicare_policy_pattern, policy_number) or "MEDICARE" not in primary_insurance):
                continue
            if exclude_medicare and re.match(medicare_policy_pattern, policy_number) and "MEDICARE" in primary_insurance:
                continue

            patient_id_header = reverse_mapping['Patient ID #2']
            patient_name_header = reverse_mapping['Patient Name']
            patient_id = row.get(patient_id_header, "N/A")
            patient_name = row.get(patient_name_header, "Unknown")
            surgery_date = row.get('Surgery Date', "Unknown Date")
            # Format surgery_date safely whether datetime/date or string
            try:
                formatted_date = surgery_date.strftime('%m-%d')
            except Exception:
                formatted_date = str(surgery_date)
            
            # Only display if not in silent mode
            if not SILENT_INITIAL_SELECTION:
                print("{0:03d}: {3} (ID: {2}) {1} ".format(index+1, patient_name, patient_id, formatted_date))

            displayed_indices.append(index)
            displayed_patient_ids.append(patient_id)

        return displayed_indices, displayed_patient_ids

    if proceed_as_medicare:
        if not SILENT_INITIAL_SELECTION:
            display_menu_header("MEDICARE Patient Selection for Today's Data Entry")
        selected_indices, selected_patient_ids = display_patient_list(csv_data, reverse_mapping, medicare_filter=True)
    else:
        if not SILENT_INITIAL_SELECTION:
            display_menu_header("PRIVATE Patient Selection for Today's Data Entry")
        selected_indices, selected_patient_ids = display_patient_list(csv_data, reverse_mapping, exclude_medicare=True)

    if not SILENT_INITIAL_SELECTION:
        print("-" * 60)
        proceed = input("\nDo you want to proceed with the selected patients? (yes/no): ").lower().strip() in ['yes', 'y']
    else:
        # Auto-confirm in silent mode
        proceed = True

    if not proceed:
        if not SILENT_INITIAL_SELECTION:
            display_menu_header("Patient Selection for Today's Data Entry")
            selected_indices, selected_patient_ids = display_patient_list(csv_data, reverse_mapping)
            print("-" * 60)
            
            while True:
                while True:
                    selection = input("\nEnter the number(s) of the patients you wish to proceed with\n(e.g., 1, 3, 5): ").strip()
                    if not selection:
                        print("Invalid entry. Please provide at least one number.")
                        continue
                    
                    selection = selection.replace('.', ',')  # Replace '.' with ',' in the user input just in case
                    selected_indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]  
                    
                    if not selected_indices:
                        print("Invalid entry. Please provide at least one integer.")
                        continue
                    
                    proceed = True
                    break
                
                if not selection:
                    print("Invalid entry. Please provide at least one number.")
                    continue
                
                selection = selection.replace('.', ',')  # Replace '.' with ',' in the user input just in case
                selected_indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]  
                
                if not selected_indices:
                    print("Invalid entry. Please provide at least one integer.")
                    continue
                
                proceed = True
                break

    patient_id_header = reverse_mapping['Patient ID #2']
    selected_patient_ids = [csv_data[i][patient_id_header] for i in selected_indices if i < len(csv_data)]

    return proceed, selected_patient_ids, selected_indices

def display_menu_header(title):
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)

def handle_user_interaction(interaction_mode, error_message):
    
    while True:
        # If interaction_mode is neither 'triage' nor 'error', then it's normal mode.
        title = "Error Occurred" if interaction_mode == 'error' else "Data Entry Options"
        display_menu_header(title)

        if interaction_mode == 'error':
            print("\nERROR: ", error_message)

        # PERFORMANCE FIX: Display patient context to address "won't be obvious anymore" issue
        # Show user which patient and field they're working with for better F11 menu usability
        if current_patient_context:
            patient_name = current_patient_context.get('patient_name', 'Unknown Patient')
            surgery_date = current_patient_context.get('surgery_date', 'Unknown Date')
            last_field = current_patient_context.get('last_field', 'Unknown Field')
            print("\nCurrent Context:")
            print("  Patient: {}".format(patient_name))
            print("  Surgery Date: {}".format(surgery_date))
            print("  Last Field: {}".format(last_field))
            print("")

        # Menu options with improved context
        print("1: Retry last entry")
        print("2: Skip to next patient and continue")
        print("3: Go back two patients and redo")
        print("4: Exit script")
        print("-" * 60)
        choice = input("Enter your choice (1/2/3/4): ").strip()
        
        if choice == '1':
            print("Selected: 'Retry last entry'. Please press 'F12' to continue.")
            return -1
        elif choice == '2':
            print("Selected: 'Skip to next patient and continue'. Please press 'F12' to continue.")
            return 1
        elif choice == '3':
            print("Selected: 'Go back two patients and redo'. Please press 'F12' to continue.")
            # Returning a specific value to indicate the action of going back two patients
            # but we might run into a problem if we stop mid-run on the first row?
            return -2
        elif choice == '4':
            print("Exiting the script.")
            exit()
        else:
            print("Invalid choice. Please enter a valid number.")

def user_interaction(csv_data, interaction_mode, error_message, reverse_mapping):
    global app_control  # Use the instance of AppControl
    selected_patient_ids = []
    selected_indices = []

    if interaction_mode == 'triage':
        display_menu_header("            =(^.^)= Welcome to MediBot! =(^.^)=")
        
        # Ensure app_control is initialized before using it in triage
        ac = _get_app_control()
        app_control = ac

        while True:
            try:
                response = input("\nAm I processing Medicare patients? (yes/no): ").lower().strip()    
                
                if not response:
                    print("A response is required. Please try again.")
                    continue
                
                if response in ['yes', 'y']:
                    ac.load_paths_from_config(medicare=True)
                    break
                elif response in ['no', 'n']:
                    ac.load_paths_from_config(medicare=False)
                    break
                else:
                    print("Invalid entry. Please enter 'yes' or 'no'.")
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled by user. Exiting script.")

        # Load configuration when needed
        config, _ = _get_config()
        fixed_values = config.get('fixed_values', {})  # Get fixed values from config json 
        if response in ['yes', 'y']:
            medicare_added_fixed_values = config.get('medicare_added_fixed_values', {})
            fixed_values.update(medicare_added_fixed_values)  # Add any medicare-specific fixed values from config
        
        proceed, selected_patient_ids, selected_indices = display_patient_selection_menu(csv_data, reverse_mapping, response in ['yes', 'y'])
        is_medicare = response in ['yes', 'y']
        return proceed, selected_patient_ids, selected_indices, fixed_values, is_medicare

    # For non-triage modes (error, normal), return the action code directly
    # The caller (manage_script_pause) expects an integer for flow control
    result = handle_user_interaction(interaction_mode, error_message)
    if isinstance(result, int):
        return result
    # Unexpected return type - signal continue
    return 0