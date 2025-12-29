#MediBot_Preprocessor.py
import os, re, sys, argparse
from collections import OrderedDict # so that the field_mapping stays in order.
import time # Added for timing instrumentation

# Add parent directory of the project to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_dir)

# Use core utilities for standardized imports
from MediCafe.core_utils import (
    import_medibot_module,
    get_config_loader_with_fallback
)

# Initialize configuration loader with fallback
MediLink_ConfigLoader = get_config_loader_with_fallback()

# Import MediBot modules using centralized import functions
MediBot_Crosswalk_Library = import_medibot_module('MediBot_Crosswalk_Library')
MediBot_Preprocessor_lib = import_medibot_module('MediBot_Preprocessor_lib')

# Initialize API client variables
get_api_client = None

try:
    # Try to use the factory for enhanced features (circuit breakers, shared clients, etc.)
    from MediCafe.api_factory import APIClientFactory
    factory = APIClientFactory()
    get_api_client = lambda: factory.get_shared_client()  # Use shared client for token caching benefits
    MediLink_ConfigLoader.log("MediBot_Preprocessor using API Factory with shared client", level="INFO")
except ImportError as e:
    # Fallback to basic API client
    try:
        from MediCafe.core_utils import get_api_client
        MediLink_ConfigLoader.log("MediBot_Preprocessor using fallback API client", level="WARNING")
    except ImportError as e2:
        # Make API client optional - don't log warning for now
        get_api_client = None

# Configuration will be loaded when needed
_config_cache = None
_crosswalk_cache = None

def _get_config():
    """Get configuration, loading it if not already cached."""
    global _config_cache, _crosswalk_cache
    if _config_cache is None:
        _config_cache, _crosswalk_cache = MediBot_Preprocessor_lib.get_cached_configuration()
    return _config_cache, _crosswalk_cache

