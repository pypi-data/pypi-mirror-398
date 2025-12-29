"""
# Create a summary JSON
summary = {
    "Payer ID": ins_payerID,
    "Provider": provider_last_name,
    "Member ID": ins_memberID,
    "Date of Birth": dob,
    "Patient Name": patient_name,
    "Patient Info": {
        "DOB": dob,
        "Address": "{} {}".format(patient_info.get("addressLine1", ""), patient_info.get("addressLine2", "")).strip(),
        "City": patient_info.get("city", ""),
        "State": patient_info.get("state", ""),
        "ZIP": patient_info.get("zip", ""),
        "Relationship": patient_info.get("relationship", "")
    },
    "Insurance Info": {
        "Payer Name": insurance_info.get("payerName", ""),
        "Payer ID": ins_payerID,
        "Member ID": ins_memberID,
        "Group Number": insurance_info.get("groupNumber", ""),
        "Insurance Type": ins_insuranceType,
        "Type Code": ins_insuranceTypeCode,
        "Address": "{} {}".format(insurance_info.get("addressLine1", ""), insurance_info.get("addressLine2", "")).strip(),
        "City": insurance_info.get("city", ""),
        "State": insurance_info.get("state", ""),
        "ZIP": insurance_info.get("zip", "")
    },
    "Policy Info": {
        "Eligibility Dates": eligibilityDates,
        "Policy Member ID": policy_info.get("memberId", ""),
        "Policy Status": policy_status
    },
    "Deductible Info": {
        "Remaining Amount": remaining_amount
    }
}

Features Added:
1. Allows users to manually input patient information for deductible lookup before processing CSV data.
2. Supports multiple manual requests, each generating its own Notepad file.
3. Validates user inputs and provides feedback on required formats.
4. Displays available Payer IDs as a note after manual entries.

UPGRADED TO LATEST CORE_UTILS:
- Uses setup_project_path() for standardized path management
- Uses get_api_core_client() for improved API client handling
- Uses create_config_cache() for better performance
- Uses log_import_error() for enhanced error logging
- Improved import error handling with fallbacks
"""
# MediLink_Deductible.py
"""
TODO Consdier the possibility of being CSV agnostic and looking for the date of service up to 60 days old and
then with an option to select specific patients to look up for all the valid rows.

"""
import os, sys, json, time
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent directory to Python path to access MediCafe module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Use latest core_utils for standardized setup and imports
try:
    from MediCafe.core_utils import (
        setup_project_path, 
        get_shared_config_loader, 
        get_api_core_client,
        log_import_error,
        create_config_cache
    )
    # Set up project paths using latest core_utils
    project_dir = setup_project_path(__file__)
    MediLink_ConfigLoader = get_shared_config_loader()

    # Import api_core for eligibility functions
    try:
        from MediCafe import api_core
    except ImportError:
        api_core = None
    
    # Import deductible utilities from MediCafe
    try:
        from MediCafe.deductible_utils import (
            validate_and_format_date,
            convert_eligibility_to_enhanced_format,
            resolve_payer_ids_from_csv,
            get_payer_id_for_patient,
            merge_responses,
            backfill_enhanced_result,
            _extract_service_date_from_csv_row,
            is_valid_insurance_code,
            extract_group_number_from_csv_row,
            collect_insurance_type_mapping_from_response
        )
    except ImportError as e:
        print("Warning: Unable to import MediCafe.deductible_utils: {}".format(e))
        # Fallback to local functions if utilities not available
        validate_and_format_date = None
        convert_eligibility_to_enhanced_format = None
        resolve_payer_ids_from_csv = None
        get_payer_id_for_patient = None
        merge_responses = None
        _extract_service_date_from_csv_row = None
        is_valid_insurance_code = None
        extract_group_number_from_csv_row = None
        collect_insurance_type_mapping_from_response = None
except ImportError as e:
    print("Error: Unable to import MediCafe.core_utils. Please ensure MediCafe package is properly installed.")
    # Don't call log_import_error here since it's not available yet
    print("Import error: {}".format(e))
    sys.exit(1)

# Safe import for requests with fallback
try:
    import requests
except ImportError:
    requests = None
    print("Warning: requests module not available. Some API functionality may be limited.")

try:
    from MediLink import MediLink_Deductible_Validator
except ImportError as e:
    print("Warning: Unable to import MediLink_Deductible_Validator: {}".format(e))
    import MediLink_Deductible_Validator

try:
    from MediBot import MediBot_Preprocessor_lib
except ImportError as e:
    print("Warning: Unable to import MediBot_Preprocessor_lib: {}".format(e))
    try:
        import MediBot_Preprocessor_lib  # type: ignore
    except ImportError as e2:
        print("Error: Cannot import MediBot_Preprocessor_lib: {}".format(e2))
        print("This module is required for CSV processing.")
        sys.exit(1)

# Fallback date validation function if utilities not available
def _fallback_validate_and_format_date(date_str):
    """Fallback date validation function if MediCafe.deductible_utils not available"""
    if validate_and_format_date is not None:
        return validate_and_format_date(date_str)
    else:
        # Simple fallback implementation
        try:
            from datetime import datetime
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return None

# Local helpers (keep v1 self-contained)
def _parse_remaining_amount(value):
    """Best-effort parser for cached remaining_amount values."""
    try:
        if value is None:
            return False, 0.0
        if isinstance(value, (int, float)):
            return True, float(value)
        text = str(value).strip()
        if not text:
            return False, 0.0
        lowered = text.lower()
        if lowered in ('not found', 'na', 'n/a'):
            return False, 0.0
        sanitized = text.replace('$', '').replace(',', '')
        return True, float(sanitized)
    except Exception:
        return False, 0.0

# Use shared utility function from MediCafe.deductible_utils
# If import failed, define fallback
try:
    _is_valid_insurance_code = is_valid_insurance_code
except NameError:
    def _is_valid_insurance_code(code):
        """Fallback validation if utility import failed."""
        if not code:
            return False
        try:
            code_str = str(code).strip()
            return bool(code_str and 1 <= len(code_str) <= 3 and code_str.isalnum() and 
                       code_str.lower() not in ('not available', 'not found', 'na', 'n/a', 'unknown', ''))
        except Exception:
            return False

def _get_patient_id_from_row(row):
    """Extract the best available patient identifier from a CSV row."""
    if not isinstance(row, dict):
        return ''
    candidate_keys = [
        'Patient ID #2', 'Patient ID', 'PATID', 'PatID', 'PatientID',
        'Patient Id', 'PatientID#2'
    ]
    for key in candidate_keys:
        value = row.get(key)
        if isinstance(value, str):
            value = value.strip()
        if value is not None:
            value_str = str(value).strip()
            if value_str:
                return value_str
    return ''

def _resolve_patient_name(row):
    """Resolve a friendly patient name with multiple fallbacks."""
    if not isinstance(row, dict):
        return 'Unknown Patient'
    name = row.get('Patient Name', '')
    if not name:
        name = row.get('Name', '')
    if not name:
        name = row.get('Member Name', '')
    if not name:
        name = row.get('Primary Insured Name', '')
    if not name:
        name = row.get('Subscriber Name', '')
    if not name:
        name = "{} {}".format(row.get('First Name', ''), row.get('Last Name', '')).strip()
    if not name:
        name = "{} {}".format(row.get('Patient First', ''), row.get('Patient Last', '')).strip()
    if not name:
        name = "{} {}".format(row.get('Subscriber First Name', ''), row.get('Subscriber Last Name', '')).strip()
    if not name:
        name = row.get('Patient', '')
    if not name:
        name = row.get('Member', '')
    if not name:
        name = row.get('Subscriber', '')
    if not name:
        first_name = row.get('First', '') or row.get('FirstName', '') or row.get('First Name', '')
        last_name = row.get('Last', '') or row.get('LastName', '') or row.get('Last Name', '')
        name = "{} {}".format(first_name or '', last_name or '').strip()
    return name.strip() or 'Unknown Patient'

def _build_cached_result(patient_info, cache_payload, dob, member_id, cache_reason=None):
    """Construct an enhanced-style record from cache data."""
    patient_name = _resolve_patient_name(patient_info)
    patient_id = _get_patient_id_from_row(patient_info) or "{}:{}".format(dob, member_id)
    insurance_code = ''
    remaining_amount = ''
    payer_id = ''
    plan_start_date = ''
    plan_end_date = ''
    if isinstance(cache_payload, dict):
        insurance_code = str(cache_payload.get('code', '')).strip()
        remaining_amount = str(cache_payload.get('remaining_amount', '')).strip()
        payer_id = str(cache_payload.get('payer_id', '')).strip()
        plan_start_date = str(cache_payload.get('plan_start_date', '')).strip()
        plan_end_date = str(cache_payload.get('plan_end_date', '')).strip()
    
    # Determine policy status based on plan_end_date
    policy_status = 'Active Policy'
    if plan_end_date:
        try:
            from datetime import datetime
            plan_end_dt = datetime.strptime(plan_end_date, '%Y-%m-%d')
            today = datetime.now()
            if plan_end_dt < today:
                policy_status = 'Past Policy'
        except (ValueError, TypeError):
            # If date parsing fails, default to Active Policy
            pass
    
    display_remaining = remaining_amount or '0.00'
    # Use cache_reason if provided, otherwise default to 'cache' for backward compatibility
    cache_label = cache_reason if cache_reason else 'cache'
    display_remaining = "{} ({})".format(display_remaining, cache_label)
    insurance_display = insurance_code or 'Cached'
    
    # Extract all_deductible_amounts from cache if available (for diagnostic columns)
    # Note: Older cache entries won't have this field, so it will be empty dict
    # Diagnostic columns will only appear for cache entries that include this data
    all_deductible_amounts = {}
    if isinstance(cache_payload, dict):
        all_deductible_amounts = cache_payload.get('all_deductible_amounts', {})
        # Ensure it's a dict (not None or other type)
        if not isinstance(all_deductible_amounts, dict):
            all_deductible_amounts = {}
    
    return {
        'patient_name': patient_name,
        'dob': dob,
        'member_id': member_id,
        'payer_id': payer_id,
        'policy_status': policy_status,
        'insurance_type': "{}".format(insurance_display),
        'remaining_amount': display_remaining,
        'data_source': 'Cache',
        'is_successful': True,
        'patient_id': patient_id,
        'plan_start_date': plan_start_date,
        'plan_end_date': plan_end_date,
        # Include all_deductible_amounts for diagnostic display (empty dict if not in cache)
        'all_deductible_amounts': all_deductible_amounts
    }

# Use latest core_utils configuration cache for better performance
_get_config, (_config_cache, _crosswalk_cache) = create_config_cache()

_RECENT_CACHE_MAX_AGE_HOURS = 24


def _is_recent_cache_payload(payload, max_age_hours=_RECENT_CACHE_MAX_AGE_HOURS):
    """Return True when cached_at exists and is within the freshness window."""
    try:
        if not isinstance(payload, dict):
            return False
        cached_at = payload.get('cached_at')
        if not cached_at:
            return False
        cached_dt = datetime.strptime(str(cached_at), '%Y-%m-%dT%H:%M:%SZ')
        return datetime.utcnow() - cached_dt < timedelta(hours=max_age_hours)
    except Exception:
        return False

def _is_stale_patient(service_date, max_age_days=30):
    """
    Check if a patient is stale based on service_date.
    Returns True if service_date is older than max_age_days from today.
    
    Args:
        service_date: Service date string in YYYY-MM-DD format or datetime object
        max_age_days: Maximum age in days (default 30)
    
    Returns:
        Boolean: True if patient is stale, False otherwise
    """
    try:
        if not service_date:
            return False
        
        # Parse service_date if it's a string
        if isinstance(service_date, str):
            service_dt = None
            for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y']:
                try:
                    service_dt = datetime.strptime(service_date.strip(), fmt)
                    break
                except ValueError:
                    continue
            if not service_dt:
                return False
        elif isinstance(service_date, datetime):
            service_dt = service_date
        else:
            return False
        
        # Check if service_date is older than max_age_days
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        return service_dt < cutoff_date
    except Exception:
        return False

# Load configuration using latest core_utils pattern
config, _ = _get_config()

# Error reporting imports for automated crash reporting
try:
    from MediCafe.error_reporter import capture_unhandled_traceback, submit_support_bundle_email, collect_support_bundle
except ImportError:
    capture_unhandled_traceback = None
    submit_support_bundle_email = None
    collect_support_bundle = None

# Initialize the API client using latest core_utils
client = get_api_core_client()
if client is None:
    print("Warning: API client not available via core_utils")
    # Fallback to direct instantiation
    try:
        if api_core:
            client = api_core.APIClient()
        else:
            raise ImportError("api_core not available")
    except ImportError as e:
        print("Error: Unable to create API client: {}".format(e))
        client = None

