# MediLink_PatientProcessor.py
# Patient data processing and endpoint determination functions
# Extracted from MediLink.py for better modularity and maintainability

import os, sys, time

# Use core utilities for standardized imports
from MediCafe.core_utils import get_shared_config_loader, import_medibot_module, extract_medilink_config
MediLink_ConfigLoader = get_shared_config_loader()

# Import shared display utilities
try:
    from MediLink.MediLink_Display_Utils import print_error as _print_error, print_warning as _print_warning
except Exception:
    # Fallback if import fails
    def _print_error(message, sleep_seconds=3):
        try:
            print("\n" + "="*60)
            print("ERROR: {}".format(str(message) if message else ""))
            print("="*60)
            time.sleep(max(0, float(sleep_seconds)) if sleep_seconds else 3)
        except Exception:
            pass
    def _print_warning(message, sleep_seconds=3):
        try:
            print("\n" + "="*60)
            print("WARNING: {}".format(str(message) if message else ""))
            print("="*60)
            time.sleep(max(0, float(sleep_seconds)) if sleep_seconds else 3)
        except Exception:
            pass

# Import insurance type cache utilities
try:
    from MediLink.insurance_type_cache import get_csv_dir_from_config, lookup as cache_lookup
    MediLink_ConfigLoader.log("Insurance type cache module imported successfully", level="INFO")
except Exception as e:
    get_csv_dir_from_config = None
    cache_lookup = None
    MediLink_ConfigLoader.log("Insurance type cache module import failed: {}".format(str(e)), level="WARNING")

import MediLink_DataMgmt
import MediLink_Display_Utils

# Optional import for submission index (duplicate detection)
try:
    from MediCafe.submission_index import compute_claim_key, find_by_claim_key
except Exception:
    compute_claim_key = None
    find_by_claim_key = None

# Add parent directory access for MediBot import
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.append(project_dir)

# Use dynamic import to avoid circular dependencies
# XP/Python34 Compatibility: Enhanced error handling with verbose output
def _get_load_insurance_function():
    """Dynamically import load_insurance_data_from_mains to avoid circular imports."""
    try:
        MediBot_Preprocessor_lib = import_medibot_module('MediBot_Preprocessor_lib')
        if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'log'):
            MediLink_ConfigLoader.log("Successfully imported MediBot_Preprocessor_lib via core_utils", level="DEBUG")
        if MediBot_Preprocessor_lib and hasattr(MediBot_Preprocessor_lib, 'load_insurance_data_from_mains'):
            func = MediBot_Preprocessor_lib.load_insurance_data_from_mains
            if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'log'):
                MediLink_ConfigLoader.log("Successfully accessed load_insurance_data_from_mains function", level="DEBUG")
            return func
        else:
            error_msg = "MediBot_Preprocessor_lib imported but load_insurance_data_from_mains attribute missing"
            if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'log'):
                MediLink_ConfigLoader.log(error_msg, level="WARNING")
            print("Warning: {}".format(error_msg))
            return None
    except Exception as e:
        error_msg = "Unexpected error accessing MediBot_Preprocessor_lib: {}".format(str(e))
        if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'log'):
            MediLink_ConfigLoader.log(error_msg, level="ERROR")
        print("Error: {}".format(error_msg))
        return None
    except AttributeError as e:
        error_msg = "AttributeError accessing load_insurance_data_from_mains: {}".format(str(e))
        if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'log'):
            MediLink_ConfigLoader.log(error_msg, level="WARNING")
        print("Warning: {}".format(error_msg))
        return None
    except Exception as e:
        error_msg = "Unexpected error accessing MediBot_Preprocessor_lib: {}".format(str(e))
        if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'log'):
            MediLink_ConfigLoader.log(error_msg, level="ERROR")
        print("Error: {}".format(error_msg))
        return None

load_insurance_data_from_mains = _get_load_insurance_function()