# CSV Preprocessor built for Carol
def preprocess_csv_data(csv_data, crosswalk):
    try:
        # Add the "Ins1 Insurance ID" and "Default Diagnosis #1" columns to the CSV data.
        # This initializes the columns with empty values for each row.
        columns_to_add = ['Ins1 Insurance ID', 'Default Diagnosis #1', 'Procedure Code', 'Minutes', 'Amount']
        MediLink_ConfigLoader.log("CSV Pre-processor: Initializing empty columns to the CSV data...", level="INFO")
        MediBot_Preprocessor_lib.add_columns(csv_data, columns_to_add)
        
        # Filter out rows without a Patient ID and rows where the Primary Insurance
        # is 'AETNA', 'AETNA MEDICARE', or 'HUMANA MED HMO'.
        MediLink_ConfigLoader.log("CSV Pre-processor: Filtering out missing Patient IDs and 'AETNA', 'AETNA MEDICARE', or 'HUMANA MED HMO'...", level="INFO")
        MediBot_Preprocessor_lib.filter_rows(csv_data)

        # Clean and validate Patient SSN fields
        MediLink_ConfigLoader.log("CSV Pre-processor: Cleaning and validating Patient SSN fields...", level="INFO")
        MediBot_Preprocessor_lib.clean_patient_ssn(csv_data)
        
        # Convert 'Surgery Date' from string format to datetime objects for sorting purposes.
        # TIMING: Start surgery date conversion timing (SLOW OPERATION)
        date_start_time = time.time()
        print("Starting surgery date conversion at: {}".format(time.strftime("%H:%M:%S")))
        MediLink_ConfigLoader.log("Starting surgery date conversion at: {}".format(time.strftime("%H:%M:%S")), level="INFO")
        
        MediBot_Preprocessor_lib.convert_surgery_date(csv_data)
        
        # TIMING: End surgery date conversion timing
        date_end_time = time.time()
        date_duration = date_end_time - date_start_time
        print("Surgery date conversion completed at: {} (Duration: {:.2f} seconds)".format(
            time.strftime("%H:%M:%S"), date_duration))
        MediLink_ConfigLoader.log("Surgery date conversion completed at: {} (Duration: {:.2f} seconds)".format(
            time.strftime("%H:%M:%S"), date_duration), level="INFO")
        
        # Update the CSV data to include only unique patient records.
        # Re-sort the CSV data after deduplication to ensure the correct order.
        # Sort the patients by 'Surgery Date' and then by 'Patient Last' name alphabetically.
        # Deduplicate patient records based on Patient ID, keeping the entry with the earliest surgery date.
        MediLink_ConfigLoader.log("CSV Pre-processor: Sorting and de-duplicating patient records...", level="INFO")
        MediBot_Preprocessor_lib.sort_and_deduplicate(csv_data) 
        # NOTE: Multiple surgery dates are now preserved (not deleted) in the '_all_surgery_dates' field for each patient.
        # The sort_and_deduplicate() function stores all surgery dates per patient, allowing MediBot to process 
        # entries for each date. See create_patient_entries_from_row() in MediBot.py for how multiple dates are handled.
        # TODO: Billing status tracking is not yet implemented. MediLink_Scheduler needs to persist a dictionary 
        # that tracks which patients have been billed and their billing/claims status. Currently, the system only 
        # checks if a patient exists in MAPAT.MED, but doesn't track which dates of service have been billed.
        # Related TODO: See MediBot.py:895 for incomplete logic handling existing patients who need new charges added.
        # Eventually, we really want to get out of Medisoft... 
        
        # Batch field operations: Convert dates, combine names/addresses, and apply replacements
        MediLink_ConfigLoader.log("CSV Pre-processor: Constructing Patient Name and Address for Medisoft...", level="INFO")
        MediBot_Preprocessor_lib.combine_fields(csv_data)
        
        # Retrieve replacement values from the crosswalk.
        # Iterate over each key-value pair in the replacements dictionary and replace the old value
        # with the new value in the corresponding fields of each row.
        MediLink_ConfigLoader.log("CSV Pre-processor: Applying mandatory replacements per Crosswalk...", level="INFO")
        MediBot_Preprocessor_lib.apply_replacements(csv_data, crosswalk)
        
        # Update the "Ins1 Insurance ID" column based on the crosswalk and the "Ins1 Payer ID" column for each row.
        # If the Payer ID is not found in the crosswalk, create a placeholder entry in the crosswalk and mark the row for review.
        MediLink_ConfigLoader.log("CSV Pre-processor: Populating 'Ins1 Insurance ID' based on Crosswalk...", level="INFO")
        config, _ = _get_config()
        
        # TIMING: Start insurance ID update timing (SLOWEST OPERATION)
        insurance_start_time = time.time()
        print("Starting insurance ID updates at: {}".format(time.strftime("%H:%M:%S")))
        MediLink_ConfigLoader.log("Starting insurance ID updates at: {}".format(time.strftime("%H:%M:%S")), level="INFO")
        
        MediBot_Preprocessor_lib.update_insurance_ids(csv_data, config, crosswalk)
        
        # TIMING: End insurance ID update timing
        insurance_end_time = time.time()
        insurance_duration = insurance_end_time - insurance_start_time
        print("Insurance ID updates completed at: {} (Duration: {:.2f} seconds)".format(
            time.strftime("%H:%M:%S"), insurance_duration))
        MediLink_ConfigLoader.log("Insurance ID updates completed at: {} (Duration: {:.2f} seconds)".format(
            time.strftime("%H:%M:%S"), insurance_duration), level="INFO")
        
        # Enrich the "Default Diagnosis #1" column based on the parsed docx for each row.
        # This needs to handle the different patient dates correctly so we get the right diagnosis code assigned to the right patient on the right date of service.
        # Currently, we've deleted all the second date entries for patients. As long as they exist in the system, they're just deleted.
        MediLink_ConfigLoader.log("CSV Pre-processor: Populating 'Default Diagnosis #1' based on Surgery Schedule and Crosswalk...", level="INFO")
        print("Parsing Surgery Schedules...") # This step takes a while.
        MediBot_Preprocessor_lib.update_diagnosis_codes(csv_data)
        
        # Enrich the procedure code column based on the diagnosis code for each patient. 
        # MediLink_ConfigLoader.log("CSV Pre-processor: Populating 'Procedure Code' based on Crosswalk...", level="INFO")
        # MediBot_Preprocessor_lib.update_procedure_codes(csv_data, crosswalk)
        
        # Convert all text fields to uppercase
        MediLink_ConfigLoader.log("CSV Pre-processor: Converting all text fields to uppercase...", level="INFO")
        print("Converting all text fields to uppercase...")
        MediBot_Preprocessor_lib.capitalize_all_fields(csv_data)
    
    except Exception as e:
        message = "An error occurred while pre-processing CSV data. Please repair the CSV directly and try again: {}".format(e)
        MediLink_ConfigLoader.log(message, level="ERROR")
        print(message)

# Global caches for existing patient IDs to avoid repeated file I/O
_medicare_patients_cache = None
_private_patients_cache = None
_current_cache = None  # Points to the active cache based on user selection