# Get provider_last_name and npi from configuration
provider_last_name = config['MediLink_Config'].get('default_billing_provider_last_name', 'Unknown')
npi = config['MediLink_Config'].get('default_billing_provider_npi', 'Unknown')

# Check if the provider_last_name is still 'Unknown'
if provider_last_name == 'Unknown':
    MediLink_ConfigLoader.log("Warning: provider_last_name was not found in the configuration.", level="WARNING")

# Define the list of payer_id's to iterate over
payer_ids = ['87726', '03432', '96385', '95467', '86050', '86047', '95378', '06111', '37602']  # United Healthcare ONLY.


# Get the latest CSV
CSV_FILE_PATH = config.get('CSV_FILE_PATH', "")

# Lean insurance type cache (persist alongside CSV)
try:
    from MediLink.insurance_type_cache import get_csv_dir_from_config, put_entry_from_enhanced_result, load_cache
except Exception:
    get_csv_dir_from_config = None
    put_entry_from_enhanced_result = None
    load_cache = None

try:
    CSV_DIR = get_csv_dir_from_config(config) if get_csv_dir_from_config else os.path.dirname(CSV_FILE_PATH)
except Exception:
    try:
        CSV_DIR = os.path.dirname(CSV_FILE_PATH)
    except Exception:
        CSV_DIR = ''
try:
    csv_data = MediBot_Preprocessor_lib.load_csv_data(CSV_FILE_PATH)
    print("Successfully loaded CSV data: {} records".format(len(csv_data)))
except Exception as e:
    print("Error loading CSV data: {}".format(e))
    print("CSV_FILE_PATH: {}".format(CSV_FILE_PATH))
    csv_data = []

# Only keep rows that have an exact match with a payer ID from the payer_ids list
if not csv_data:
    print("Error: No CSV data loaded. Please check the CSV file path and format.")
    sys.exit(1)

valid_rows = [row for row in csv_data if str(row.get('Ins1 Payer ID', '')).strip() in payer_ids]

if not valid_rows:
    print("Error: No valid rows found with supported payer IDs.")
    print("Supported payer IDs: {}".format(payer_ids))
    print("Available payer IDs in CSV: {}".format(set(str(row.get('Ins1 Payer ID', '')).strip() for row in csv_data if row.get('Ins1 Payer ID', ''))))
    sys.exit(1)

# DEBUG: Log available fields in the first row for diagnostic purposes (DEBUG level is suppressed by default)
if valid_rows:
    try:
        first_row = valid_rows[0]
        MediLink_ConfigLoader.log("DEBUG: Available fields in CSV data:", level="DEBUG")
        for field_name in sorted(first_row.keys()):
            MediLink_ConfigLoader.log("  - '{}': '{}'".format(field_name, first_row[field_name]), level="DEBUG")
        MediLink_ConfigLoader.log("DEBUG: End of available fields", level="DEBUG")
    except Exception:
        pass

# Extract important columns for summary with fallback
summary_valid_rows = [
    {
        'DOB': row.get('Patient DOB', row.get('DOB', '')),  # Try 'Patient DOB' first, then 'DOB'
        'Ins1 Member ID': row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip(),  # Try 'Primary Policy Number' first, then 'Ins1 Member ID'
        'Ins1 Payer ID': row.get('Ins1 Payer ID', '')
    }
    for row in valid_rows
]

# Display enhanced summary of valid rows using unified display philosophy
try:
    from MediLink.MediLink_Display_Utils import display_enhanced_deductible_table
except ImportError as e:
    print("Warning: Unable to import MediLink_Display_Utils: {}".format(e))
    # Create a fallback display function
    def display_enhanced_deductible_table(data, context="", title=""):
        print("Fallback display for {}: {} records".format(context, len(data)))
        for i, row in enumerate(data, 1):
            print("{:03d}: {} | {} | {} | {} | {} | {} | [{}]".format(
                i,
                row.get('Patient ID', ''),
                row.get('Patient Name', '')[:20],
                row.get('Patient DOB', ''),
                row.get('Primary Policy Number', '')[:12],
                row.get('Ins1 Payer ID', ''),
                row.get('Service Date', ''),
                row.get('status', 'READY')
            ))

# Patients will be derived from patient_groups below

# Build fast index for (dob, member_id) -> CSV row to avoid repeated scans
patient_row_index = {}
for row in valid_rows:
    idx_dob = _fallback_validate_and_format_date(row.get('Patient DOB', row.get('DOB', '')))
    idx_member_id = row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip()
    if idx_dob and idx_member_id:
        patient_row_index[(idx_dob, idx_member_id)] = row

# Group patients by (dob, member_id)
patient_groups = defaultdict(list)
for row in valid_rows:
    dob = _fallback_validate_and_format_date(row.get('Patient DOB', row.get('DOB', '')))
    member_id = row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip()
    # Try multiple possible service date field names (after header cleaning)
    # Surgery Date is treated as the primary source of date of service.
    service_date = row.get('Surgery Date', '')
    if not service_date:
        service_date = row.get('Service Date', '')
    if not service_date:
        service_date = row.get('Date of Service', '')
    if not service_date:
        service_date = row.get('DOS', '')
    if not service_date:
        service_date = row.get('Date', '')
    if dob and member_id:
        # Try to parse service date, but handle various formats
        service_date_sort = datetime.min
        if service_date:
            try:
                # Try common date formats
                for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%y', '%m/%d/%y']:
                    try:
                        service_date_sort = datetime.strptime(service_date, fmt)
                        break
                    except ValueError:
                        continue
            except:
                pass  # Keep datetime.min if parsing fails
        
        patient_groups[(dob, member_id)].append({
            'service_date_display': service_date,
            'service_date_sort': service_date_sort,
            'patient_id': row.get('Patient ID', '')
        })

# Update patients to unique
patients = list(patient_groups.keys())

# Use the enhanced table display for pre-API context
# Create display data from unique patients with their service dates
display_data = []
for (dob, member_id), service_records in patient_groups.items():
    # Find the original row data for this patient
    original_row = patient_row_index.get((dob, member_id))
    
    if original_row:
        # Use the first service record for display
        first_service = service_records[0] if service_records else {}
        service_date_display = first_service.get('service_date_display', '')
        service_date_sort = first_service.get('service_date_sort', datetime.min)
        
        # Check if patient is stale (30+ days after latest service_date)
        is_stale = False
        if service_date_sort and service_date_sort != datetime.min:
            is_stale = _is_stale_patient(service_date_sort, max_age_days=30)
        elif service_date_display:
            is_stale = _is_stale_patient(service_date_display, max_age_days=30)
        
        # Skip stale patients from display
        if is_stale:
            continue
        
        patient_name = _resolve_patient_name(original_row)
        display_row = {
            'Patient ID': original_row.get('Patient ID', ''),
            'Patient Name': patient_name,
            'Patient DOB': dob,
            'Primary Policy Number': member_id,
            'Ins1 Payer ID': original_row.get('Ins1 Payer ID', ''),
            'Service Date': service_date_display,
            'status': 'Ready'
        }
        display_data.append(display_row)

display_enhanced_deductible_table(display_data, context="pre_api")

# Cache write helper - delegates directly to cache module
# All extraction and validation logic is in insurance_type_cache.put_entry_from_enhanced_result()

def _get_recent_csv_files(csv_dir, max_files=4):
    """
    Scan csv_dir for CSV files and return the most recent ones.
    
    Args:
        csv_dir: Directory path to scan for CSV files
        max_files: Maximum number of files to return (default 4)
    
    Returns:
        List of tuples: (filepath, filename, mtime) sorted by modification time (most recent first)
    """
    if not csv_dir or not os.path.exists(csv_dir):
        return []
    
    csv_files = []
    try:
        for filename in os.listdir(csv_dir):
            # Case-insensitive check for .csv extension
            if filename.lower().endswith('.csv'):
                filepath = os.path.join(csv_dir, filename)
                if os.path.isfile(filepath):
                    try:
                        mtime = os.path.getmtime(filepath)
                        csv_files.append((filepath, filename, mtime))
                    except Exception:
                        # Skip files we can't get mtime for
                        continue
    except Exception:
        # Directory access error or other issue
        return []
    
    # Sort by modification time (most recent first) and return up to max_files
    csv_files.sort(key=lambda x: x[2], reverse=True)
    return csv_files[:max_files]

def select_csv_file(csv_dir):
    """
    Display the 4 most recent CSV files and prompt user to select one.
    
    Args:
        csv_dir: Directory path to scan for CSV files
    
    Returns:
        Selected file path (str) or None if cancelled
    """
    if not csv_dir:
        print("\nCSV directory path is not configured.")
        return None
    
    if not os.path.exists(csv_dir):
        print("\nCSV directory does not exist: {}".format(csv_dir))
        return None
    
    recent_files = _get_recent_csv_files(csv_dir, max_files=4)
    
    if not recent_files:
        print("\nNo CSV files found in directory: {}".format(csv_dir))
        return None
    
    print("\n" + "=" * 80)
    print("SELECT CSV FILE")
    print("=" * 80)
    print("Recent CSV files in directory: {}".format(csv_dir))
    print()
    
    # Display numbered list showing only filenames
    for i, (filepath, filename, mtime) in enumerate(recent_files, 1):
        print("{}. {}".format(i, filename))
    
    print("{}. Cancel".format(len(recent_files) + 1))
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-{}): ".format(len(recent_files) + 1)).strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(recent_files):
                selected_filepath = recent_files[choice_num - 1][0]
                print("Selected: {}".format(recent_files[choice_num - 1][1]))
                return selected_filepath
            elif choice_num == len(recent_files) + 1:
                print("Selection cancelled.")
                return None
            else:
                print("Invalid choice. Please enter a number between 1 and {}.".format(len(recent_files) + 1))
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nSelection cancelled.")
            return None

def reload_csv_data(csv_file_path):
    """
    Reload CSV data and rebuild all dependent data structures.
    
    Args:
        csv_file_path: Path to the CSV file to load
    
    Returns:
        Tuple: (success: bool, error_message: str or None)
    """
    global csv_data, valid_rows, summary_valid_rows, patient_row_index, patient_groups, patients, display_data, CSV_FILE_PATH, CSV_DIR
    
    try:
        # Reload CSV data
        csv_data = MediBot_Preprocessor_lib.load_csv_data(csv_file_path)
        print("Successfully loaded CSV data: {} records".format(len(csv_data)))
        
        # Validate CSV data loaded before updating globals
        if not csv_data:
            return False, "No CSV data loaded. Please check the CSV file path and format."
        
        # Rebuild valid_rows (filtered by payer_ids)
        valid_rows = [row for row in csv_data if str(row.get('Ins1 Payer ID', '')).strip() in payer_ids]
        
        if not valid_rows:
            return False, "No valid rows found with supported payer IDs. Supported payer IDs: {}".format(payer_ids)
        
        # Update global CSV_FILE_PATH and CSV_DIR only after successful validation
        CSV_FILE_PATH = csv_file_path
        try:
            CSV_DIR = get_csv_dir_from_config(config) if get_csv_dir_from_config else os.path.dirname(CSV_FILE_PATH)
        except Exception:
            try:
                CSV_DIR = os.path.dirname(CSV_FILE_PATH)
            except Exception:
                CSV_DIR = ''
        
        # Rebuild summary_valid_rows
        summary_valid_rows = [
            {
                'DOB': row.get('Patient DOB', row.get('DOB', '')),  # Try 'Patient DOB' first, then 'DOB'
                'Ins1 Member ID': row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip(),  # Try 'Primary Policy Number' first, then 'Ins1 Member ID'
                'Ins1 Payer ID': row.get('Ins1 Payer ID', '')
            }
            for row in valid_rows
        ]
        
        # Rebuild patient_row_index
        patient_row_index = {}
        for row in valid_rows:
            idx_dob = _fallback_validate_and_format_date(row.get('Patient DOB', row.get('DOB', '')))
            idx_member_id = row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip()
            if idx_dob and idx_member_id:
                patient_row_index[(idx_dob, idx_member_id)] = row
        
        # Rebuild patient_groups
        patient_groups = defaultdict(list)
        for row in valid_rows:
            dob = _fallback_validate_and_format_date(row.get('Patient DOB', row.get('DOB', '')))
            member_id = row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip()
            # Try multiple possible service date field names (after header cleaning)
            # Surgery Date is treated as the primary source of date of service.
            service_date = row.get('Surgery Date', '')
            if not service_date:
                service_date = row.get('Service Date', '')
            if not service_date:
                service_date = row.get('Date of Service', '')
            if not service_date:
                service_date = row.get('DOS', '')
            if not service_date:
                service_date = row.get('Date', '')
            if dob and member_id:
                # Try to parse service date, but handle various formats
                service_date_sort = datetime.min
                if service_date:
                    try:
                        # Try common date formats
                        for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%y', '%m/%d/%y']:
                            try:
                                service_date_sort = datetime.strptime(service_date, fmt)
                                break
                            except ValueError:
                                continue
                    except:
                        pass  # Keep datetime.min if parsing fails
                
                patient_groups[(dob, member_id)].append({
                    'service_date_display': service_date,
                    'service_date_sort': service_date_sort,
                    'patient_id': row.get('Patient ID', '')
                })
        
        # Rebuild patients list
        patients = list(patient_groups.keys())
        
        # Rebuild display_data
        display_data = []
        for (dob, member_id), service_records in patient_groups.items():
            # Find the original row data for this patient
            original_row = patient_row_index.get((dob, member_id))
            
            if original_row:
                # Use the first service record for display
                first_service = service_records[0] if service_records else {}
                service_date_display = first_service.get('service_date_display', '')
                service_date_sort = first_service.get('service_date_sort', datetime.min)
                
                # Check if patient is stale (30+ days after latest service_date)
                is_stale = False
                if service_date_sort and service_date_sort != datetime.min:
                    is_stale = _is_stale_patient(service_date_sort, max_age_days=30)
                elif service_date_display:
                    is_stale = _is_stale_patient(service_date_display, max_age_days=30)
                
                # Skip stale patients from display
                if is_stale:
                    continue
                
                patient_name = _resolve_patient_name(original_row)
                display_row = {
                    'Patient ID': original_row.get('Patient ID', ''),
                    'Patient Name': patient_name,
                    'Patient DOB': dob,
                    'Primary Policy Number': member_id,
                    'Ins1 Payer ID': original_row.get('Ins1 Payer ID', ''),
                    'Service Date': service_date_display,
                    'status': 'Ready'
                }
                display_data.append(display_row)
        
        # Display updated summary (non-critical - don't fail reload if display fails)
        try:
            display_enhanced_deductible_table(display_data, context="pre_api")
        except Exception as display_error:
            # Log display error but don't fail the reload
            MediLink_ConfigLoader.log("Warning: Failed to display CSV summary: {}".format(display_error), level="WARNING")
        
        return True, None
        
    except Exception as e:
        error_msg = "Error loading CSV data: {}".format(e)
        print(error_msg)
        return False, error_msg