# XP Compatibility: Add fallback function if import fails
if load_insurance_data_from_mains is None:
    def load_insurance_data_from_mains_fallback(config):
        """
        Fallback function for load_insurance_data_from_mains when MediBot_Preprocessor_lib is not available.
        Returns empty dictionary to prevent AttributeError.
        """
        print("Warning: load_insurance_data_from_mains not available. Using empty insurance mapping.")
        return {}
    
    load_insurance_data_from_mains = load_insurance_data_from_mains_fallback


def collect_detailed_patient_data(selected_files, config, crosswalk):
    """
    Collects detailed patient data from the selected files.
    
    DATA FLOW CLARIFICATION:
    This function processes fixed-width files through extract_and_suggest_endpoint(),
    which creates data structures with:
    - 'patient_id' field (sourced from 'CHART' field) - used for display/other purposes
    - 'patid' field (sourced from 'PATID' field) - used for cache matching with CSV "Patient ID #2"
    
    This is DIFFERENT from MediBot's parse_z_dat() flow which uses 'PATID' field.
    
    :param selected_files: List of selected file paths.
    :param config: Configuration settings loaded from a JSON file.
    :param crosswalk: Crosswalk data for mapping purposes.
    :return: A list of detailed patient data with 'patient_id' and 'patid' fields populated.
    """
    detailed_patient_data = []
    
    # Retrieve insurance options with codes and descriptions
    try:
        medi = extract_medilink_config(config)
        insurance_options = medi.get('insurance_options')
    except Exception:
        insurance_options = None
    
    for file_path in selected_files:
        # IMPORTANT: extract_and_suggest_endpoint creates data with both:
        # - 'patient_id' field (from 'CHART' field) - for display/other uses
        # - 'patid' field (from 'PATID' field) - for cache matching
        detailed_data = extract_and_suggest_endpoint(file_path, config, crosswalk)
        detailed_patient_data.extend(detailed_data)  # Accumulate detailed data for processing
        
    # Enrich the detailed patient data with insurance type
    # NOTE: This receives data from extract_and_suggest_endpoint with 'patient_id' and 'patid' fields
    detailed_patient_data = enrich_with_insurance_type(detailed_patient_data, insurance_options)
    
    # Overlay API-derived insurance type codes from cache (API > MAN > DEF)
    MediLink_ConfigLoader.log("Starting cache lookup overlay for {} patients".format(len(detailed_patient_data)), level="INFO")
    try:
        if cache_lookup is None:
            MediLink_ConfigLoader.log("Cache lookup function not available. Check insurance_type_cache module import.", level="INFO")
            _print_error("Cache lookup function not available. Check insurance_type_cache module import.")
        elif get_csv_dir_from_config is None:
            MediLink_ConfigLoader.log("CSV directory resolver not available", level="INFO")
            _print_error("CSV directory resolver not available.")
        else:
            csv_dir = get_csv_dir_from_config(config) if get_csv_dir_from_config else ''
            MediLink_ConfigLoader.log("Cache directory resolved: '{}'".format(csv_dir), level="INFO")
            if not csv_dir:
                MediLink_ConfigLoader.log("CSV directory is empty. Cache lookup skipped. Check CSV_FILE_PATH in config.json.", level="INFO")
                _print_error("CSV directory is empty. Cache lookup skipped. Check CSV_FILE_PATH in config.json.")
            else:
                lookup_count = 0
                success_count = 0
                miss_count = 0
                for idx, data in enumerate(detailed_patient_data):
                    try:
                        # Use PATID (5-digit patient ID) for cache matching - matches CSV "Patient ID #2"
                        patid = data.get('patid', '')
                        if not patid:
                            MediLink_ConfigLoader.log("PATID missing for patient {}, skipping cache lookup".format(idx + 1), level="WARNING")
                            continue
                        service_date_iso = data.get('surgery_date_iso', '')
                        lookup_count += 1
                        # Log lookup attempt at DEBUG level (individual lookups are verbose)
                        MediLink_ConfigLoader.log("Cache lookup for patid='{}' with service_date='{}'".format(
                            patid, service_date_iso or 'none'), level="DEBUG")
                        api_code = cache_lookup(patient_id=patid, csv_dir=csv_dir, service_date=service_date_iso)
                        if api_code:
                            success_count += 1
                            MediLink_ConfigLoader.log("Cache lookup SUCCESS for patid='{}': code='{}'".format(patid, api_code), level="DEBUG")
                            data['insurance_type'] = api_code
                            data['insurance_type_source'] = 'API'
                        else:
                            miss_count += 1
                            MediLink_ConfigLoader.log("Cache lookup MISS for patid='{}' (not found in cache)".format(patid), level="DEBUG")
                    except Exception as e:
                        MediLink_ConfigLoader.log("Cache lookup exception for patient {}: {}".format(idx + 1, str(e)), level="WARNING")
                        continue
                MediLink_ConfigLoader.log("Cache lookup complete: {} success(es), {} miss(es) out of {} patients".format(
                    success_count, miss_count, lookup_count), level="INFO")
    except Exception as e:
        MediLink_ConfigLoader.log("Insurance type cache overlay error: {}".format(str(e)), level="ERROR")
    
    # Display summaries and provide an option for bulk edit
    MediLink_Display_Utils.display_patient_summaries(detailed_patient_data, config)

    return detailed_patient_data