def load_existing_patient_ids(MAPAT_MED_PATH):
    """
    Load all existing patient IDs from MAPAT.MED file into memory cache.
    
    Args:
        MAPAT_MED_PATH: Path to the MAPAT.MED file
        
    Returns:
        dict: {patient_id: patient_name} mapping of all existing patients
    """
    patient_cache = {}
    
    if not MAPAT_MED_PATH:
        MediLink_ConfigLoader.log("MAPAT.MED path not provided - returning empty cache", level="WARNING")
        return patient_cache
    
    try:
        MediLink_ConfigLoader.log("Loading patient cache from: {}".format(MAPAT_MED_PATH), level="INFO")
        with open(MAPAT_MED_PATH, 'r') as file:
            next(file)  # Skip header row
            for line in file:
                if line.startswith("0"):  # 1 is a flag for a deleted record so it would need to be re-entered.
                    patient_id = line[194:202].strip()  # Extract Patient ID (Columns 195-202)
                    patient_name = line[9:39].strip()  # Extract Patient Name (Columns 10-39)
                    
                    if patient_id:  # Only cache non-empty patient IDs
                        patient_cache[patient_id] = patient_name
        
        MediLink_ConfigLoader.log("Loaded {} patients into cache from {}".format(len(patient_cache), MAPAT_MED_PATH), level="INFO")
        
    except FileNotFoundError:
        MediLink_ConfigLoader.log("MAPAT.med was not found at location: {}".format(MAPAT_MED_PATH), level="WARNING")
        print("MAPAT.med was not found at location: {}".format(MAPAT_MED_PATH))
        print("Continuing with empty patient cache...")
    except Exception as e:
        MediLink_ConfigLoader.log("Error loading patient cache: {}".format(e), level="ERROR")
        print("Error loading patient cache: {}".format(e))
    
    return patient_cache

def set_patient_caches(medicare_cache, private_cache):
    """
    Store both patient caches for later use based on user selection.
    
    Args:
        medicare_cache: Dict of Medicare patient IDs and names
        private_cache: Dict of Private patient IDs and names
    """
    global _medicare_patients_cache, _private_patients_cache
    _medicare_patients_cache = medicare_cache
    _private_patients_cache = private_cache

def select_active_cache(is_medicare):
    """
    Select which patient cache to use based on Medicare selection.
    
    Args:
        is_medicare: True for Medicare patients, False for Private patients
    """
    global _current_cache, _medicare_patients_cache, _private_patients_cache
    _current_cache = _medicare_patients_cache if is_medicare else _private_patients_cache

def check_existing_patients(selected_patient_ids, MAPAT_MED_PATH):
    """
    Check which selected patients already exist in the system using cached data.
    This is now much faster as it uses in-memory cache instead of file I/O.
    
    Args:
        selected_patient_ids: List of patient IDs to check
        MAPAT_MED_PATH: Path to MAPAT.MED file (for fallback if cache not available)
        
    Returns:
        tuple: (existing_patients, patients_to_process)
    """
    global _current_cache
    
    # Use current cache if available, otherwise fallback to loading file
    if _current_cache is not None:
        existing_patients_dict = _current_cache
    else:
        # Fallback: load from file if cache not available
        existing_patients_dict = load_existing_patient_ids(MAPAT_MED_PATH)
    
    existing_patients = []
    patients_to_process = []
    
    # Use cached data for O(1) lookups instead of file I/O
    for patient_id in selected_patient_ids:
        if patient_id in existing_patients_dict:
            patient_name = existing_patients_dict[patient_id]
            existing_patients.append((patient_id, patient_name))
        else:
            patients_to_process.append(patient_id)
    
    return existing_patients, patients_to_process