# Function to handle manual patient deductible lookup
def manual_deductible_lookup():
    print("\n--- Manual Patient Deductible Lookup ---")
    print("Available Payer IDs: {}".format(", ".join(payer_ids)))
    print("Enter 'quit' at any time to return to main menu.\n")
    
    while True:
        member_id = input("Enter the Member ID of the subscriber (or 'quit' to exit): ").strip()
        if member_id.lower() == 'quit':
            print("Returning to main menu.\n")
            break
        if not member_id:
            print("No Member ID entered. Please try again.\n")
            continue

        dob_input = input("Enter the Date of Birth (YYYY-MM-DD): ").strip()
        if dob_input.lower() == 'quit':
            print("Returning to main menu.\n")
            break
            
        formatted_dob = _fallback_validate_and_format_date(dob_input)
        if not formatted_dob:
            print("Invalid DOB format. Please enter in YYYY-MM-DD format.\n")
            continue

        print("\nProcessing manual lookup for Member ID: {}, DOB: {}".format(member_id, formatted_dob))
        print("Checking {} payer IDs...".format(len(payer_ids)))

        # Fetch eligibility data
        found_data = False
        printed_messages = set()
        for i, payer_id in enumerate(payer_ids, 1):
            print("Checking Payer ID {} ({}/{}): {}".format(payer_id, i, len(payer_ids), payer_id))
            
            # Determine API mode based on global flags
            api_mode = _determine_api_mode()
            # Get service_date from CSV using utility function if available
            csv_row = patient_row_index.get((formatted_dob, member_id))
            service_date_for_api = None
            if csv_row and _extract_service_date_from_csv_row:
                _, service_date_dt = _extract_service_date_from_csv_row(csv_row)
                if service_date_dt != datetime.min:
                    service_date_for_api = service_date_dt
            # Best-effort group number extraction from CSV (optional discriminator)
            group_number_for_api = None
            if csv_row and extract_group_number_from_csv_row:
                try:
                    group_number_for_api = extract_group_number_from_csv_row(csv_row)
                except Exception:
                    group_number_for_api = None
            eligibility_data = get_eligibility_info(
                client, payer_id, provider_last_name, formatted_dob, member_id, npi,
                api_mode=api_mode, is_manual_lookup=True, printed_messages=printed_messages,
                service_date=service_date_for_api, group_number=group_number_for_api
            )
            if eligibility_data:
                found_data = True
                
                # Convert to enhanced format and display
                # Check if we already have processed data (from merge_responses in validation mode)
                if isinstance(eligibility_data, dict) and 'patient_name' in eligibility_data and 'data_source' in eligibility_data:
                    # Already processed data from merge_responses
                    enhanced_result = eligibility_data
                elif convert_eligibility_to_enhanced_format is not None:
                    # Silent insurance type mapping collection (for error reporting)
                    # Try to collect even if already processed (may have rawGraphQLResponse preserved)
                    _collect_and_merge_insurance_type_mapping(eligibility_data)
                    
                    # Attempt CSV backfill context for manual route
                    csv_row = patient_row_index.get((formatted_dob, member_id))
                    derived_patient_id = ""
                    derived_service_date = ""
                    if csv_row:
                        try:
                            derived_patient_id = str(csv_row.get('Patient ID #2', csv_row.get('Patient ID', '')))
                            derived_service_date = str(csv_row.get('Service Date', ''))
                        except Exception:
                            derived_patient_id = ""
                            derived_service_date = ""
                    # Raw API data needs conversion with patient info
                    enhanced_result = convert_eligibility_to_enhanced_format(
                        eligibility_data, formatted_dob, member_id, derived_patient_id, derived_service_date
                    )
                else:
                    # Fallback if utility function not available
                    enhanced_result = None
                if enhanced_result:
                    try:
                        # Backfill with CSV row data when available
                        csv_row = patient_row_index.get((formatted_dob, member_id))
                        enhanced_result = backfill_enhanced_result(enhanced_result, csv_row)
                    except Exception:
                        pass
                    # Persist insurance type code to cache
                    csv_row = patient_row_index.get((formatted_dob, member_id))
                    if put_entry_from_enhanced_result:
                        put_entry_from_enhanced_result(CSV_DIR, enhanced_result, formatted_dob, member_id, payer_id,
                                                       csv_row=csv_row, service_date_for_api=service_date_for_api, context="manual")
                    # Ensure patient_id present; warn/log and set surrogate if missing
                    try:
                        pid = str(enhanced_result.get('patient_id', '')).strip()
                        if not pid:
                            surrogate = "{}:{}".format(formatted_dob, member_id)
                            enhanced_result['patient_id'] = surrogate
                            print("Warning: Missing Patient ID; using surrogate key {}".format(surrogate))
                            MediLink_ConfigLoader.log(
                                "Manual lookup: Missing Patient ID; using surrogate key {}".format(surrogate),
                                level="WARNING"
                            )
                    except Exception:
                        pass
                    # Ensure patient_name not blank
                    try:
                        if not str(enhanced_result.get('patient_name', '')).strip():
                            enhanced_result['patient_name'] = 'Unknown Patient'
                    except Exception:
                        enhanced_result['patient_name'] = 'Unknown Patient'
                    print("\n" + "=" * 60)
                    display_enhanced_deductible_table([enhanced_result], context="post_api", 
                                                    title="Manual Lookup Result")
                    print("=" * 60)
                    
                    # Enhanced manual lookup result display
                    print("\n" + "=" * 60)
                    print("MANUAL LOOKUP RESULT")
                    print("=" * 60)
                    print("Patient Name: {}".format(enhanced_result['patient_name']))
                    print("Member ID: {}".format(enhanced_result['member_id']))
                    print("Date of Birth: {}".format(enhanced_result['dob']))
                    print("Payer ID: {}".format(enhanced_result['payer_id']))
                    print("Insurance Type: {}".format(enhanced_result['insurance_type']))
                    print("Policy Status: {}".format(enhanced_result['policy_status']))
                    print("Remaining Deductible: {}".format(enhanced_result['remaining_amount']))
                    print("=" * 60)
                else:
                    # Fallback display when enhanced_result is None
                    print("\n" + "=" * 60)
                    print("MANUAL LOOKUP RESULT")
                    print("=" * 60)
                    print("Patient Name: Not Available")
                    print("Member ID: {}".format(member_id))
                    print("Date of Birth: {}".format(formatted_dob))
                    print("Payer ID: {}".format(payer_id))
                    print("Insurance Type: Not Available")
                    print("Policy Status: Not Available")
                    print("Remaining Deductible: Not Available")
                    print("Note: Data conversion failed - raw API response available")
                    print("=" * 60)
                
                # Generate unique output file for manual request
                output_file_name = "eligibility_report_manual_{}_{}.txt".format(member_id, formatted_dob)
                output_file_path = os.path.join(os.getenv('TEMP'), output_file_name)
                with open(output_file_path, 'w') as output_file:
                    table_header = "{:<20} | {:<10} | {:<8} | {:<5} | {:<14} | {:<14}".format(
                        "Patient Name", "DOB", "IT Code", "PayID", "Policy Status", "Remaining Amt")
                    output_file.write(table_header + "\n")
                    output_file.write("-" * len(table_header) + "\n")
                    # Write directly from enhanced_result to ensure CSV backfill/defaults are preserved
                    if enhanced_result:
                        table_row = "{:<20} | {:<10} | {:<8} | {:<5} | {:<14} | {:<14}".format(
                            enhanced_result['patient_name'][:20],
                            enhanced_result['dob'],
                            enhanced_result['insurance_type'][:8],
                            enhanced_result['payer_id'][:5],
                            enhanced_result['policy_status'][:14],
                            enhanced_result['remaining_amount'][:14])
                        output_file.write(table_row + "\n")

                        # Persist per-row error diagnostics in a user-friendly way
                        try:
                            row_reason = _compute_error_reason(enhanced_result)
                            row_messages = enhanced_result.get('error_messages', []) or []
                            if row_reason or row_messages:
                                output_file.write("  >> Errors:" + "\n")
                                if row_reason:
                                    output_file.write("  >> - {}\n".format(row_reason))
                                for msg in row_messages:
                                    # Avoid duplicating the reason message if identical
                                    if not row_reason or msg.strip() != row_reason.strip():
                                        output_file.write("  >> - {}\n".format(str(msg)))
                        except Exception:
                            pass
                    else:
                        display_eligibility_info(eligibility_data, formatted_dob, member_id, output_file)
                
                # Ask if user wants to open the report
                open_report = input("\nEligibility data found! Open the report? (Y/N): ").strip().lower()
                if open_report in ['y', 'yes']:
                    os.startfile(output_file_path)
                print("Manual eligibility report generated: {}\n".format(output_file_path))
                break  # Assuming one payer ID per manual lookup
            else:
                print("No eligibility data found for Payer ID: {}".format(payer_id))
        
        if not found_data:
            print("\nNo eligibility data found for any Payer ID.")
        
        # Ask if the user wants to perform another manual lookup
        continue_choice = input("\nDo you want to perform another manual lookup? (Y/N): ").strip().lower()
        if continue_choice in ['n', 'no']:
            break


# Helper function to set mode flags
def _set_mode_flags(validation=False, legacy=False, payer_probe=False):
    """Set global mode flags. Only one should be True at a time."""
    global API_VALIDATION_MODE, LEGACY_MODE, DEBUG_MODE_PAYER_PROBE
    API_VALIDATION_MODE = validation
    LEGACY_MODE = legacy
    DEBUG_MODE_PAYER_PROBE = payer_probe

# Helper function to extract service date for API calls
def _get_service_date_for_api(dob, member_id, patient_groups, patient_row_index):
    """Extract service_date from patient_groups or CSV row for API calls.
    
    Returns:
        datetime object or None if not found
    """
    service_date_for_api = None
    service_records = patient_groups.get((dob, member_id), [])
    if service_records and len(service_records) > 0:
        service_date_sort = service_records[0].get('service_date_sort')
        if service_date_sort and service_date_sort != datetime.min:
            # Use already-parsed datetime from patient_groups
            service_date_for_api = service_date_sort
    # Fallback to extracting from CSV row if not found in patient_groups
    if not service_date_for_api and _extract_service_date_from_csv_row:
        patient_info = patient_row_index.get((dob, member_id))
        if patient_info:
            _, service_date_dt = _extract_service_date_from_csv_row(patient_info)
            if service_date_dt != datetime.min:
                service_date_for_api = service_date_dt
    return service_date_for_api