def enrich_with_insurance_type(detailed_patient_data, patient_insurance_type_mapping=None):
    """
    Enriches the detailed patient data with insurance type based on patient ID.
    Enhanced with optional API integration and comprehensive logging.

    DATA FLOW CLARIFICATION:
    This function receives data from collect_detailed_patient_data() -> extract_and_suggest_endpoint().
    The data contains both 'patient_id' (from 'CHART') and 'patid' (from 'PATID') fields.
    This function uses 'patient_id' for legacy insurance type mapping.
    
    IMPORTANT: Do not confuse with MediBot's parse_z_dat() flow which uses 'PATID'.
    MediLink flow: fixed-width files -> extract_and_suggest_endpoint() -> 'patient_id' (CHART) + 'patid' (PATID)
    MediBot flow: Z.dat files -> parse_z_dat() -> 'PATID' field

    Parameters:
    - detailed_patient_data: List of dictionaries containing detailed patient data with 'patient_id' and 'patid' fields.
    - patient_insurance_mapping: Dictionary mapping patient IDs to their insurance types.

    Returns:
    - Enriched detailed patient data with insurance type added.
    
    TODO: Implement a function to provide `patient_insurance_mapping` from a reliable source.
    This is going to be coming soon as an API feature from United Healthcare. We'll be able to get insurance types directly via their API.
    So, while we won't be able to do it for all payerIDs, we'll be able to do it for the ones that are supported by UHC.
    So, we'll need a way to augment the associated menu here so that the user is aware of which insurance types are already pulled from
    UHC and which ones are not yet supported so they know which ones they need to edit. It is possible that we may want to isolate the 
    patient data that is already pulled from UHC so that the user can see which ones are already using the enriched data.

    Integration proposal:
    - Use MediCafe.api_core APIClient to fetch insurance types where endpoint supports it; cache results.
    - Merge API-derived types into patient_insurance_mapping with explicit provenance markers.
    - Fallback: retain CSV/crosswalk-derived types when API not available.
    - UI: indicate which entries are API-enriched vs manual.
    """
    # Enhanced mode check with graceful degradation
    enhanced_mode = False
    
    # XP/Python34 Compatibility: Enhanced error handling with verbose output
    try:
        from MediLink import MediLink_insurance_utils
        get_feature_flag = getattr(MediLink_insurance_utils, 'get_feature_flag', None)
        validate_insurance_type_from_config = getattr(MediLink_insurance_utils, 'validate_insurance_type_from_config', None)
        enhanced_mode = get_feature_flag('enhanced_insurance_enrichment', default=False) if get_feature_flag else False
        MediLink_ConfigLoader.log("Insurance enhancement utilities loaded successfully", level="DEBUG")
    except ImportError as e:
        MediLink_ConfigLoader.log("Insurance utils not available: {}. Using legacy mode.".format(str(e)), level="INFO")
        print("Info: Using legacy insurance processing mode due to: {}".format(str(e)))
        enhanced_mode = False
    except Exception as e:
        MediLink_ConfigLoader.log("Error initializing insurance enhancements: {}. Using legacy mode.".format(str(e)), level="ERROR")
        print("Warning: Insurance enhancement error ({}), using legacy mode".format(str(e)))
        enhanced_mode = False
    
    if patient_insurance_type_mapping is None:
        MediLink_ConfigLoader.log("No Patient:Insurance-Type mapping available.", level="INFO")
        patient_insurance_type_mapping = {}
    
    # Enhanced mode with validation
    if enhanced_mode:
        MediLink_ConfigLoader.log("Using enhanced insurance type enrichment", level="INFO")
        
        for data in detailed_patient_data:
            # FIELD NAME CLARIFICATION: Use 'patient_id' field created by extract_and_suggest_endpoint()
            # This field contains the value from the 'CHART' field in the original fixed-width file
            patient_id = data.get('patient_id')
            if patient_id:
                raw_insurance_type = patient_insurance_type_mapping.get(patient_id, '12')  # Default to '12' (PPO/SBR09)
                source = 'MANUAL' if patient_id in patient_insurance_type_mapping else 'DEFAULT'
                validated_insurance_type, _ = validate_insurance_type_from_config(
                    raw_insurance_type, patient_id, source=source, strict_mode=True)
                data['insurance_type'] = validated_insurance_type
                data['insurance_type_source'] = source
            else:
                # Handle case where patient_id is missing or empty
                MediLink_ConfigLoader.log("No patient_id found in data record", level="WARNING")
                data['insurance_type'] = '12'  # SBR09 default PPO
                data['insurance_type_source'] = 'DEFAULT_FALLBACK'
        
    else:
        # Legacy mode (preserve existing behavior exactly) + always set source
        MediLink_ConfigLoader.log("Using legacy insurance type enrichment", level="INFO")
        for data in detailed_patient_data:
            # FIELD NAME CLARIFICATION: Use 'patient_id' field created by extract_and_suggest_endpoint()
            # This field contains the value from the 'CHART' field in the original fixed-width file
            patient_id = data.get('patient_id')
            if patient_id:
                insurance_type = patient_insurance_type_mapping.get(patient_id, '12')  # Default to '12' (PPO/SBR09)
                data['insurance_type'] = insurance_type
                # Mirror enhanced mode semantics for source
                data['insurance_type_source'] = 'MANUAL' if patient_id in patient_insurance_type_mapping else 'DEFAULT'
            else:
                # Handle case where patient_id is missing or empty
                MediLink_ConfigLoader.log("No patient_id found in data record", level="WARNING")
                insurance_type = '12'  # Default when no patient ID available
                data['insurance_type'] = insurance_type
                data['insurance_type_source'] = 'DEFAULT_FALLBACK'
    
    return detailed_patient_data


