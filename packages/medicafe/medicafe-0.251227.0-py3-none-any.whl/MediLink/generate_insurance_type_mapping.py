"""
Simple script to generate API insurance type code to description mapping.
Processes CSV data, calls eligibility APIs, and prints unique mappings to console.
"""
import os
import sys
from datetime import datetime
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
            resolve_payer_ids_from_csv,
            get_payer_id_for_patient,
            _extract_service_date_from_csv_row,
            collect_insurance_type_mapping_from_response
        )
    except ImportError as e:
        print("Warning: Unable to import MediCafe.deductible_utils: {}".format(e))
        validate_and_format_date = None
        resolve_payer_ids_from_csv = None
        get_payer_id_for_patient = None
        _extract_service_date_from_csv_row = None
except ImportError as e:
    print("Error: Unable to import MediCafe.core_utils. Please ensure MediCafe package is properly installed.")
    print("Import error: {}".format(e))
    sys.exit(1)

try:
    from MediBot import MediBot_Preprocessor_lib
except ImportError as e:
    print("Error: Cannot import MediBot_Preprocessor_lib: {}".format(e))
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
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return None

# Use latest core_utils configuration cache for better performance
_get_config, (_config_cache, _crosswalk_cache) = create_config_cache()

# Load configuration
config, _ = _get_config()

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

# Define the list of payer_id's to iterate over
payer_ids = ['87726', '03432', '96385', '95467', '86050', '86047', '95378', '06111', '37602']  # United Healthcare ONLY.

# Get the latest CSV
CSV_FILE_PATH = config.get('CSV_FILE_PATH', "")

# Load CSV data
try:
    csv_data = MediBot_Preprocessor_lib.load_csv_data(CSV_FILE_PATH)
    print("Successfully loaded CSV data: {} records".format(len(csv_data)))
except Exception as e:
    print("Error loading CSV data: {}".format(e))
    print("CSV_FILE_PATH: {}".format(CSV_FILE_PATH))
    sys.exit(1)

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
    if dob and member_id:
        patient_groups[(dob, member_id)].append(row)

# Get unique patients
patients = list(patient_groups.keys())

print("\nProcessing {} unique patients to extract insurance type mappings...".format(len(patients)))

# Load crosswalk data for payer ID resolution
try:
    _, crosswalk = _get_config()
except Exception as e:
    MediLink_ConfigLoader.log("Failed to load crosswalk data: {}".format(e), level="WARNING")
    crosswalk = {}

# Pre-resolve payer IDs for all patients
if resolve_payer_ids_from_csv is not None:
    _payer_id_cache = resolve_payer_ids_from_csv(csv_data, config, crosswalk, payer_ids)
    print("Resolved {} patient-payer mappings from CSV data".format(len(_payer_id_cache)))
else:
    _payer_id_cache = {}

# Dictionary to store unique API code -> description mappings
api_code_mapping = {}

# Process each patient
processed = 0
for dob, member_id in patients:
    processed += 1
    if processed % 10 == 0:
        print("Processed {}/{} patients...".format(processed, len(patients)))
    
    # Get payer ID for this patient
    payer_id = None
    if get_payer_id_for_patient is not None:
        payer_id = get_payer_id_for_patient(dob, member_id, _payer_id_cache)
    
    if not payer_id:
        # Skip if no payer ID resolved
        continue
    
    # Get service_date from patient_groups or CSV row
    service_date_for_api = None
    service_records = patient_groups.get((dob, member_id), [])
    if service_records and len(service_records) > 0:
        service_date = service_records[0].get('Service Date', '')
        if service_date:
            try:
                # Try common date formats
                for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%y', '%m/%d/%y']:
                    try:
                        service_date_dt = datetime.strptime(service_date, fmt)
                        service_date_for_api = service_date_dt.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
            except:
                pass
    
    # Fallback to extracting from CSV row if not found
    if not service_date_for_api and _extract_service_date_from_csv_row:
        patient_info = patient_row_index.get((dob, member_id))
        if patient_info:
            _, service_date_dt = _extract_service_date_from_csv_row(patient_info)
            if service_date_dt != datetime.min:
                service_date_for_api = service_date_dt.strftime('%Y-%m-%d')
    
    service_start = service_date_for_api
    service_end = service_start  # Single day surgeries
    
    # Call eligibility API
    try:
        if not client or not api_core:
            continue
        
        eligibility_data = api_core.get_eligibility_super_connector(
            client, payer_id, provider_last_name, 'MemberIDDateOfBirth', dob, member_id, npi,
            service_start=service_start, service_end=service_end
        )
        
        if not eligibility_data:
            continue
        
        # Extract insurance info using shared utility function
        if collect_insurance_type_mapping_from_response is not None:
            mapping_entry = collect_insurance_type_mapping_from_response(eligibility_data)
            if mapping_entry:
                # Merge with existing values if code already exists
                for api_code, unique_values in mapping_entry.items():
                    if api_code in api_code_mapping:
                        existing = api_code_mapping[api_code]
                        existing_set = set(existing)
                        for val in unique_values:
                            if val not in existing_set:
                                existing.append(val)
                    else:
                        api_code_mapping[api_code] = unique_values
    except Exception as e:
        # Skip on error, continue processing
        continue

print("\n" + "=" * 80)
print("API INSURANCE TYPE CODE TO DESCRIPTION MAPPING")
print("=" * 80)
print("\nAPI_TO_SBR_MAPPING = {")
for code, values in sorted(api_code_mapping.items()):
    # Print as a list with all field values
    values_str = ', '.join(["'{}'".format(v) for v in values])
    print("    '{}': [{}],".format(code, values_str))
print("}")
print("\nTotal unique mappings: {}".format(len(api_code_mapping)))

# Optionally print reference table from config.json
print("\n" + "=" * 80)
print("SBR-COMPATIBLE CODES REFERENCE (from config.json)")
print("=" * 80)
try:
    medi = config.get('MediLink_Config', {})
    insurance_options = medi.get('insurance_options', {})
    if insurance_options:
        print("\nSBR_CODES = {")
        for code, desc in sorted(insurance_options.items()):
            print("    '{}': '{}',".format(code, desc))
        print("}")
except Exception:
    print("Could not load insurance_options from config.json")

print("\n" + "=" * 80)