# Helper function to determine API mode from global flags
def _determine_api_mode():
    """Determine API mode based on global mode flags."""
    if API_VALIDATION_MODE:
        return 'validation'
    elif LEGACY_MODE:
        return 'legacy'
    else:
        return 'optumai_only'  # Default (when all flags are False)

# Function to get eligibility information
def get_eligibility_info(client, payer_id, provider_last_name, date_of_birth, member_id, npi,
                         api_mode='optumai_only', is_manual_lookup=False, printed_messages=None,
                         service_date=None, group_number=None):
    """
    Get eligibility information for a patient.
    
    Args:
        api_mode: API call mode - 'optumai_only' (default), 'validation', or 'legacy'
        service_date: Can be a datetime object (preferred) or a string/CSV row dict.
                     If datetime, formats directly to YYYY-MM-DD.
                     If string/CSV row, uses _extract_service_date_from_csv_row utility.
    """
    if printed_messages is None:
        printed_messages = set()

    try:
        # Convert service_date to YYYY-MM-DD format for API calls
        service_start = None
        service_end = None
        if service_date:
            try:
                # If it's already a datetime object, format it directly
                if isinstance(service_date, datetime):
                    if service_date != datetime.min:
                        service_start = service_date.strftime('%Y-%m-%d')
                        service_end = service_start  # Single day surgeries
                # If it's a dict (CSV row), use the utility function
                elif isinstance(service_date, dict) and _extract_service_date_from_csv_row:
                    _, service_date_dt = _extract_service_date_from_csv_row(service_date)
                    if service_date_dt != datetime.min:
                        service_start = service_date_dt.strftime('%Y-%m-%d')
                        service_end = service_start
                # If it's a string, try to parse using utility (if available) or fallback
                elif isinstance(service_date, str) and service_date.strip():
                    # Try utility function first if we have a CSV row context
                    # Otherwise, parse as string
                    service_date_str = service_date.strip()
                    for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y']:
                        try:
                            parsed_date = datetime.strptime(service_date_str, fmt)
                            service_start = parsed_date.strftime('%Y-%m-%d')
                            service_end = service_start
                            break
                        except ValueError:
                            continue
            except Exception as e:
                MediLink_ConfigLoader.log("Failed to process service_date '{}': {}".format(service_date, e), level="WARNING")
        
        # Log the parameters being sent to the function
        MediLink_ConfigLoader.log("Calling eligibility check with parameters:", level="DEBUG")
        MediLink_ConfigLoader.log("payer_id: {}".format(payer_id), level="DEBUG")
        MediLink_ConfigLoader.log("provider_last_name: {}".format(provider_last_name), level="DEBUG")
        MediLink_ConfigLoader.log("date_of_birth: {}".format(date_of_birth), level="DEBUG")
        MediLink_ConfigLoader.log("member_id: {}".format(member_id), level="DEBUG")
        MediLink_ConfigLoader.log("npi: {}".format(npi), level="DEBUG")
        if service_start:
            MediLink_ConfigLoader.log("service_start: {}".format(service_start), level="DEBUG")
            MediLink_ConfigLoader.log("service_end: {}".format(service_end), level="DEBUG")

        # Route to appropriate API mode
        if api_mode == 'validation':
            # API Validation Mode: Call both APIs and run validation
            MediLink_ConfigLoader.log("Running in API VALIDATION MODE - calling both APIs", level="INFO")
            # Always initialize row-level error messages for diagnostics
            error_messages_for_row = []
            # Track Super Connector connection failure (for user-facing diagnostics)
            sc_failure_info = None
            # Enable verbose diagnostics in API validation mode without config changes
            diagnostics_verbose = True
            sc_preflight_failed = False
            # NOTE: No config flag mutation needed; OPTUMAI call now never auto-falls back
            
            # Get legacy response
            MediLink_ConfigLoader.log("Getting legacy get_eligibility_v3 API response", level="INFO")

            legacy_eligibility = None
            if client and hasattr(client, 'get_access_token'):
                try:
                    # Try to get access token for UHCAPI endpoint
                    access_token = client.get_access_token('UHCAPI')
                    if access_token:
                        legacy_eligibility = api_core.get_eligibility_v3(
                            client, payer_id, provider_last_name, 'MemberIDDateOfBirth', date_of_birth, member_id, npi,
                            service_start=service_start, service_end=service_end
                        )
                    else:
                        MediLink_ConfigLoader.log("No access token available for Legacy API (UHCAPI endpoint). Check configuration.", level="WARNING")
                except Exception as e:
                    MediLink_ConfigLoader.log("Failed to get access token for Legacy API: {}".format(e), level="ERROR")
            else:
                MediLink_ConfigLoader.log("API client does not support token authentication for Legacy API.", level="WARNING")
            
            # Get OPTUMAI eligibility response for comparison (formerly Super Connector)
            MediLink_ConfigLoader.log("Getting OPTUMAI eligibility API response", level="INFO")
            super_connector_eligibility = None
            try:
                if not sc_preflight_failed:
                    super_connector_eligibility = api_core.get_eligibility_super_connector(
                        client, payer_id, provider_last_name, 'MemberIDDateOfBirth', date_of_birth, member_id, npi,
                        service_start=service_start, service_end=service_end, group_number=group_number
                    )
                else:
                    super_connector_eligibility = None
            except Exception as e:
                MediLink_ConfigLoader.log("OPTUMAI eligibility API failed: {}".format(e), level="ERROR")
                # Best-effort triage classification for clearer downstream messaging
                try:
                    # Use centralized classifier when available
                    from MediCafe.deductible_utils import classify_api_failure
                    code, message = classify_api_failure(e, 'OPTUMAI eligibility API')
                    # Sticky preflight failure for subsequent patients in this run
                    if code in ['TIMEOUT', 'CONN_ERR', 'AUTH_FAIL', 'MISCONFIG']:
                        sc_preflight_failed = True
                except Exception:
                    try:
                        failure_reason = "OPTUMAI eligibility API connection failed"
                        detail = str(e)
                        detail_lower = detail.lower()
                        
                        # Categorize errors: token expiration, subscription/auth, network, configuration
                        if requests and hasattr(requests, 'exceptions') and isinstance(e, requests.exceptions.Timeout):
                            failure_reason = "OPTUMAI eligibility API timeout (network error)"
                        elif requests and hasattr(requests, 'exceptions') and isinstance(e, requests.exceptions.ConnectionError):
                            failure_reason = "OPTUMAI eligibility API connection error (network error)"
                        elif "Invalid payer_id" in detail:
                            failure_reason = "OPTUMAI eligibility API rejected payer_id (configuration error)"
                        elif ("No access token" in detail) or ("token" in detail_lower and "expired" in detail_lower):
                            failure_reason = "OPTUMAI eligibility API token expiration (token error - will retry with refresh)"
                        elif ("invalid_access_token" in detail_lower) or ("401" in detail) or ("unauthorized" in detail_lower):
                            failure_reason = "OPTUMAI eligibility API authentication failed (subscription/auth error - verify client credentials and subscription access)"
                        elif ("token" in detail_lower and "authentication" in detail_lower):
                            failure_reason = "OPTUMAI eligibility API authentication failed (subscription/auth error - verify client credentials and subscription access)"
                        elif ("Eligibility endpoint not configured" in detail) or ("endpoint" in detail_lower and "configured" in detail_lower):
                            failure_reason = "OPTUMAI eligibility API endpoint misconfigured (configuration error)"
                        elif ("403" in detail) or ("forbidden" in detail_lower) or ("permission" in detail_lower):
                            failure_reason = "OPTUMAI eligibility API authorization failed (subscription/auth error - verify subscription permissions)"
                        
                        message = "{}: {}".format(failure_reason, detail)
                    except Exception:
                        message = "OPTUMAI eligibility API failed: {}".format(str(e))
                sc_failure_info = {"message": message}
                try:
                    error_messages_for_row.append(message)
                except Exception:
                    pass
            
            # Run validation if we have at least one response
            # Generate validation report even if one API fails - this helps with debugging
            validation_file_path = os.path.join(os.getenv('TEMP'), 'validation_report_{}_{}.txt'.format(member_id, date_of_birth))
            try:
                if legacy_eligibility and super_connector_eligibility:
                    # Both APIs returned data - run full comparison
                    validation_report = MediLink_Deductible_Validator.run_validation_comparison(
                        legacy_eligibility, super_connector_eligibility, validation_file_path
                    )
                    print("\nValidation report generated (both APIs): {}".format(validation_file_path))
                elif legacy_eligibility:
                    # Only legacy API returned data
                    validation_report = MediLink_Deductible_Validator.run_validation_comparison(
                        legacy_eligibility, None, validation_file_path
                    )
                    print("\nValidation report generated (legacy only): {}".format(validation_file_path))
                elif super_connector_eligibility:
                    # Only OPTUMAI eligibility API returned data
                    validation_report = MediLink_Deductible_Validator.run_validation_comparison(
                        None, super_connector_eligibility, validation_file_path
                    )
                    print("\nValidation report generated (OPTUMAI only): {}".format(validation_file_path))
                else:
                    # Neither API returned data
                    print("\nNo validation report generated - both APIs failed")
                    validation_file_path = None
                
                # Log any OPTUMAI eligibility API errors if we have that data
                if super_connector_eligibility and "rawGraphQLResponse" in super_connector_eligibility:
                    raw_response = super_connector_eligibility.get('rawGraphQLResponse', {})
                    errors = raw_response.get('errors', [])
                    if errors:
                        error_msg = "OPTUMAI eligibility API returned {} error(s):".format(len(errors))
                        if error_msg not in printed_messages:
                            print(error_msg)
                            printed_messages.add(error_msg)
                        for i, error in enumerate(errors):
                            error_code = error.get('code', 'UNKNOWN')
                            error_desc = error.get('description', 'No description')
                            detail_msg = "  Error {}: {} - {}".format(i+1, error_code, error_desc)
                            if detail_msg not in printed_messages:
                                print(detail_msg)
                                printed_messages.add(detail_msg)
                            # Accumulate per-row messages for persistence in reports
                            try:
                                error_messages_for_row.append("{} - {}".format(error_code, error_desc))
                            except Exception:
                                pass
                            
                            # Check for data in error extensions (some APIs return data here)
                            extensions = error.get('extensions', {})
                            if extensions and 'details' in extensions:
                                details = extensions.get('details', [])
                                if details:
                                    print("    Found {} detail records in error extensions".format(len(details)))
                                    # Log first detail record for debugging
                                    if details:
                                        first_detail = details[0]
                                        print("    First detail: {}".format(first_detail))
                                        # Persist a brief extension note without dumping raw objects
                                        try:
                                            error_messages_for_row.append("Extensions include {} detail record(s)".format(len(details)))
                                        except Exception:
                                            pass

                        # Provide concise terminal hints for 401/403 outcomes (XP-safe)
                        def _emit_hint(status_code):
                            try:
                                if status_code == '401':
                                    h = "Hint: Authentication failed. Verify API credentials/token and endpoint configuration."
                                    if h not in printed_messages:
                                        print(h)
                                        printed_messages.add(h)
                                elif status_code == '403':
                                    h = "Hint: Access denied. Verify provider TIN/NPI and account permissions/roles."
                                    if h not in printed_messages:
                                        print(h)
                                        printed_messages.add(h)
                            except Exception:
                                pass

                        try:
                            _emit_hint(super_connector_eligibility.get('statuscode'))
                        except Exception:
                            pass
                
                # Check status code
                if super_connector_eligibility:
                    status_code = super_connector_eligibility.get('statuscode')
                    from MediCafe.deductible_utils import is_ok_200
                    if status_code is not None and not is_ok_200(status_code):
                        print("OPTUMAI eligibility API status code: {} (non-200 indicates errors)".format(status_code))
                        # Record status code for the row diagnostics
                        error_messages_for_row.append("Status code {} from OPTUMAI eligibility".format(status_code))
                # If Super Connector failed entirely, append a triage note to the validation report (if created)
                try:
                    if sc_failure_info and validation_file_path and os.path.exists(validation_file_path):
                        with open(validation_file_path, 'a') as vf:
                            vf.write("\n" + "-" * 80 + "\n")
                            vf.write("OPTUMAI ELIGIBILITY CONNECTION FAILURE NOTE\n")
                            vf.write("-" * 80 + "\n")
                            vf.write(sc_failure_info['message'] + "\n")
                            vf.write("Recommendation: Verify network connectivity, credentials, payer ID validity, and endpoint configuration.\n")
                except Exception:
                    pass
                
                # Open validation report in Notepad (only for manual lookups, not batch processing)
                if validation_file_path and os.path.exists(validation_file_path):
                    # Only open in manual mode - batch processing will handle this separately
                    if is_manual_lookup:  # Check if we're in manual lookup mode
                        os.startfile(validation_file_path)
                elif validation_file_path:
                    print("\nValidation report file was not created: {}".format(validation_file_path))
            except Exception as e:
                print("\nError generating validation report: {}".format(str(e)))
            
            # After validation, merge responses
            try:
                if merge_responses is not None:
                    merged_data = merge_responses(super_connector_eligibility, legacy_eligibility, date_of_birth, member_id, service_date=service_start)
                else:
                    MediLink_ConfigLoader.log("merge_responses utility not available; returning raw API response", level="WARNING")
                    merged_data = super_connector_eligibility or legacy_eligibility or {}
                
                # Silent insurance type mapping collection (for error reporting)
                _collect_and_merge_insurance_type_mapping(merged_data, super_connector_eligibility, legacy_eligibility)
                
                # Attach accumulated row-level messages for downstream display/persistence
                try:
                    if isinstance(merged_data, dict) and error_messages_for_row:
                        merged_data['error_messages'] = error_messages_for_row
                except Exception:
                    pass
                # Surface OPTUMAI eligibility failure prominently in user-facing diagnostics
                try:
                    if sc_failure_info and isinstance(merged_data, dict):
                        merged_data['super_connector_failed'] = True
                        # Prefer explaining the connection failure over generic name/amount messages
                        if (not merged_data.get('error_reason')) or (merged_data.get('data_source') in ['None', 'Error']) or (not merged_data.get('is_successful', False)):
                            merged_data['error_reason'] = sc_failure_info['message']
                        # Ensure the failure message is included in error_messages
                        if 'error_messages' not in merged_data or merged_data['error_messages'] is None:
                            merged_data['error_messages'] = []
                        if sc_failure_info['message'] not in merged_data['error_messages']:
                            merged_data['error_messages'].append(sc_failure_info['message'])
                        # Attach diagnostics envelope (minimal) without breaking existing schema
                        try:
                            if diagnostics_verbose:
                                if 'diagnostics' not in merged_data or merged_data['diagnostics'] is None:
                                    merged_data['diagnostics'] = []
                                if sc_failure_info['message'] not in merged_data['diagnostics']:
                                    merged_data['diagnostics'].append(sc_failure_info['message'])
                        except Exception:
                            pass
                except Exception:
                    pass
                return merged_data
            except Exception as e:
                MediLink_ConfigLoader.log("Error in merge_responses: {}".format(e), level="ERROR")
                # Return a safe fallback result
                return {
                    'patient_name': 'Unknown Patient',
                    'dob': date_of_birth,
                    'member_id': member_id,
                    'insurance_type': 'Not Available',
                    'policy_status': 'Not Available',
                    'remaining_amount': 'Not Found',
                    'data_source': 'Error',
                    'is_successful': False
                }
        
        elif api_mode == 'legacy':
            # Legacy mode: Only call legacy API
            MediLink_ConfigLoader.log("Running in LEGACY MODE - calling legacy API only", level="INFO")
            
            # Only get legacy response with proper token handling
            if client and hasattr(client, 'get_access_token'):
                try:
                    access_token = client.get_access_token('UHCAPI')
                    if access_token:
                        eligibility = api_core.get_eligibility_v3(
                            client, payer_id, provider_last_name, 'MemberIDDateOfBirth', date_of_birth, member_id, npi,
                            service_start=service_start, service_end=service_end
                        )
                    else:
                        MediLink_ConfigLoader.log("No access token available for Legacy API in Legacy mode.", level="WARNING")
                        return None
                except Exception as e:
                    MediLink_ConfigLoader.log("Failed to get access token for Legacy API in Legacy mode: {}".format(e), level="ERROR")
                    return None
            else:
                MediLink_ConfigLoader.log("API client does not support token authentication for Legacy API in Legacy mode.", level="WARNING")
                return None
            
            # Log the response
            if 'eligibility' in locals():
                MediLink_ConfigLoader.log("Eligibility response: {}".format(json.dumps(eligibility, indent=4)), level="DEBUG")
                return eligibility
            else:
                return None
        
        else:
            # OptumAI Only Mode (default): Call only OptumAI endpoint
            MediLink_ConfigLoader.log("Running in OPTUMAI ONLY MODE - calling OptumAI endpoint", level="DEBUG")
            
            # Validate client and api_core availability
            if not client:
                MediLink_ConfigLoader.log("API client not available for OptumAI endpoint.", level="WARNING")
                return {
                    'patient_name': 'Unknown Patient',
                    'dob': date_of_birth,
                    'member_id': member_id,
                    'insurance_type': 'Not Available',
                    'policy_status': 'Not Available',
                    'remaining_amount': 'Not Found',
                    'payer_id': payer_id,
                    'data_source': 'Error',
                    'is_successful': False,
                    'error_reason': 'API client not available'
                }
            
            if not api_core:
                MediLink_ConfigLoader.log("api_core module not available for OptumAI endpoint.", level="WARNING")
                return {
                    'patient_name': 'Unknown Patient',
                    'dob': date_of_birth,
                    'member_id': member_id,
                    'insurance_type': 'Not Available',
                    'policy_status': 'Not Available',
                    'remaining_amount': 'Not Found',
                    'payer_id': payer_id,
                    'data_source': 'Error',
                    'is_successful': False,
                    'error_reason': 'api_core module not available'
                }
            
            optumai_eligibility = None
            try:
                optumai_eligibility = api_core.get_eligibility_super_connector(
                    client, payer_id, provider_last_name, 'MemberIDDateOfBirth', date_of_birth, member_id, npi,
                    service_start=service_start, service_end=service_end, group_number=group_number
                )
            except Exception as e:
                MediLink_ConfigLoader.log("OPTUMAI eligibility API failed: {}".format(e), level="ERROR")
                # Return error result
                return {
                    'patient_name': 'Unknown Patient',
                    'dob': date_of_birth,
                    'member_id': member_id,
                    'insurance_type': 'Not Available',
                    'policy_status': 'Not Available',
                    'remaining_amount': 'Not Found',
                    'payer_id': payer_id,
                    'data_source': 'Error',
                    'is_successful': False,
                    'error_reason': 'OPTUMAI eligibility API failed: {}'.format(str(e))
                }
            
            # Handle None response (API call succeeded but returned None)
            if optumai_eligibility is None:
                MediLink_ConfigLoader.log("OPTUMAI eligibility API returned None", level="WARNING")
                return {
                    'patient_name': 'Unknown Patient',
                    'dob': date_of_birth,
                    'member_id': member_id,
                    'insurance_type': 'Not Available',
                    'policy_status': 'Not Available',
                    'remaining_amount': 'Not Found',
                    'payer_id': payer_id,
                    'data_source': 'Error',
                    'is_successful': False,
                    'error_reason': 'OPTUMAI eligibility API returned no data'
                }
            
            # Process OptumAI response through merge_responses (with None for legacy)
            try:
                if merge_responses is not None:
                    merged_data = merge_responses(optumai_eligibility, None, date_of_birth, member_id, service_date=service_start)
                else:
                    MediLink_ConfigLoader.log("merge_responses utility not available; returning raw API response", level="WARNING")
                    merged_data = optumai_eligibility or {}
                
                # Silent insurance type mapping collection (for error reporting)
                _collect_and_merge_insurance_type_mapping(merged_data, optumai_eligibility)
                
                return merged_data
            except Exception as e:
                MediLink_ConfigLoader.log("Error in merge_responses: {}".format(e), level="ERROR")
                # Return a safe fallback result
                return {
                    'patient_name': 'Unknown Patient',
                    'dob': date_of_birth,
                    'member_id': member_id,
                    'insurance_type': 'Not Available',
                    'policy_status': 'Not Available',
                    'remaining_amount': 'Not Found',
                    'payer_id': payer_id,
                    'data_source': 'Error',
                    'is_successful': False,
                    'error_reason': 'Error processing OptumAI response: {}'.format(str(e))
                }
    except Exception as e:
        # Handle HTTP errors if requests is available
        if requests and hasattr(requests, 'exceptions') and isinstance(e, requests.exceptions.HTTPError):
            # Log the HTTP error response
            print("API Request Error: {}".format(e))
            if hasattr(e, 'response') and hasattr(e.response, 'content'):
                MediLink_ConfigLoader.log("Response content: {}".format(e.response.content), level="ERROR")
        else:
            # Log any other exceptions
            print("Eligibility Check Error: {}".format(e))
    return None