def _normalize_dos_to_iso(mm_dd_yy):
    """Convert date like 'MM-DD-YY' to 'YYYY-MM-DD' safely."""
    try:
        parts = mm_dd_yy.split('-')
        if len(parts) == 3:
            mm, dd, yy = parts
            # Assume 20xx for YY < 50 else 19xx (adjust as needed)
            century = '20' if int(yy) < 50 else '19'
            return "{}-{}-{}".format(century + yy, mm.zfill(2), dd.zfill(2))
    except Exception:
        pass
    return mm_dd_yy


def extract_and_suggest_endpoint(file_path, config, crosswalk):
    """
    Reads a fixed-width file, extracts file details including surgery date, patient ID, 
    patient name, primary insurance, and other necessary details for each record. It suggests 
    an endpoint based on insurance provider information found in the crosswalk and prepares 
    detailed patient data for processing.
    
    DATA FLOW CLARIFICATION:
    This function is the PRIMARY data source for MediLink patient processing.
    It creates both 'patient_id' and 'patid' fields from fixed-width files.
    
    IMPORTANT: This is DIFFERENT from MediBot's parse_z_dat() which extracts 'PATID'.
    
    Field mapping for MediLink flow:
    - Fixed-width file 'CHART' field -> detailed_data['patient_id'] (for display/other uses)
    - Fixed-width file 'PATID' field -> detailed_data['patid'] (for cache matching with CSV "Patient ID #2")
    - The 'patient_id' is used by enrich_with_insurance_type() for legacy mapping
    - The 'patid' is used by cache lookup for API-derived insurance types
    
    Parameters:
    - file_path: Path to the fixed-width file.
    - crosswalk: Crosswalk dictionary loaded from a JSON file.

    Returns:
    - A comprehensive data structure retaining detailed patient claim details needed for processing,
      including new key-value pairs for file path, surgery date, patient name, and primary insurance.
    """
    detailed_patient_data = []
    
    # Load insurance data from MAINS to create a mapping from insurance names to their respective IDs
    if load_insurance_data_from_mains is None:
        MediLink_ConfigLoader.log("load_insurance_data_from_mains function not available. Using empty insurance mapping.", level="WARNING")
        insurance_to_id = {}
    else:
        insurance_to_id = load_insurance_data_from_mains(config)
        MediLink_ConfigLoader.log("Insurance data loaded from MAINS. {} insurance providers found.".format(len(insurance_to_id)), level="INFO")

    # Resolve receiptsRoot for duplicate detection (optional)
    try:
        medi_cfg = extract_medilink_config(config)
        receipts_root = medi_cfg.get('local_claims_path', None)
    except Exception:
        receipts_root = None

    for personal_info, insurance_info, service_info, service_info_2, service_info_3 in MediLink_DataMgmt.read_fixed_width_data(file_path):
        # Parse reserved 5-line record: 3 active lines + 2 reserved for future expansion
        try:
            cfg_for_parse = extract_medilink_config(config)
        except Exception:
            cfg_for_parse = config
        parsed_data = MediLink_DataMgmt.parse_fixed_width_data(personal_info, insurance_info, service_info, service_info_2, service_info_3, cfg_for_parse)
        
        primary_insurance = parsed_data.get('INAME')
        primary_procedure_code = parsed_data.get('CODEA')
               
        # Retrieve the insurance ID associated with the primary insurance
        insurance_id = insurance_to_id.get(primary_insurance)
        MediLink_ConfigLoader.log("Primary insurance ID retrieved for '{}': {}".format(primary_insurance, insurance_id))

        # Use insurance ID to retrieve the payer ID(s) associated with the insurance
        payer_ids = []
        if insurance_id:
            for payer_id, payer_data in crosswalk.get('payer_id', {}).items():
                medisoft_ids = [str(id) for id in payer_data.get('medisoft_id', [])]
                if str(insurance_id) in medisoft_ids:
                    payer_ids.append(payer_id)
        if payer_ids:
            MediLink_ConfigLoader.log("Payer IDs retrieved for insurance '{}': {}".format(primary_insurance, payer_ids))
        else:
            MediLink_ConfigLoader.log("No payer IDs found for insurance '{}'".format(primary_insurance))
        
        # Find the suggested endpoint from the crosswalk based on the payer IDs
        suggested_endpoint = 'AVAILITY'  # Default endpoint if no matching payer IDs found
        if payer_ids:
            payer_id = payer_ids[0]  # Select the first payer ID
            suggested_endpoint = crosswalk['payer_id'].get(payer_id, {}).get('endpoint', 'AVAILITY')
            MediLink_ConfigLoader.log("Suggested endpoint for payer ID '{}': {}".format(payer_id, suggested_endpoint))
            
            # Validate suggested endpoint against the config
            try:
                medi = extract_medilink_config(config)
                endpoints = medi.get('endpoints', {})
            except Exception:
                endpoints = {}
            if suggested_endpoint not in endpoints:
                MediLink_ConfigLoader.log("Warning: Suggested endpoint '{}' is not defined in the configuration. Please Run MediBot. If this persists, check the crosswalk and config file.".format(suggested_endpoint), level="ERROR")
                raise ValueError("Invalid suggested endpoint: '{}' for payer ID '{}'. Please correct the configuration.".format(suggested_endpoint, payer_id))
        else:
            MediLink_ConfigLoader.log("No suggested endpoint found for payer IDs: {}".format(payer_ids))

        # Normalize DOS for keying
        raw_dos = parsed_data.get('DATE')
        iso_dos = _normalize_dos_to_iso(raw_dos) if raw_dos else ''

        # Enrich detailed patient data with additional information and suggested endpoint
        detailed_data = parsed_data.copy()  # Copy parsed_data to avoid modifying the original dictionary
        # Extract PATID (5-digit patient ID) for cache matching - this matches CSV "Patient ID #2"
        patid = parsed_data.get('PATID', '')
        if patid:
            MediLink_ConfigLoader.log("Extracted PATID='{}' from fixed-width file".format(patid), level="INFO")
            # Validate PATID format (should be 5-digit numeric)
            patid_str = str(patid).strip()
            if not (patid_str.isdigit() and len(patid_str) == 5):
                MediLink_ConfigLoader.log("WARNING: PATID '{}' has unexpected format (expected 5-digit numeric)".format(patid), level="INFO")
        else:
            MediLink_ConfigLoader.log("WARNING: PATID field is empty in fixed-width file for patient", level="INFO")
        
        detailed_data.update({
            'file_path': file_path,
            'patient_id': parsed_data.get('CHART'),  # Keep CHART for display/other uses
            'patid': patid,  # Add PATID for cache matching (matches CSV "Patient ID #2")
            'surgery_date': parsed_data.get('DATE'),
            'surgery_date_iso': iso_dos,
            'patient_name': ' '.join([parsed_data.get(key, '') for key in ['FIRST', 'MIDDLE', 'LAST']]),
            'amount': parsed_data.get('AMOUNT'),
            'primary_insurance': primary_insurance,
            'primary_procedure_code': primary_procedure_code,
            'suggested_endpoint': suggested_endpoint
        })

        # Compute claim_key (optional)
        claim_key = None
        try:
            if compute_claim_key:
                claim_key = compute_claim_key(
                    detailed_data.get('patient_id', ''),
                    '',  # payer_id not reliably known here
                    detailed_data.get('primary_insurance', ''),
                    detailed_data.get('surgery_date_iso', ''),
                    detailed_data.get('primary_procedure_code', '')
                )
                detailed_data['claim_key'] = claim_key
        except Exception:
            pass

        # Duplicate candidate flag (optional upstream detection)
        try:
            if find_by_claim_key and receipts_root and claim_key:
                existing = find_by_claim_key(receipts_root, claim_key)
                detailed_data['duplicate_candidate'] = bool(existing)
            else:
                detailed_data['duplicate_candidate'] = False
        except Exception:
            detailed_data['duplicate_candidate'] = False

        detailed_patient_data.append(detailed_data)

    # Return only the enriched detailed patient data
    return detailed_patient_data


def get_effective_endpoint(patient_data):
    """
    Returns the most appropriate endpoint for a patient based on the hierarchy:
    1. Confirmed endpoint (final decision)
    2. User preferred endpoint (if user made a change)
    3. Original suggested endpoint
    4. Default (AVAILITY)
    
    :param patient_data: Individual patient data dictionary
    :return: The effective endpoint to use for this patient
    """
    return (patient_data.get('confirmed_endpoint') or 
            patient_data.get('user_preferred_endpoint') or 
            patient_data.get('suggested_endpoint', 'AVAILITY'))