def intake_scan(csv_headers, field_mapping):
    identified_fields = OrderedDict()
    missing_fields_warnings = []
    config, _ = _get_config()
    required_fields = config["required_fields"]
    
    MediLink_ConfigLoader.log("Intake Scan - Field Mapping: {}".format(field_mapping), level="DEBUG")
    MediLink_ConfigLoader.log("Intake Scan - CSV Headers: {}".format(csv_headers), level="DEBUG")
    
    # Pre-compile regex patterns for better performance
    compiled_patterns = {}
    for medisoft_field, patterns in field_mapping.items():
        compiled_patterns[medisoft_field] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    # Pre-compile the alphanumeric regex for policy number validation
    alphanumeric_pattern = re.compile("^[a-zA-Z0-9]*$")
    
    # Iterate over the Medisoft fields defined in field_mapping
    for medisoft_field in field_mapping.keys():
        matched = False
        for pattern in compiled_patterns[medisoft_field]:
            # Use early termination - find first match and break
            for header in csv_headers:
                if pattern.search(header):
                    identified_fields[header] = medisoft_field
                    matched = True
                    break
            if matched:
                break
        else:
            # Check if the missing field is a required field before appending the warning
            if medisoft_field in required_fields:
                missing_fields_warnings.append("WARNING: No matching CSV header found for Medisoft field '{0}'".format(medisoft_field))
   
    # CSV Integrity Checks
    # Check for blank or partially blank CSV
    if len(csv_headers) == 0 or all(header == "" for header in csv_headers):
        missing_fields_warnings.append("WARNING: The CSV appears to be blank or contains only headers without data.")

    # Display the identified fields and missing fields warnings
    #MediLink_ConfigLoader.log("The following Medisoft fields have been identified in the CSV:")
    #for header, medisoft_field in identified_fields.items():
    #    MediLink_ConfigLoader.log("{} (CSV header: {})".format(medisoft_field, header))

    # This section interprets the information from identified_fields and decides if there are significant issues.
    # e.g. If the 'Street' value:key is 'Address', then any warnings about City, State, Zip can be ignored.
    for header, field in identified_fields.items():
        # Insurance Policy Numbers should be all alphanumeric with no other characters. 
        if 'Insurance Policy Number' in field:
            policy_number = identified_fields.get(header)
            MediLink_ConfigLoader.log("Checking Insurance Policy Number '{}' for alphanumeric characters.".format(policy_number), level="DEBUG")
            if not alphanumeric_pattern.match(policy_number):
                missing_fields_warnings.append("WARNING: Insurance Policy Number '{}' contains invalid characters.".format(policy_number))
                MediLink_ConfigLoader.log("Insurance Policy Number '{}' contains invalid characters.".format(policy_number), level="WARNING")
        # Additional checks can be added as needed for other fields
    
    if missing_fields_warnings:
        MediLink_ConfigLoader.log("\nSome required fields could not be matched:", level="INFO")
        for warning in missing_fields_warnings:
            MediLink_ConfigLoader.log(warning, level="WARNING")

    return identified_fields

def main():
    parser = argparse.ArgumentParser(description='Run MediLink Data Management Tasks')
    parser.add_argument('--update-crosswalk', action='store_true',
                        help='Run the crosswalk update independently')
    parser.add_argument('--init-crosswalk', action='store_true',
                        help='Initialize the crosswalk using historical data from MAPAT and Carols CSV')
    parser.add_argument('--load-csv', action='store_true',
                        help='Load and process CSV data')
    parser.add_argument('--preprocess-csv', action='store_true',
                        help='Preprocess CSV data based on specific rules')
    parser.add_argument('--open-csv', action='store_true',
                        help='Open CSV for manual editing')

    args = parser.parse_args()

    # If no arguments provided, print usage instructions
    if not any(vars(args).values()):
        parser.print_help()
        return

    # Load configuration only when needed
    if args.update_crosswalk or args.init_crosswalk or args.load_csv or args.preprocess_csv or args.open_csv:
        config, crosswalk = MediBot_Preprocessor_lib.get_cached_configuration()
    
    # Initialize API client only when needed
    if args.update_crosswalk or args.init_crosswalk:
        if get_api_client is not None:
            client = get_api_client()
        else:
            print("Error: No API client available")
            client = None
    
    if args.update_crosswalk:
        print("Updating the crosswalk...")
        MediBot_Crosswalk_Library.crosswalk_update(client, config, crosswalk)

    if args.init_crosswalk:
        MediBot_Crosswalk_Library.initialize_crosswalk_from_mapat(client, config, crosswalk)

    if args.load_csv:
        print("Loading CSV data...")
        csv_data = MediBot_Preprocessor_lib.load_csv_data(config['CSV_FILE_PATH'])
        print("Loaded {} records from the CSV.".format(len(csv_data)))

    if args.preprocess_csv:
        if 'csv_data' in locals():
            print("Preprocessing CSV data...")
            preprocess_csv_data(csv_data, crosswalk)
        else:
            print("Error: CSV data needs to be loaded before preprocessing. Use --load-csv.")
    
    if args.open_csv:
        print("Opening CSV for editing...")
        MediBot_Preprocessor_lib.open_csv_for_editing(config['CSV_FILE_PATH'])

if __name__ == '__main__':
    main()