# API response parsing functions moved to MediCafe.deductible_utils
# All parsing logic is now centralized in the utility module for DRY compliance
#
# TODO (API DEVELOPER FIX REQUIRED):
# The following issues from the original commentary still need to be addressed:
# 1. Complete Super Connector API response schema - API developers are working on this
# 2. Full response structure validation - depends on stable API response structure  
# 3. Comprehensive test cases - requires consistent API responses
#
# CURRENT STATUS:
#  Enhanced logging and debugging capabilities implemented
#  Schema validation framework in place
#  Compatibility analysis functions added
#  Robust fallback mechanisms implemented
#  Complete API response schema validation (pending API fix)
#  Comprehensive test suite (pending stable API responses)
#
# NEXT STEPS:
# - Monitor API developer progress on Super Connector schema fixes
# - Update schema validation once API responses are stable
# - Create comprehensive test cases with known good responses
# - Consider adding automated schema detection for new API versions

# Function to extract required fields and display in a tabular format
def display_eligibility_info(data, dob, member_id, output_file, patient_id=None, service_date=None):
    """Legacy display function - converts to enhanced format and displays
    
    Args:
        data: Eligibility data to display
        dob: Date of birth
        member_id: Member ID
        output_file: File object to write to
        patient_id: Optional patient ID (unused, kept for signature compatibility)
        service_date: Optional service date (unused, kept for signature compatibility)
    """
    if data is None:
        return

    # Convert to enhanced format (guard if utility missing)
    enhanced_data = None
    if convert_eligibility_to_enhanced_format is not None:
        # Convert None to empty string for compatibility with utility function
        patient_id_str = patient_id if patient_id is not None else ""
        service_date_str = service_date if service_date is not None else ""
        enhanced_data = convert_eligibility_to_enhanced_format(data, dob, member_id, patient_id_str, service_date_str)
    if enhanced_data:
        # Write to output file in legacy format for compatibility
        table_row = "{:<20} | {:<10} | {:<40} | {:<5} | {:<14} | {:<14}".format(
            enhanced_data['patient_name'][:20], 
            enhanced_data['dob'], 
            enhanced_data['insurance_type'][:40], 
            enhanced_data['payer_id'][:5], 
            enhanced_data['policy_status'][:14], 
            enhanced_data['remaining_amount'][:14])
        output_file.write(table_row + "\n")
        print(table_row)  # Print to console for progressive display

# Helper to compute a user-friendly error explanation for a result row
def _compute_error_reason(record):
    # Delegate to centralized helper to avoid duplication
    try:
        from MediCafe.deductible_utils import compute_error_reason
        return compute_error_reason(record)
    except Exception:
        try:
            if not isinstance(record, dict):
                return ""
            reason = str(record.get('error_reason', '')).strip()
            name_unknown = (not str(record.get('patient_name', '')).strip()) or (record.get('patient_name') == 'Unknown Patient')
            has_error = (str(record.get('status', '')) == 'Error') or (str(record.get('data_source', '')) in ['None', 'Error'])
            amount_missing = (str(record.get('remaining_amount', '')) == 'Not Found')
            if not reason:
                if name_unknown:
                    reason = 'Patient name could not be determined from API responses or CSV backfill'
                elif amount_missing:
                    reason = 'Deductible remaining amount not found in eligibility response'
                elif has_error:
                    reason = 'Eligibility lookup encountered an error; see logs for details'
            return reason
        except Exception:
            return ""

# Global mode flags (will be set in main)
# Note: OPTUMAI_ONLY_MODE removed - default behavior when other flags are False
API_VALIDATION_MODE = False  # Troubleshooting: Dual API calls with validation
LEGACY_MODE = False  # Troubleshooting: Legacy API only
DEBUG_MODE_PAYER_PROBE = False  # Troubleshooting: Multi-payer probing (O(PxN) complexity)

# Crosswalk-based payer ID resolution cache
_payer_id_cache = None

# Silent insurance type mapping monitor (accumulates across batch for error reporting)
_insurance_type_mapping_monitor = {}

def _collect_and_merge_insurance_type_mapping(eligibility_data, fallback_data=None, second_fallback_data=None):
    """
    Helper function to collect insurance type mapping from eligibility data and merge into module monitor.
    Tries eligibility_data first, then fallback_data, then second_fallback_data.
    
    Args:
        eligibility_data: Primary eligibility data to collect from
        fallback_data: Optional fallback data if primary doesn't yield results
        second_fallback_data: Optional second fallback data
    """
    if collect_insurance_type_mapping_from_response is None:
        return
    
    try:
        mapping_entry = None
        if eligibility_data:
            mapping_entry = collect_insurance_type_mapping_from_response(eligibility_data)
        if not mapping_entry and fallback_data:
            mapping_entry = collect_insurance_type_mapping_from_response(fallback_data)
        if not mapping_entry and second_fallback_data:
            mapping_entry = collect_insurance_type_mapping_from_response(second_fallback_data)
        
        if mapping_entry:
            for api_code, unique_values in mapping_entry.items():
                if api_code in _insurance_type_mapping_monitor:
                    existing = _insurance_type_mapping_monitor[api_code]
                    existing_set = set(existing)
                    for val in unique_values:
                        if val not in existing_set:
                            existing.append(val)
                else:
                    _insurance_type_mapping_monitor[api_code] = unique_values
    except Exception:
        pass  # Silent failure - don't interrupt processing

# Payer ID resolution functions moved to MediCafe.deductible_utils
# All resolution logic is now centralized in the utility module for DRY compliance

# Main Execution Flow
if __name__ == "__main__":
    # Install unhandled exception hook to capture tracebacks
    try:
        if capture_unhandled_traceback is not None:
            sys.excepthook = capture_unhandled_traceback
    except Exception:
        pass

    try:
        print("\n" + "=" * 80)
        print("MEDILINK DEDUCTIBLE LOOKUP TOOL")
        print("=" * 80)
        print("This tool provides manual and batch eligibility lookups.")
        print("=" * 80)

        # Main menu for mode selection
        def show_troubleshooting_menu():
            """Display troubleshooting submenu and return selected mode."""
            while True:
                print("\n" + "=" * 80)
                print("TROUBLESHOOTING OPTIONS")
                print("=" * 80)
                print("1. API Validation Mode - Dual API calls (OptumAI + Legacy) with validation reports")
                print("2. Legacy Mode - Legacy API only (for compatibility testing)")
                print("3. Payer Probe Mode - Multi-payer probing (O(PxN) complexity, diagnostic only)")
                print("4. Back to Main Menu")
                
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice == "1":
                    return "validation"
                elif choice == "2":
                    return "legacy"
                elif choice == "3":
                    return "payer_probe"
                elif choice == "4":
                    return None
                else:
                    print("Invalid choice. Please enter 1-4.")
        
        # Main mode selection
        print("\nSelect operation mode:")
        print("1. Standard Mode (Default) - OptumAI endpoint only, cache-enabled, consolidated output")
        print("2. Troubleshooting Options")
        print("3. Exit")

        mode_choice = input("\nEnter your choice (1-3) [Default: 1]: ").strip()
        if not mode_choice:
            mode_choice = "1"

        if mode_choice == "3":
            print("\nExiting. Thank you for using MediLink Deductible Tool!")
            sys.exit(0)
        
        if mode_choice == "2":
            # Show troubleshooting submenu
            troubleshooting_mode = show_troubleshooting_menu()
            if troubleshooting_mode is None:
                print("\nExiting. Thank you for using MediLink Deductible Tool!")
                sys.exit(0)
            elif troubleshooting_mode == "validation":
                _set_mode_flags(validation=True, legacy=False, payer_probe=False)
                print("\nRunning in API VALIDATION MODE")
                print("- Dual API calls (OptumAI + Legacy)")
                print("- Validation reports and comparisons")
                print("- Detailed logging and error reporting")
                print("- Crosswalk-based payer ID resolution (O(N) complexity)")
            elif troubleshooting_mode == "legacy":
                _set_mode_flags(validation=False, legacy=True, payer_probe=False)
                print("\nRunning in LEGACY MODE")
                print("- Legacy API only")
                print("- For compatibility testing")
                print("- Progressive output during processing")
                print("- Consolidated output file at the end")
                print("- Crosswalk-based payer ID resolution (O(N) complexity)")
            elif troubleshooting_mode == "payer_probe":
                _set_mode_flags(validation=False, legacy=False, payer_probe=True)
                print("\nRunning in PAYER PROBE MODE")
                print("- Multi-payer probing for troubleshooting")
                print("- Original O(PxN) complexity algorithm")
                print("- Use only for diagnostic sessions")
                print("- Not recommended for production use")
        elif mode_choice not in ["1", "2", "3"]:
            print("Invalid choice. Using Standard Mode (Default).")
            mode_choice = "1"
        
        # Set default mode (Standard Mode - OptumAI only)
        if mode_choice == "1":
            _set_mode_flags(validation=False, legacy=False, payer_probe=False)
            print("\nRunning in STANDARD MODE")
            print("- OptumAI endpoint only")
            print("- Cache-enabled")
            print("- Consolidated output")
            print("- Crosswalk-based payer ID resolution (O(N) complexity)")

        while True:
            print("\nChoose an option:")
            print("1. Manual Patient Lookup")
            print("2. Batch CSV Processing")
            print("3. Select CSV File")
            print("4. Exit")

            choice = input("\nEnter your choice (1-4): ").strip()
            
            # Initialize variables for summary (used outside batch processing block)
            eligibility_results = []
            patients_to_process = []
            cache_hits_zero = 0
            cache_hits_recent = 0
            api_call_attempts = 0
            errors = []
            validation_files_created = []

            if choice == "1":
                # Step 1: Handle Manual Deductible Lookups
                manual_deductible_lookup()

                # Ask if user wants to continue
                continue_choice = input("\nDo you want to perform another operation? (Y/N): ").strip().lower()
                if continue_choice in ['n', 'no']:
                    print("\nExiting. Thank you for using MediLink Deductible Tool!")
                    break

            elif choice == "2":
                # Step 2: Proceed with Existing CSV Processing
                print("\n--- Starting Batch Eligibility Processing ---")
                
                # Prompt user to select CSV file each time batch processing is selected
                selected_csv = select_csv_file(CSV_DIR)
                if not selected_csv:
                    print("Batch processing cancelled - no CSV file selected.")
                    continue
                
                # Reload CSV data with selected file
                success, error_msg = reload_csv_data(selected_csv)
                if not success:
                    print("\nFailed to load CSV file: {}".format(error_msg))
                    print("Batch processing cancelled.")
                    continue
                
                print("Processing {} patients from CSV data...".format(len(patients)))

                # Ask for confirmation before starting batch processing
                confirm = input("Proceed with batch processing? (Y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    print("Batch processing cancelled.")
                    continue
                
                # Record start time for processing time calculation
                batch_start_time = time.time()

                # PERFORMANCE OPTIMIZATION: Crosswalk-based payer ID resolution
                # This eliminates O(PxN) complexity by using CSV/crosswalk data as authoritative source
                # Multi-payer probing is retained behind DEBUG_MODE_PAYER_PROBE toggle for troubleshooting

                # Load crosswalk data for payer ID resolution
                try:
                    _, crosswalk = _get_config()
                except Exception as e:
                    MediLink_ConfigLoader.log("Failed to load crosswalk data: {}".format(e), level="WARNING")
                    crosswalk = {}

                # Pre-resolve payer IDs for all patients (O(N) operation)
                if not DEBUG_MODE_PAYER_PROBE:
                    if resolve_payer_ids_from_csv is not None:
                        # Use valid_rows instead of csv_data to ensure cache keys match the patients we'll process
                        # This ensures the (dob, member_id) format is consistent
                        _payer_id_cache = resolve_payer_ids_from_csv(valid_rows, config, crosswalk, payer_ids)
                        print("Resolved {} patient-payer mappings from CSV data".format(len(_payer_id_cache)))
                        # Log sample cache keys for debugging
                        if _payer_id_cache:
                            sample_keys = list(_payer_id_cache.keys())[:3]
                            MediLink_ConfigLoader.log("Sample cache keys: {}".format(sample_keys), level="DEBUG")
                    else:
                        # Fallback if utility function not available
                        _payer_id_cache = {}
                        print("Warning: Payer ID resolution utility not available, using empty cache")

                errors = []
                validation_files_created = []  # Track validation files that were actually created
                printed_messages = set()                 # Initialize a set to track printed messages
                results_by_patient = {}
                patients_to_process = []
                cache_hits_zero = 0
                cache_hits_recent = 0
                # TEMPORARY: Track cache hits for diagnostic API calls (to populate diagnostic columns from fresh API data)
                # TODO: DEPRECATE - Once users provide feedback on which diagnostic column contains the correct value,
                #       and extract_super_connector_remaining_amount() is updated with correct selection logic, this
                #       diagnostic API call behavior should be removed. Cache hits should skip API calls entirely,
                #       and diagnostic columns should no longer be displayed. The system will return to using only
                #       the single selected remaining_amount value.
                cache_hit_patients = {}  # Key: (dob, member_id), Value: (cache_payload, cache_reason, patient_info)

                # Import cache lookup function if available
                try:
                    from MediLink.insurance_type_cache import lookup as cache_lookup_func
                except Exception:
                    cache_lookup_func = None

                # Decide which patients can be fulfilled directly from cache
                MediLink_ConfigLoader.log(
                    "Starting cache check loop for {} patients".format(len(patients)),
                    level="DEBUG"
                )
                patients_processed_count = 0
                for dob, member_id in patients:
                    try:
                        patients_processed_count += 1
                        MediLink_ConfigLoader.log(
                            "Processing patient {}/{} in cache check loop: DOB='{}', MemberID='{}'".format(
                                patients_processed_count, len(patients), dob, member_id
                            ),
                            level="DEBUG"
                        )
                        patient_info = patient_row_index.get((dob, member_id))
                        if not patient_info:
                            MediLink_ConfigLoader.log(
                                "WARNING: patient_info not found in patient_row_index for (DOB: {}, MemberID: {})".format(
                                    dob, member_id
                                ), level="WARNING")
                            # Still proceed - patient_info might be None but we can still try to process
                        patient_id = _get_patient_id_from_row(patient_info) if patient_info else ''
                        
                        # Get service_date from patient_groups for cache lookup
                        service_date_for_cache = None
                        service_date_for_stale_check = None
                        service_records = patient_groups.get((dob, member_id), [])
                        if service_records and len(service_records) > 0:
                            service_date_sort = service_records[0].get('service_date_sort')
                            if service_date_sort and service_date_sort != datetime.min:
                                service_date_for_cache = service_date_sort.strftime('%Y-%m-%d')
                                service_date_for_stale_check = service_date_sort
                        
                        # Fallback to extracting from CSV row if not found in patient_groups
                        if not service_date_for_cache and _extract_service_date_from_csv_row and patient_info:
                            _, service_date_dt = _extract_service_date_from_csv_row(patient_info)
                            if service_date_dt != datetime.min:
                                service_date_for_cache = service_date_dt.strftime('%Y-%m-%d')
                                service_date_for_stale_check = service_date_dt
                        
                        # Stale patient check disabled for batch processing
                        # Batch processing should handle historical data regardless of service date age
                        # The stale check was preventing processing of valid historical eligibility data
                        # If service date is available, log it for reference but don't skip processing
                        if service_date_for_stale_check:
                            MediLink_ConfigLoader.log(
                                "Processing patient with service date (DOB: {}, MemberID: {}, ServiceDate: {})".format(
                                    dob, member_id, service_date_for_stale_check
                                ), level="DEBUG")
                        elif not service_date_for_stale_check:
                            # No service date available - log for debugging
                            MediLink_ConfigLoader.log(
                                "No service date available for patient (DOB: {}, MemberID: {}) - proceeding without service date".format(
                                    dob, member_id
                                ), level="DEBUG")
                        
                        use_cache = False
                        cache_payload = None
                        cache_reason = None
                        # Log cache lookup conditions for debugging
                        if not cache_lookup_func:
                            MediLink_ConfigLoader.log(
                                "Cache lookup function not available for patient (DOB: {}, MemberID: {})".format(
                                    dob, member_id
                                ), level="INFO")
                        elif not patient_id:
                            MediLink_ConfigLoader.log(
                                "Patient ID is empty for patient (DOB: {}, MemberID: {}) - cannot lookup cache".format(
                                    dob, member_id
                                ), level="INFO")
                        elif not CSV_DIR:
                            MediLink_ConfigLoader.log(
                                "CSV_DIR is empty for patient (DOB: {}, MemberID: {}) - cannot lookup cache".format(
                                    dob, member_id
                                ), level="INFO")
                        
                        if cache_lookup_func and patient_id and CSV_DIR:
                            try:
                                cache_payload = cache_lookup_func(
                                    patient_id=patient_id, 
                                    csv_dir=CSV_DIR, 
                                    return_full=True,
                                    service_date=service_date_for_cache
                                )
                                if cache_payload:
                                    # Validate that cached insurance code is a valid short code
                                    cached_code = cache_payload.get('code', '')
                                    if not _is_valid_insurance_code(cached_code):
                                        # Invalid code (description, "Not Available", etc.) - skip cache and call API
                                        MediLink_ConfigLoader.log(
                                            "Cache code invalid for patient {}: '{}' - will call API".format(
                                                patient_id, cached_code[:50]), level="INFO")
                                        cache_payload = None
                                    else:
                                        recent_cache = _is_recent_cache_payload(cache_payload)
                                        ok_amount, cache_amount = _parse_remaining_amount(cache_payload.get('remaining_amount'))
                                        if ok_amount and cache_amount <= 0.0:
                                            use_cache = True
                                            cache_reason = 'zero'
                                        elif recent_cache:
                                            use_cache = True
                                            cache_reason = 'recent'
                            except Exception:
                                pass
                        
                        if use_cache:
                            if cache_reason == 'zero':
                                cache_hits_zero += 1
                            elif cache_reason == 'recent':
                                cache_hits_recent += 1
                            
                            # TEMPORARY: Store cache hit info for diagnostic API call
                            # We still need to make API calls to get fresh diagnostic data (all_deductible_amounts)
                            # TODO: DEPRECATE - Once correct selection logic is identified and implemented, cache hits
                            #       should skip API calls entirely. This diagnostic behavior is only needed until users
                            #       provide feedback on which column contains the correct deductible value.
                            cache_hit_patients[(dob, member_id)] = (cache_payload, cache_reason, patient_info)
                            
                            # TEMPORARY: Still add to processing queue to get fresh API data for diagnostic columns
                            # The cached value will be used for the CURRENT column, fresh API data for diagnostic columns
                            # TODO: DEPRECATE - Remove this diagnostic API call behavior once selection logic is corrected
                            patients_to_process.append((dob, member_id))
                            
                            remaining_display = cache_payload.get('remaining_amount', '0.00') if isinstance(cache_payload, dict) else '0.00'
                            if cache_reason == 'recent':
                                MediLink_ConfigLoader.log(
                                    "Cache fresh (<24h) for patient {} (DOB {}, Member ID {}) - will call API for diagnostic data".format(
                                        patient_id or 'UNKNOWN', dob, member_id),
                                    level="DEBUG"
                                )
                            else:
                                MediLink_ConfigLoader.log(
                                    "Cache satisfied patient {} (DOB {}, Member ID {}) -> remaining {} (will call API for diagnostic data)".format(
                                        patient_id or 'UNKNOWN', dob, member_id, remaining_display),
                                    level="DEBUG"
                                )
                        else:
                            # Log when patient is added to processing queue for debugging
                            MediLink_ConfigLoader.log(
                                "Adding patient to API queue: DOB='{}', MemberID='{}', PatientID='{}', CSV_DIR='{}'".format(
                                    dob, member_id, patient_id or '(empty)', CSV_DIR or '(empty)'
                                ),
                                level="DEBUG"
                            )
                            patients_to_process.append((dob, member_id))
                    except Exception as e:
                        # Log any exceptions during patient processing
                        MediLink_ConfigLoader.log(
                            "Exception processing patient (DOB: {}, MemberID: {}): {}".format(
                                dob, member_id, str(e)
                            ), level="ERROR")
                        import traceback
                        MediLink_ConfigLoader.log(
                            "Traceback: {}".format(traceback.format_exc()),
                            level="ERROR"
                        )
                        # Continue processing other patients even if one fails
                        continue

                MediLink_ConfigLoader.log(
                    "Cache check loop complete. Processed {} patients, {} added to queue".format(
                        patients_processed_count, len(patients_to_process)
                    ),
                    level="INFO"  # Keep as INFO - this is a summary message
                )
                total_api_targets = len(patients_to_process)
                processed_count = 0
                api_call_attempts = 0
                
                # Log diagnostic info about patients to process
                if total_api_targets == 0:
                    MediLink_ConfigLoader.log(
                        "WARNING: No patients added to patients_to_process. Total patients: {}, Cache hits (zero): {}, Cache hits (recent): {}".format(
                            len(patients), cache_hits_zero, cache_hits_recent
                        ), level="WARNING")
                    # Log sample patient keys for comparison
                    if patients:
                        sample_patients = list(patients)[:3]
                        MediLink_ConfigLoader.log("Sample patient keys: {}".format(sample_patients), level="WARNING")
                    if _payer_id_cache:
                        sample_cache_keys = list(_payer_id_cache.keys())[:3]
                        MediLink_ConfigLoader.log("Sample cache keys: {}".format(sample_cache_keys), level="WARNING")

                for dob, member_id in patients_to_process:
                    processed_count += 1
                    print("Processing patient {}/{}: Member ID {}, DOB {}".format(
                        processed_count, total_api_targets, member_id, dob))

                    # Get payer ID for this patient
                    if DEBUG_MODE_PAYER_PROBE:
                        # PAYER PROBE MODE: Use multi-payer probing (original O(PxN) logic)
                        patient_processed = False
                        for payer_id in payer_ids:
                            try:
                                # Determine API mode based on global flags (payer probe uses optumai_only but with multi-payer loop)
                                api_mode = _determine_api_mode()
                                api_call_attempts += 1
                                # Get service_date from patient_groups or CSV row
                                service_date_for_api = _get_service_date_for_api(dob, member_id, patient_groups, patient_row_index)
                                # Best-effort group number from CSV (optional discriminator)
                                group_number_for_api = None
                                try:
                                    patient_info = patient_row_index.get((dob, member_id))
                                    if patient_info and extract_group_number_from_csv_row:
                                        group_number_for_api = extract_group_number_from_csv_row(patient_info)
                                except Exception:
                                    group_number_for_api = None
                                eligibility_data = get_eligibility_info(
                                    client, payer_id, provider_last_name, dob, member_id, npi,
                                    api_mode=api_mode, is_manual_lookup=False, printed_messages=printed_messages,
                                    service_date=service_date_for_api, group_number=group_number_for_api
                                )
                                if eligibility_data is not None:
                                    # Silent insurance type mapping collection (for error reporting)
                                    # Try to collect even if already processed (may have rawGraphQLResponse preserved)
                                    _collect_and_merge_insurance_type_mapping(eligibility_data)
                                    
                                    if isinstance(eligibility_data, dict) and 'patient_name' in eligibility_data and 'data_source' in eligibility_data:
                                        enhanced_result = eligibility_data
                                    elif convert_eligibility_to_enhanced_format is not None:
                                        patient_info = patient_row_index.get((dob, member_id))
                                        service_date = ""
                                        if patient_info:
                                            service_date = patient_info.get('Service Date', '')
                                        enhanced_result = convert_eligibility_to_enhanced_format(
                                            eligibility_data, dob, member_id, 
                                            patient_info.get('Patient ID', '') if patient_info else '',
                                            service_date
                                        )
                                    else:
                                        enhanced_result = None
                                    if enhanced_result:
                                        patient_info = None
                                        try:
                                            patient_info = patient_row_index.get((dob, member_id))
                                            enhanced_result = backfill_enhanced_result(enhanced_result, patient_info)
                                        except Exception:
                                            pass
                                        
                                        # TEMPORARY: If this was a cache hit, merge cached value with fresh API diagnostic data
                                        # Use cached remaining_amount for CURRENT column, fresh API data for diagnostic columns
                                        # TODO: DEPRECATE - Once users provide feedback and correct selection logic is implemented,
                                        #       remove this diagnostic merging behavior. Cache hits should not trigger API calls,
                                        #       and diagnostic columns should not be displayed. The system will use only the
                                        #       single correctly-selected remaining_amount value.
                                        cache_key = (dob, member_id)
                                        if cache_key in cache_hit_patients:
                                            cache_payload, cache_reason, cached_patient_info = cache_hit_patients[cache_key]
                                            # Preserve the cached remaining_amount (what's currently being used)
                                            cached_remaining = cache_payload.get('remaining_amount', '') if isinstance(cache_payload, dict) else ''
                                            if cached_remaining:
                                                # Format cached value with cache reason label
                                                cache_label = cache_reason if cache_reason else 'cache'
                                                enhanced_result['remaining_amount'] = "{} ({})".format(cached_remaining, cache_label)
                                            # Keep fresh API diagnostic data (all_deductible_amounts) from enhanced_result
                                            # This allows users to see cached value vs all available options
                                            MediLink_ConfigLoader.log(
                                                "Merged cache hit with fresh API diagnostic data for patient (DOB: {}, MemberID: {})".format(
                                                    dob, member_id),
                                                level="DEBUG"
                                            )
                                        
                                        # Write to cache (only if result is successful or has valid data)
                                        # TEMPORARY: Skip cache write if this was already a cache hit (to avoid unnecessary writes)
                                        # TODO: DEPRECATE - Once diagnostic behavior is removed, cache writes should proceed normally
                                        if cache_key not in cache_hit_patients:
                                            if not patient_info:
                                                patient_info = patient_row_index.get((dob, member_id))
                                            if put_entry_from_enhanced_result:
                                                put_entry_from_enhanced_result(CSV_DIR, enhanced_result, dob, member_id, payer_id,
                                                                               csv_row=patient_info, service_date_for_api=service_date_for_api, context="batch")
                                        results_by_patient[(dob, member_id)] = enhanced_result
                                        patient_processed = True

                                        if API_VALIDATION_MODE:
                                            validation_file_path = os.path.join(os.getenv('TEMP'), 'validation_report_{}_{}.txt'.format(member_id, dob))
                                            if os.path.exists(validation_file_path):
                                                msg = "  Validation report created: {}".format(os.path.basename(validation_file_path))
                                                if msg not in printed_messages:
                                                    print(msg)
                                                    printed_messages.add(msg)
                                                validation_files_created.append(validation_file_path)
                                        break  # Stop trying other payer_ids
                            except Exception:
                                continue
                        
                        if not patient_processed:
                            error_msg = "No successful payer_id found for patient (Payer Probe Mode)"
                            errors.append((dob, member_id, error_msg))
                    else:
                        # PRODUCTION MODE: Use crosswalk-resolved payer ID (O(N) complexity)
                        if get_payer_id_for_patient is not None:
                            # Log lookup attempt for debugging
                            lookup_key = (dob, member_id)
                            MediLink_ConfigLoader.log(
                                "Looking up payer_id for patient: DOB='{}', MemberID='{}', Key={}".format(
                                    dob, member_id, lookup_key
                                ), level="DEBUG")
                            payer_id = get_payer_id_for_patient(dob, member_id, _payer_id_cache)
                            if payer_id:
                                MediLink_ConfigLoader.log(
                                    "Found payer_id '{}' for patient (DOB: {}, MemberID: {})".format(
                                        payer_id, dob, member_id
                                    ), level="DEBUG")
                            else:
                                MediLink_ConfigLoader.log(
                                    "No payer_id found for patient (DOB: {}, MemberID: {})".format(
                                        dob, member_id
                                    ), level="WARNING")
                        else:
                            payer_id = None
                        
                        if payer_id:
                            try:
                                # Determine API mode based on global flags
                                api_mode = _determine_api_mode()
                                api_call_attempts += 1
                                # Get service_date from patient_groups or CSV row
                                service_date_for_api = _get_service_date_for_api(dob, member_id, patient_groups, patient_row_index)
                                # Best-effort group number from CSV (optional discriminator)
                                group_number_for_api = None
                                try:
                                    patient_info = patient_row_index.get((dob, member_id))
                                    if patient_info and extract_group_number_from_csv_row:
                                        group_number_for_api = extract_group_number_from_csv_row(patient_info)
                                except Exception:
                                    group_number_for_api = None
                                eligibility_data = get_eligibility_info(
                                    client, payer_id, provider_last_name, dob, member_id, npi,
                                    api_mode=api_mode, is_manual_lookup=False, printed_messages=printed_messages,
                                    service_date=service_date_for_api, group_number=group_number_for_api
                                )
                                if eligibility_data is not None:
                                    # Silent insurance type mapping collection (for error reporting)
                                    # Try to collect even if already processed (may have rawGraphQLResponse preserved)
                                    _collect_and_merge_insurance_type_mapping(eligibility_data)
                                    
                                    if isinstance(eligibility_data, dict) and 'patient_name' in eligibility_data and 'data_source' in eligibility_data:
                                        enhanced_result = eligibility_data
                                    elif convert_eligibility_to_enhanced_format is not None:
                                        patient_info = patient_row_index.get((dob, member_id))
                                        service_date = ""
                                        if patient_info:
                                            service_date = patient_info.get('Service Date', '')
                                        enhanced_result = convert_eligibility_to_enhanced_format(
                                            eligibility_data, dob, member_id, 
                                            patient_info.get('Patient ID', '') if patient_info else '',
                                            service_date
                                        )
                                    else:
                                        enhanced_result = None
                                    
                                    # Handle case where conversion failed or returned None
                                    if enhanced_result:
                                        patient_info = None
                                        try:
                                            patient_info = patient_row_index.get((dob, member_id))
                                            enhanced_result = backfill_enhanced_result(enhanced_result, patient_info)
                                        except Exception:
                                            pass
                                        
                                        # If this was a cache hit, merge cached value with fresh API diagnostic data
                                        # Use cached remaining_amount for CURRENT column, fresh API data for diagnostic columns
                                        cache_key = (dob, member_id)
                                        if cache_key in cache_hit_patients:
                                            cache_payload, cache_reason, cached_patient_info = cache_hit_patients[cache_key]
                                            # Preserve the cached remaining_amount (what's currently being used)
                                            cached_remaining = cache_payload.get('remaining_amount', '') if isinstance(cache_payload, dict) else ''
                                            if cached_remaining:
                                                # Format cached value with cache reason label
                                                cache_label = cache_reason if cache_reason else 'cache'
                                                enhanced_result['remaining_amount'] = "{} ({})".format(cached_remaining, cache_label)
                                            # Keep fresh API diagnostic data (all_deductible_amounts) from enhanced_result
                                            # This allows users to see cached value vs all available options
                                            MediLink_ConfigLoader.log(
                                                "Merged cache hit with fresh API diagnostic data for patient (DOB: {}, MemberID: {})".format(
                                                    dob, member_id),
                                                level="DEBUG"
                                            )
                                        
                                        # Write to cache (only if result is successful or has valid data)
                                        # TEMPORARY: Skip cache write if this was already a cache hit (to avoid unnecessary writes)
                                        # TODO: DEPRECATE - Once diagnostic behavior is removed, cache writes should proceed normally
                                        if cache_key not in cache_hit_patients:
                                            if not patient_info:
                                                patient_info = patient_row_index.get((dob, member_id))
                                            if put_entry_from_enhanced_result:
                                                put_entry_from_enhanced_result(CSV_DIR, enhanced_result, dob, member_id, payer_id,
                                                                               csv_row=patient_info, service_date_for_api=service_date_for_api, context="batch")
                                        results_by_patient[(dob, member_id)] = enhanced_result

                                        if API_VALIDATION_MODE:
                                            validation_file_path = os.path.join(os.getenv('TEMP'), 'validation_report_{}_{}.txt'.format(member_id, dob))
                                            if os.path.exists(validation_file_path):
                                                msg = "  Validation report created: {}".format(os.path.basename(validation_file_path))
                                                if msg not in printed_messages:
                                                    print(msg)
                                                    printed_messages.add(msg)
                                                validation_files_created.append(validation_file_path)
                                    else:
                                        # Conversion failed or returned None - log and add to errors
                                        MediLink_ConfigLoader.log(
                                            "Failed to convert eligibility data to enhanced format for patient (DOB: {}, MemberID: {})".format(
                                                dob, member_id
                                            ), level="WARNING")
                                        error_msg = "Eligibility data conversion failed for payer_id {}".format(payer_id)
                                        errors.append((dob, member_id, error_msg))
                                else:
                                    error_msg = "No eligibility data returned for payer_id {}".format(payer_id)
                                    errors.append((dob, member_id, error_msg))
                            except Exception as e:
                                error_msg = "API error for payer_id {}: {}".format(payer_id, str(e))
                                errors.append((dob, member_id, error_msg))
                        else:
                            # Log diagnostic info when payer_id lookup fails
                            cache_keys_sample = list(_payer_id_cache.keys())[:3] if _payer_id_cache else []
                            lookup_key = (dob, member_id)
                            MediLink_ConfigLoader.log(
                                "No payer_id resolved for patient (DOB: {}, Member ID: {}). Cache has {} entries. Sample keys: {}".format(
                                    dob, member_id, len(_payer_id_cache), cache_keys_sample
                                ), level="WARNING")
                            error_msg = "No payer_id resolved from CSV/crosswalk data"
                            errors.append((dob, member_id, error_msg))

                eligibility_results = [results_by_patient[key] for key in patients if key in results_by_patient]

                # Display results using enhanced table
                if eligibility_results:
                    print("\n" + "=" * 80)
                    display_enhanced_deductible_table(eligibility_results, context="post_api")
                    print("=" * 80)
            
                # Enhanced processing summary (only after batch processing)
                print("\n" + "=" * 80)
                print("PROCESSING SUMMARY")
                print("=" * 80)
                
                # Calculate processing statistics
                total_patients = len(patients)
                successful_lookups = sum(1 for r in eligibility_results if r.get('is_successful', False))
                failed_lookups = total_patients - successful_lookups
                success_rate = int(100 * successful_lookups / total_patients) if total_patients > 0 else 0
                api_calls_made = api_call_attempts
                
                # Calculate processing time from actual start time
                batch_end_time = time.time()
                elapsed_seconds = int(batch_end_time - batch_start_time)
                minutes = elapsed_seconds // 60
                seconds = elapsed_seconds % 60
                if minutes > 0:
                    processing_time = "{} minute{} {} second{}".format(
                        minutes, 's' if minutes != 1 else '',
                        seconds, 's' if seconds != 1 else '')
                else:
                    processing_time = "{} second{}".format(seconds, 's' if seconds != 1 else '')
                
                # Determine operation mode for summary
                if API_VALIDATION_MODE:
                    operation_mode = "API Validation Mode"
                elif LEGACY_MODE:
                    operation_mode = "Legacy Mode"
                elif DEBUG_MODE_PAYER_PROBE:
                    operation_mode = "Payer Probe Mode"
                else:
                    operation_mode = "Standard Mode (OptumAI Only)"
                
                # Performance optimization statistics
                if DEBUG_MODE_PAYER_PROBE:
                    complexity_mode = "O(PxN) - Multi-payer probing"
                    optimization_note = "Using original algorithm for troubleshooting"
                else:
                    complexity_mode = "O(N) - Crosswalk-based resolution"
                    optimization_note = "Optimized using CSV/crosswalk data"
                
                print("Operation Mode: {}".format(operation_mode))
                print("Total patients in CSV: {}".format(total_patients))
                print("Patients satisfied from cache (remaining_amount <= 0): {}".format(cache_hits_zero))
                print("Patients skipped due to recent cache (<24h): {}".format(cache_hits_recent))
                print("Patients sent to API: {}".format(len(patients_to_process)))
                print("Successful lookups: {}".format(successful_lookups))
                print("Failed lookups: {}".format(failed_lookups))
                print("Success rate: {}%".format(success_rate))
                print("Processing time: {}".format(processing_time))
                print("Algorithm complexity: {}".format(complexity_mode))
                print("API calls attempted: {}".format(api_calls_made))
                print("Optimization: {}".format(optimization_note))
                print("=" * 80)
                
                # Enhanced error display if any errors occurred
                if errors:
                    print("\n" + "=" * 50)
                    print("ERROR SUMMARY")
                    print("=" * 50)
                    for i, (dob, member_id, error_msg) in enumerate(errors, 1):
                        print("{:02d}. Member ID: {} | DOB: {} | Error: {}".format(
                            i, member_id, dob, error_msg))
                    print("=" * 50)
                    
                    # Provide recommendations for common errors
                    print("\nRecommendations:")
                    print("- Check network connectivity")
                    print("- Verify member ID formats")
                    print("- Contact support for API issues")
                
                # Write results to file for legacy compatibility
                output_file_path = os.path.join(os.getenv('TEMP'), 'eligibility_report.txt')
                with open(output_file_path, 'w') as output_file:
                    table_header = "{:<20} | {:<10} | {:<8} | {:<5} | {:<14} | {:<14}".format(
                        "Patient Name", "DOB", "IT Code", "PayID", "Policy Status", "Remaining Amt")
                    output_file.write(table_header + "\n")
                    output_file.write("-" * len(table_header) + "\n")

                    # Global notice when OPTUMAI eligibility connection failed for any patients
                    try:
                        sc_failed_count = sum(1 for r in eligibility_results if isinstance(r, dict) and r.get('super_connector_failed'))
                        if sc_failed_count:
                            output_file.write("NOTICE: OPTUMAI eligibility API connection failed for {} patient(s). Fallback data used when available.\n".format(sc_failed_count))
                    except Exception:
                        pass
                    
                    # Write all results to file
                    for result in eligibility_results:
                        table_row = "{:<20} | {:<10} | {:<8} | {:<5} | {:<14} | {:<14}".format(
                            result['patient_name'][:20], 
                            result['dob'], 
                            result['insurance_type'][:8], 
                            result['payer_id'][:5], 
                            result['policy_status'][:14], 
                            result['remaining_amount'][:14])
                        output_file.write(table_row + "\n")

                        # Persist per-row error diagnostics in a user-friendly way
                        try:
                            row_reason = _compute_error_reason(result)
                            row_messages = result.get('error_messages', []) or []
                            if row_reason or row_messages:
                                output_file.write("  >> Errors:" + "\n")
                                if row_reason:
                                    output_file.write("  >> - {}\n".format(row_reason))
                                for msg in row_messages:
                                    if not row_reason or msg.strip() != row_reason.strip():
                                        output_file.write("  >> - {}\n".format(str(msg)))
                        except Exception:
                            pass

                    # Write enhanced error summary to file
                    if errors:
                        error_msg = "\nErrors encountered during API calls:\n"
                        output_file.write(error_msg)
                        for error in errors:
                            error_details = "DOB: {}, Member ID: {}, Error: {}\n".format(error[0], error[1], error[2])
                            output_file.write(error_details)

                # Ask if user wants to open the report
                open_report = input("\nBatch processing complete! Open the eligibility report? (Y/N): ").strip().lower()
                if open_report in ['y', 'yes']:
                    os.startfile(output_file_path)
                
                # Print summary of validation reports only in API validation mode
                if API_VALIDATION_MODE:
                    print("\n" + "=" * 80)
                    print("VALIDATION SUMMARY")
                    print("=" * 80)
                    validation_files_created = list(set(validation_files_created))  # Dedupe
                    if validation_files_created:
                        print("Validation reports generated: {} files".format(len(validation_files_created)))
                        print("Files created:")
                        for file_path in validation_files_created:
                            print("  - {}".format(os.path.basename(file_path)))
                        
                        # Ask if user wants to open validation reports
                        open_validation = input("\nOpen validation reports in Notepad? (Y/N): ").strip().lower()
                        if open_validation in ['y', 'yes']:
                            for file_path in validation_files_created:
                                print("Opening: {}".format(os.path.basename(file_path)))
                                os.startfile(file_path)
                    else:
                        print("No validation reports were generated.")
                        print("This may be because:")
                        print("  - OPTUMAI eligibility API calls failed")
                        print("  - Both APIs didn't return data for the same patients")
                        print("  - Validation report generation encountered errors")
                    print("=" * 80)
            
                # Ask if user wants to continue
                continue_choice = input("\nDo you want to perform another operation? (Y/N): ").strip().lower()
                if continue_choice in ['n', 'no']:
                    print("\nExiting. Thank you for using MediLink Deductible Tool!")
                    break

            elif choice == "3":
                # Select CSV File option
                selected_csv = select_csv_file(CSV_DIR)
                if selected_csv:
                    success, error_msg = reload_csv_data(selected_csv)
                    if not success:
                        print("\nFailed to reload CSV file: {}".format(error_msg))
                        print("Please try selecting a different file or check the file format.")
                    else:
                        print("\nCSV file reloaded successfully.")
                else:
                    print("\nCSV selection cancelled.")

            elif choice == "4":
                print("\nExiting. Thank you for using MediLink Deductible Tool!")
                break

            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

    except Exception as e:
        print("\n" + "="*60)
        print("DEDUCTIBLE LOOKUP EXECUTION FAILURE")
        print("="*60)
        print("Error: {}".format(e))
        print("Error type: {}".format(type(e).__name__))
        print("="*60)

        # Collect and submit error report
        try:
            if submit_support_bundle_email is not None and collect_support_bundle is not None:
                zip_path = collect_support_bundle(include_traceback=True, insurance_type_mapping=_insurance_type_mapping_monitor if _insurance_type_mapping_monitor else None)
                if zip_path:
                    # Try to check internet connectivity
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
            print("Error report collection failed: {}".format(report_e))
            print("Error report collection failed: {}".format(report_e))