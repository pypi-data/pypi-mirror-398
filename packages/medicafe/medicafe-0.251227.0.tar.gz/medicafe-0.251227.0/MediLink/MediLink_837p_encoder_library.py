# MediLink_837p_encoder_library.py
from datetime import datetime
import sys, os
# Set up paths and use core utilities
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from MediCafe.core_utils import get_shared_config_loader
MediLink_ConfigLoader = get_shared_config_loader()
import re

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.append(project_dir)

# Import MediBot modules conditionally to avoid circular imports
# XP/Python34 Compatibility: Enhanced error handling with verbose output
MediBot_Preprocessor_lib = None
load_insurance_data_from_mains = None

try:
    from MediBot import MediBot_Preprocessor_lib
    MediLink_ConfigLoader.log("Successfully imported MediBot_Preprocessor_lib", level="DEBUG")
    
    if hasattr(MediBot_Preprocessor_lib, 'load_insurance_data_from_mains'):
        load_insurance_data_from_mains = MediBot_Preprocessor_lib.load_insurance_data_from_mains
        MediLink_ConfigLoader.log("Successfully accessed load_insurance_data_from_mains function", level="DEBUG")
    else:
        MediLink_ConfigLoader.log("Warning: MediBot_Preprocessor_lib found but load_insurance_data_from_mains attribute missing", level="WARNING")
        print("Warning: MediBot_Preprocessor_lib missing load_insurance_data_from_mains attribute")
except ImportError as e:
    MediLink_ConfigLoader.log("ImportError accessing MediBot_Preprocessor_lib: {}".format(str(e)), level="WARNING")
    print("Warning: Cannot import MediBot_Preprocessor_lib: {}".format(str(e)))
except AttributeError as e:
    MediLink_ConfigLoader.log("AttributeError accessing load_insurance_data_from_mains: {}".format(str(e)), level="WARNING")
    print("Warning: AttributeError with load_insurance_data_from_mains: {}".format(str(e)))
except Exception as e:
    MediLink_ConfigLoader.log("Unexpected error accessing MediBot_Preprocessor_lib: {}".format(str(e)), level="ERROR")
    print("Error: Unexpected error with MediBot_Preprocessor_lib: {}".format(str(e)))

# XP Compatibility: Add fallback function if import fails
if load_insurance_data_from_mains is None:
    def load_insurance_data_from_mains_fallback(config):
        """
        Fallback function for load_insurance_data_from_mains when MediBot_Preprocessor_lib is not available.
        Returns empty dictionary to prevent AttributeError.
        """
        MediLink_ConfigLoader.log("Using fallback load_insurance_data_from_mains function", level="WARNING")
        print("Warning: load_insurance_data_from_mains not available. Using empty insurance mapping.")
        return {}
    
    load_insurance_data_from_mains = load_insurance_data_from_mains_fallback

try:
    from MediBot import MediBot_Crosswalk_Library
except ImportError:
    MediBot_Crosswalk_Library = None

# Safe import for API functions - works in multiple contexts
try:
    from MediCafe import api_core as MediLink_API_v3  # [auto-migrated]
    fetch_payer_name_from_api = getattr(MediLink_API_v3, 'fetch_payer_name_from_api', None)
except ImportError:
    MediLink_API_v3 = None
    fetch_payer_name_from_api = None

# Safe import for utility functions - works in multiple contexts
try:
    import MediLink_837p_utilities
except (ImportError, SystemError):
    try:
        import MediLink_837p_utilities
    except ImportError:
        MediLink_837p_utilities = None

# Safe import for COB helper library (optional)
try:
    import MediLink_837p_cob_library as COB
except (ImportError, SystemError):
    COB = None

# Safe import for UI functions - works in multiple contexts
try:
    import MediLink_UI
except (ImportError, SystemError):
    try:
        import MediLink_UI
    except ImportError:
        MediLink_UI = None

# Import MediBot crosswalk utilities via centralized import helpers
from MediCafe.core_utils import import_medibot_module

# Resolve required functions directly at import-time using centralized helper (Py 3.4.4 friendly)
update_crosswalk_with_new_payer_id = (
    import_medibot_module('MediBot_Crosswalk_Utils', 'update_crosswalk_with_new_payer_id') or
    import_medibot_module('MediBot_Crosswalk_Library', 'update_crosswalk_with_new_payer_id')
)

update_crosswalk_with_corrected_payer_id = (
    import_medibot_module('MediBot_Crosswalk_Utils', 'update_crosswalk_with_corrected_payer_id') or
    import_medibot_module('MediBot_Crosswalk_Library', 'update_crosswalk_with_corrected_payer_id')
)

if not callable(update_crosswalk_with_new_payer_id):
    raise RuntimeError("Crosswalk update function not available (new payer id). Ensure MediBot_Crosswalk_Utils or MediBot_Crosswalk_Library is importable.")
if not callable(update_crosswalk_with_corrected_payer_id):
    raise RuntimeError("Crosswalk update function not available (corrected payer id). Ensure MediBot_Crosswalk_Utils or MediBot_Crosswalk_Library is importable.")

# Import enhanced insurance selection with fallback
# XP/Python34 Compatibility: Enhanced error handling with verbose output
try:
    from MediLink import MediLink_insurance_utils
except Exception:
    MediLink_insurance_utils = None

safe_insurance_type_selection = None
try:
    if MediLink_insurance_utils is None:
        import importlib
        MediLink_insurance_utils = importlib.import_module('MediLink.MediLink_insurance_utils')
    safe_insurance_type_selection = getattr(MediLink_insurance_utils, 'safe_insurance_type_selection', None)
    MediLink_ConfigLoader.log("Successfully imported safe_insurance_type_selection from MediLink_insurance_utils", level="DEBUG")
except ImportError as e:
    MediLink_ConfigLoader.log("ImportError importing safe_insurance_type_selection: {}".format(str(e)), level="WARNING")
    print("Warning: safe_insurance_type_selection not available: {}".format(str(e)))
    safe_insurance_type_selection = None
except Exception as e:
    MediLink_ConfigLoader.log("Unexpected error importing safe_insurance_type_selection: {}".format(str(e)), level="ERROR")
    print("Error: Unexpected error importing safe_insurance_type_selection: {}".format(str(e)))
    safe_insurance_type_selection = None

# Import display utilities
try:
    import MediLink_Display_Utils
except ImportError:
    MediLink_Display_Utils = None

# Re-export commonly used functions for backward compatibility
if MediLink_837p_utilities:
    get_output_directory = MediLink_837p_utilities.get_output_directory
    format_datetime = MediLink_837p_utilities.format_datetime
    get_user_confirmation = MediLink_837p_utilities.get_user_confirmation
    prompt_user_for_payer_id = MediLink_837p_utilities.prompt_user_for_payer_id
    convert_date_format = MediLink_837p_utilities.convert_date_format
    format_claim_number = MediLink_837p_utilities.format_claim_number
    generate_segment_counts = MediLink_837p_utilities.generate_segment_counts
    handle_validation_errors = MediLink_837p_utilities.handle_validation_errors
    winscp_validate_output_directory = MediLink_837p_utilities.winscp_validate_output_directory
    find_closest_insurance_matches = MediLink_837p_utilities.find_closest_insurance_matches
    prompt_for_insurance_selection = MediLink_837p_utilities.prompt_for_insurance_selection
    build_nm1_segment = MediLink_837p_utilities.build_nm1_segment

# -----------------------------------------------------------------------------
# Test Mode Utilities
# -----------------------------------------------------------------------------
def _is_test_mode(config):
    """
    Determine if test mode is enabled. Accepts either the full config
    (with 'MediLink_Config') or the MediLink subset config.
    """
    try:
        if isinstance(config, dict):
            # Prefer direct MediLink subset key
            if config.get('TestMode', False):
                return True
            # Fallback: full config structure
            medi = config.get('MediLink_Config', {})
            if isinstance(medi, dict) and medi.get('TestMode', False):
                return True
    except Exception:
        pass
    return False


# Constructs the ST segment for transaction set.
def create_st_segment(transaction_set_control_number):
    return "ST*837*{:04d}*005010X222A1~".format(transaction_set_control_number)

# Constructs the BHT segment based on parsed data.
def create_bht_segment(parsed_data):
    chart_number = parsed_data.get('CHART', 'UNKNOWN')
    return "BHT*0019*00*{}*{}*{}*CH~".format(
        chart_number, format_datetime(), format_datetime(format_type='time'))
    
# Constructs the HL segment for billing provider.
def create_hl_billing_provider_segment():
    return "HL*1**20*1~"

# Constructs the HL segment for subscriber [hierarchical level (HL*2)]
def create_hl_subscriber_segment():
    """
    Returns the subscriber HL segment. Kept for backward compatibility with
    MediLink_837p_encoder.py which expects this function.
    """
    return ["HL*2*1*22*0~"]

# Constructs the NM1 segment for billing provider and includes address and Tax ID.
def create_nm1_billing_provider_segment(config, endpoint):
    endpoint_config = config.get('endpoints', {}).get(endpoint.upper(), {})
    
    # Billing provider details
    billing_provider_entity_code = endpoint_config.get('billing_provider_entity_code', '85')
    billing_provider_npi_qualifier = endpoint_config.get('billing_provider_npi_qualifier', 'XX')
    # Resolve required values with TestMode-aware enforcement
    billing_provider_lastname = legacy_require_config_value(
        [config, endpoint_config],
        ['billing_provider_lastname', 'default_billing_provider_name'],
        'DEFAULT NAME',
        '2010AA Billing Provider Last Name',
        config,
        endpoint
    )
    billing_provider_firstname = config.get('billing_provider_firstname', '')
    billing_provider_npi = legacy_require_config_value(
        [endpoint_config, config],
        ['billing_provider_npi', 'default_billing_provider_npi'],
        'DEFAULT NPI',
        '2010AA Billing Provider NPI',
        config,
        endpoint
    ) # BUG This is stupid. The NPI is the same. Maybe the first and last name registration might vary by endpoint, but the NPI wont.
    
    # Determine billing_entity_type_qualifier based on the presence of billing_provider_firstname
    billing_entity_type_qualifier = '1' if billing_provider_firstname else '2' 
    
    # Construct NM1 segment for the billing provider
    nm1_segment = "NM1*{}*{}*{}*{}****{}*{}~".format(
        billing_provider_entity_code, 
        billing_entity_type_qualifier,
        billing_provider_lastname, 
        billing_provider_firstname,
        billing_provider_npi_qualifier, 
        billing_provider_npi
    )
  
    # Construct address segments
    address_segments = []
    if config.get('billing_provider_address'):
        addr = legacy_require_config_value([config], 'billing_provider_address', 'NO ADDRESS', '2010AA Billing Address', config, endpoint)
        city = legacy_require_config_value([config], 'billing_provider_city', 'NO CITY', '2010AA Billing City', config, endpoint)
        state = legacy_require_config_value([config], 'billing_provider_state', 'NO STATE', '2010AA Billing State', config, endpoint)
        zip_code = legacy_require_config_value([config], 'billing_provider_zip', 'NO ZIP', '2010AA Billing ZIP', config, endpoint)
        # N3 segment for address line
        address_segments.append("N3*{}~".format(addr))
        # N4 segment for City, State, ZIP
        address_segments.append("N4*{}*{}*{}~".format(city, state, zip_code))
    
    # Assuming Tax ID is part of the same loop, otherwise move REF segment to the correct loop
    billing_tin = legacy_require_config_value([config], 'billing_provider_tin', 'NO TAX ID', '2010AA Billing TIN', config, endpoint)
    ref_segment = "REF*EI*{}~".format(billing_tin)
    
    # Construct PRV segment if provider taxonomy is needed
    #prv_segment = ""
    #if config.get('billing_provider_taxonomy'):
    #    prv_segment = "PRV*BI*PXC*{}~".format(config.get('billing_provider_taxonomy'))
    
    segments = [nm1_segment]
    # if prv_segment:
    #     segments.append(prv_segment)
    segments.extend(address_segments)
    segments.append(ref_segment)
    
    return segments

# Constructs the NM1 segment and accompanying details for the service facility location.
def create_service_facility_location_npi_segment(config):
    """
    Constructs segments for the service facility location, including the NM1 segment for identification
    and accompanying N3 and N4 segments for address details.
    """
    facility_npi = legacy_require_config_value([config], 'service_facility_npi', 'DEFAULT FACILITY NPI', '2310C Service Facility NPI', config)
    facility_name = legacy_require_config_value([config], 'service_facility_name', 'DEFAULT FACILITY NAME', '2310C Service Facility Name', config)
    address_line_1 = legacy_require_config_value([config], 'service_facility_address', 'NO ADDRESS', '2310C Service Facility Address', config)
    city = legacy_require_config_value([config], 'service_facility_city', 'NO CITY', '2310C Service Facility City', config)
    state = legacy_require_config_value([config], 'service_facility_state', 'NO STATE', '2310C Service Facility State', config)
    zip_code = legacy_require_config_value([config], 'service_facility_zip', 'NO ZIP', '2310C Service Facility ZIP', config)

    # NM1 segment for facility identification
    nm1_segment = "NM1*77*2*{}*****XX*{}~".format(facility_name, facility_npi)
    # N3 segment for facility address
    n3_segment = "N3*{}~".format(address_line_1)
    # N4 segment for facility city, state, and ZIP
    n4_segment = "N4*{}*{}*{}~".format(city, state, zip_code)

    return [nm1_segment, n3_segment, n4_segment]

# Constructs the NM1 segment for submitter name and includes PER segment for contact information.
def create_1000A_submitter_name_segment(patient_data, config, endpoint):
    """
    Creates the 1000A submitter name segment, including the PER segment for contact information.
    """
    endpoint_config = config.get('endpoints', {}).get(endpoint.upper(), {})
    submitter_id_qualifier = endpoint_config.get('submitter_id_qualifier', '46')  # '46' for ETIN or 'XX' for NPI
    
    # Required submitter name
    submitter_name = legacy_require_config_value([endpoint_config, config], 'nm_103_value', 'DEFAULT NAME', '1000A Submitter Name', config, endpoint)
    
    # Extract payer_id from patient_data
    payer_id = patient_data.get('payer_id', '')
    
    # Check if payer_id is Florida Blue (00590 or BCBSF) and assign submitter_id accordingly
    if payer_id in ['00590', 'BCBSF']:
        submitter_id = legacy_require_config_value([endpoint_config], 'nm_109_bcbsf', 'DEFAULT BCBSF ID', '1000A Submitter ID (BCBSF)', config, endpoint)
    else:
        submitter_id = legacy_require_config_value([endpoint_config], 'nm_109_value', 'DEFAULT ID', '1000A Submitter ID', config, endpoint)
    
    # Submitter contact details (required)
    contact_name = legacy_require_config_value([config], 'submitter_name', 'NONE', '1000A Submitter Contact Name', config, endpoint)
    contact_telephone_number = legacy_require_config_value([config], 'submitter_tel', 'NONE', '1000A Submitter Contact Phone', config, endpoint)
    
    # Get submitter first name to determine entity type qualifier
    submitter_first_name = config.get('submitter_first_name', '')
    # Determine entity_type_qualifier: '1' for individual (with first name), '2' for organization
    entity_type_qualifier = '1' if submitter_first_name else '2' # Make sure that this is correct. Original default was 2.
    
    # Construct NM1 segment for the submitter
    # EDI NM1 Segment Format: NM1*41*{entity_type}*{org_name}*{first}*{middle}*{prefix}*{suffix}*{id_qualifier}*{id}~
    # For organizational submitters (entity_type=2), we use the organization name in NM1-03 and leave individual name fields blank
    # TODO: For individual submitters (entity_type=1), we would need to parse submitter_name into first/last components
    # PROPOSAL:
    # - When entity_type_qualifier == '1', split submitter_name into last/first (common formats: "Last, First" or "First Last").
    # - Populate NM1 as: NM1*41*1*{last}*{first}*****{id_qualifier}*{id}~
    # - Keep current behavior by default (org submitter). Add a feature flag to enable individual parsing once verified.
    # Example (disabled by default):
    #   last, first = parse_name_components(submitter_name)  # implement conservatively
    #   nm1_segment = "NM1*41*1*{}*{}*****{}*{}~".format(last, first, submitter_id_qualifier, submitter_id)
    # Current implementation works in production - claims are being paid successfully
    nm1_segment = "NM1*41*{}*{}*****{}*{}~".format(entity_type_qualifier, submitter_name, submitter_id_qualifier, submitter_id)
    
    # Construct PER segment for the submitter's contact information
    per_segment = "PER*IC*{}*TE*{}~".format(contact_name, contact_telephone_number)
    return [nm1_segment, per_segment]

# Constructs the NM1 segment for the receiver (1000B).
def create_1000B_receiver_name_segment(config, endpoint):
    endpoint_config = config.get('endpoints', {}).get(endpoint.upper(), {})
    receiver_entity_code = '40'
    receiver_id_qualifier = endpoint_config.get('receiver_id_qualifier', '46')
    receiver_name = legacy_require_config_value([endpoint_config], 'receiver_name', 'DEFAULT RECEIVER NAME', '1000B Receiver Name', config, endpoint)
    receiver_edi = legacy_require_config_value([endpoint_config], 'receiver_edi', 'DEFAULT EDI', '1000B Receiver EDI', config, endpoint)
    return "NM1*{entity_code}*2*{receiver_name}*****{id_qualifier}*{receiver_edi}~".format(
        entity_code=receiver_entity_code,
        receiver_name=receiver_name,
        id_qualifier=receiver_id_qualifier,
        receiver_edi=receiver_edi
    )

def create_nm1_payto_address_segments(config):
    """
    Constructs the NM1 segment for the Pay-To Address, N3 for street address, and N4 for city, state, and ZIP.
    This is used if the Pay-To Address is different from the Billing Provider Address.
    """
    payto_provider_name = legacy_require_config_value([config], 'payto_provider_name', 'DEFAULT PAY-TO NAME', '2010AB Pay-To Name', config)
    payto_address = legacy_require_config_value([config], 'payto_address', 'DEFAULT PAY-TO ADDRESS', '2010AB Pay-To Address', config)
    payto_city = legacy_require_config_value([config], 'payto_city', 'DEFAULT PAY-TO CITY', '2010AB Pay-To City', config)
    payto_state = legacy_require_config_value([config], 'payto_state', 'DEFAULT PAY-TO STATE', '2010AB Pay-To State', config)
    payto_zip = legacy_require_config_value([config], 'payto_zip', 'DEFAULT PAY-TO ZIP', '2010AB Pay-To ZIP', config)
    
    nm1_segment = "NM1*87*2*{}~".format(payto_provider_name)
    n3_segment = "N3*{}~".format(payto_address)
    n4_segment = "N4*{}*{}*{}~".format(payto_city, payto_state, payto_zip)
    return [nm1_segment, n3_segment, n4_segment]

# Constructs the N3 and N4 segments for the payer's address.
def create_payer_address_segments(config):
    """
    Constructs the N3 and N4 segments for the payer's address.
    
    """
    payer_address_line_1 = config.get('payer_address_line_1', '')
    payer_city = config.get('payer_city', '')
    payer_state = config.get('payer_state', '')
    payer_zip = config.get('payer_zip', '')

    n3_segment = "N3*{}~".format(payer_address_line_1)
    n4_segment = "N4*{}*{}*{}~".format(payer_city, payer_state, payer_zip)

    return [n3_segment, n4_segment]

# Constructs the PRV segment for billing provider.
def create_billing_prv_segment(config, endpoint):
    if endpoint.lower() == 'optumedi':
        return "PRV*BI*PXC*{}~".format(config['billing_provider_taxonomy'])
    return ""

# (2000B Loop) Constructs the SBR segment for subscriber based on parsed data and configuration.
def create_sbr_segment(config, parsed_data, endpoint):
    # Determine the payer responsibility sequence number code based on the payer type
    # If the payer is Medicare, use 'P' (Primary)
    # If the payer is not Medicare and is primary insurance, use 'P' (Primary)
    # If the payer is secondary insurance after Medicare, use 'S' (Secondary)
    # Assume everything is Primary for now.
    responsibility_code = 'S' if parsed_data.get('claim_type') == 'secondary' else 'P'

    # Insurance Type Code (SBR09)
    insurance_type_code = insurance_type_selection(parsed_data)

    # Prefer Medicare-specific type codes when determinable and COB helpers are available
    if COB is not None:
        try:
            medicare_type = COB.determine_medicare_payer_type(parsed_data, config)
            if medicare_type:
                insurance_type_code = medicare_type  # MB or MA
        except Exception as e:
            MediLink_ConfigLoader.log("COB determine_medicare_payer_type error: {}".format(str(e)), level="WARNING")

    # Construct the SBR segment using the determined codes
    sbr_segment = "SBR*{responsibility_code}*18*******{insurance_type_code}~".format(
        responsibility_code=responsibility_code,
        insurance_type_code=insurance_type_code
    )
    return sbr_segment

def insurance_type_selection(parsed_data):
    """
    Enhanced insurance type selection with optional API integration and safe fallbacks.
    Maintains exact same signature as existing implementation.
    
    TODO (HIGH SBR09) Finish making this function. 
    This should  eventually integrate into a menu upstream. This menu flow probably needs to be alongside the suggested endpoint flow.
    For now let's make a menu here and then figure out the automated/API method to getting this per patient as there are no
    useful historical patterns other than to say that the default should be PPO (12), then CI, then FI as most common options, 
    followed by the rest. 
    
    Present a user-selectable menu of insurance types based on predefined codes.
    User needs to input the desired 2 character code for that patient or default to PPO.
    
    Currently implements a simple text-based selection menu to choose
    an insurance type for a patient. The default selection is '12' for PPO, but the user
    can input other codes as per the options listed. This initial implementation uses
    simple input/output functions for selection and can be replaced in the future by a 
    more dynamic interface or API-driven selection method.
    
    FUTURE: The selection menu can attempt an on-demand eligibility call to retrieve
    the insurance type code when absent, then persist via the lean JSON cache for
    reuse; keep this behind a feature flag and do not alter current priority (API>MAN>DEF).
    """
    MediLink_ConfigLoader.log("insurance_type_selection(parsed_data): {}".format(parsed_data), level="DEBUG")
    
    # Try enhanced selection with safe fallback
    if safe_insurance_type_selection:
        try:
            return safe_insurance_type_selection(parsed_data, _original_insurance_type_selection_logic)
        except Exception as e:
            MediLink_ConfigLoader.log("Error in enhanced insurance selection: {}. Using original logic".format(str(e)), level="ERROR")
            return _original_insurance_type_selection_logic(parsed_data)
    else:
        MediLink_ConfigLoader.log("Enhanced insurance selection not available. Using original logic", level="INFO")
        return _original_insurance_type_selection_logic(parsed_data)

def _original_insurance_type_selection_logic(parsed_data):
    """
    Original insurance type selection logic extracted to preserve exact behavior.
    This ensures backward compatibility when enhanced features are not available.
    """
    # Import validation function
    try:
        from MediLink.MediLink_insurance_utils import validate_insurance_type_from_config
    except ImportError:
        validate_insurance_type_from_config = None
    
    # Check if insurance type is already assigned and is valid
    insurance_type_code = parsed_data.get('insurance_type')
    insurance_type_source = str(parsed_data.get('insurance_type_source', ''))
    
    # If API provided the code, validate it against insurance_options (strict mode)
    if insurance_type_source == 'API' and validate_insurance_type_from_config:
        try:
            validated_code, is_valid = validate_insurance_type_from_config(
                insurance_type_code, 
                payer_id=parsed_data.get('payer_id', ''),
                source='API',
                strict_mode=True,
                allow_unknown=False
            )
            if not is_valid:
                MediLink_ConfigLoader.log("API insurance type '{}' not found in insurance_options, using validated fallback '{}'".format(
                    insurance_type_code, validated_code), level="WARNING")
            else:
                MediLink_ConfigLoader.log("Insurance type (API) validated: {}".format(validated_code), level="DEBUG")
            return validated_code
        except Exception as e:
            MediLink_ConfigLoader.log("Error validating API insurance type: {}".format(str(e)), level="WARNING")
            # Fall through to format validation
    
    # For non-API sources, also validate against insurance_options if validation function available
    if insurance_type_code and validate_insurance_type_from_config:
        try:
            validated_code, is_valid = validate_insurance_type_from_config(
                insurance_type_code,
                payer_id=parsed_data.get('payer_id', ''),
                source=insurance_type_source or 'UNKNOWN',
                strict_mode=True,
                allow_unknown=False
            )
            if not is_valid:
                if validated_code != insurance_type_code:
                    MediLink_ConfigLoader.log("Insurance type '{}' (source: {}) not found in insurance_options, using validated fallback '{}'".format(
                        insurance_type_code, insurance_type_source or 'UNKNOWN', validated_code), level="WARNING")
                else:
                    MediLink_ConfigLoader.log("Insurance type '{}' (source: {}) not found in insurance_options but format is valid, using as-is".format(
                        insurance_type_code, insurance_type_source or 'UNKNOWN'), level="WARNING")
            return validated_code
        except Exception as e:
            MediLink_ConfigLoader.log("Error validating insurance type: {}".format(str(e)), level="WARNING")
            # Fall through to format validation
    
    # Format validation fallback (if validation function unavailable or failed)
    if insurance_type_code and len(insurance_type_code) <= 3 and insurance_type_code.isalnum():
        MediLink_ConfigLoader.log("Insurance type already assigned: {}".format(insurance_type_code), level="DEBUG")
        return insurance_type_code
    elif insurance_type_code:
        MediLink_ConfigLoader.log("Invalid insurance type: {}".format(insurance_type_code), level="WARNING")
    
    print("\nInsurance Type Validation Error: Select the insurance type for patient {}: ".format(parsed_data['LAST']))

    # Retrieve insurance options with codes and descriptions
    config, _ = MediLink_ConfigLoader.load_configuration()
    try:
        from MediCafe.core_utils import extract_medilink_config
        medi = extract_medilink_config(config)
        insurance_options = medi.get('insurance_options', {})
    except Exception:
        insurance_options = {}

    # If COB library is available, augment options with Medicare codes (MB/MA/MC)
    if COB is not None:
        try:
            insurance_options = COB.get_enhanced_insurance_options(config)
        except Exception as e:
            MediLink_ConfigLoader.log("COB get_enhanced_insurance_options error: {}".format(str(e)), level="WARNING")
    
    # STRATEGIC NOTE (Enhanced Insurance Options): COB library is fully implemented
    # To activate enhanced Medicare support, replace this TODO with:
    # if COB is not None and config.get('MediLink_Config', {}).get('cob_settings', {}).get('enabled', False):
    #     try:
    #         insurance_options = COB.get_enhanced_insurance_options(config)
    #         # This adds support for Medicare codes: MB (Part B), MA (Advantage), MC (Part C)
    #     except Exception as e:
    #         MediLink_ConfigLoader.log("COB enhancement error: {}".format(str(e)), level="WARNING")
    # 
    # IMPLEMENTATION QUESTIONS:
    # 1. Should Medicare type detection be automatic or require explicit configuration?
    # 2. How should Medicare Advantage plans be distinguished from traditional Medicare?
    # 3. Should enhanced options be enabled globally or per-endpoint?

    def prompt_display_insurance_options():
        # Prompt to display full list
        display_full_list = input("Do you want to see the full list of insurance options? (yes/no): ").strip().lower()

        # Display full list if user confirms
        if display_full_list in ['yes', 'y'] and MediLink_Display_Utils:
            MediLink_Display_Utils.display_insurance_options(insurance_options)

    # Horrible menu
    prompt_display_insurance_options()
    
    # Default selection
    insurance_type_code = '12'

    # User input for insurance type
    user_input = input("Enter the 2-character code for the insurance type (or press Enter to default to '12' for PPO): ").strip().upper()

    # Input validation and assignment
    if user_input:
        # Basic format validation
        if len(user_input) > 3 or not user_input.isalnum():
            print("Invalid format: Insurance codes should be 1-3 alphanumeric characters. Defaulting to PPO.")
        elif user_input in insurance_options:
            insurance_type_code = user_input
            print("Selected: {} - {}".format(user_input, insurance_options[user_input]))
        else:
            # User wants to use a code not in options - confirm with them
            confirm = input("Code '{}' not found in options. Use it anyway? (y/n): ".format(user_input)).strip().lower()
            if confirm in ['y', 'yes']:
                insurance_type_code = user_input
                print("Using code: {}".format(user_input))
            else:
                print("Defaulting to PPO (Preferred Provider Organization)")
    else:
        print("Using default: PPO (Preferred Provider Organization)")

    return insurance_type_code

def payer_id_to_payer_name(parsed_data, config, endpoint, crosswalk, client):
    """
    Preprocesses payer information from parsed data and enriches parsed_data with the payer name and ID.

    Args:
        parsed_data (dict): Parsed data containing Z-dat information.
        config (dict): Configuration settings.
        endpoint (str): Intended Endpoint for resolving payer information.

    Returns:
        dict: Enriched parsed data with payer name and payer ID.
    """
    # Step 1: Extract insurance name from parsed data
    insurance_name = parsed_data.get('INAME', '')

    # Step 2: Map insurance name to payer ID
    payer_id = map_insurance_name_to_payer_id(insurance_name, config, client, crosswalk)

    # Step 3: Validate payer_id
    if payer_id is None:
        error_message = "Payer ID for '{}' cannot be None.".format(insurance_name)
        MediLink_ConfigLoader.log(error_message, level="WARNING")
        raise ValueError(error_message)

    # Step 4: Resolve payer name using payer ID
    payer_name = resolve_payer_name(payer_id, config, endpoint, insurance_name, parsed_data, crosswalk, client)

    # Enrich parsed_data with payer name and payer ID
    parsed_data['payer_name'] = payer_name
    parsed_data['payer_id'] = payer_id

    return parsed_data

# Then you can use the enriched parsed_data in your main function
def create_2010BB_payer_information_segment(parsed_data):
    """
    Creates the 2010BB payer information segment.

    Args:
        parsed_data (dict): Parsed data containing enriched payer information.

    Returns:
        str: The 2010BB payer information segment.
    """
    # Extract enriched payer name and payer ID
    payer_name = parsed_data.get('payer_name')
    payer_id = parsed_data.get('payer_id')

    # Validate payer_name and payer_id
    if not payer_name or not payer_id:
        error_message = "Payer name and payer ID must be provided."
        raise ValueError(error_message)

    # Build NM1 segment using provided payer name and payer ID
    return build_nm1_segment(payer_name, payer_id)



def resolve_payer_name(payer_id, config, primary_endpoint, insurance_name, parsed_data, crosswalk, client):
    # Check if the payer_id is in the crosswalk with a name already attached to it.
    if payer_id in crosswalk.get('payer_id', {}):
        payer_info = crosswalk['payer_id'][payer_id]
        MediLink_ConfigLoader.log("Payer ID {} found in crosswalk with name: {}".format(payer_id, payer_info['name']), level="DEBUG")
        return payer_info['name']  # Return the name from the crosswalk directly.
    
    # Step 1: Attempt to fetch payer name from API using primary endpoint
    MediLink_ConfigLoader.log("Attempting to resolve Payer ID {} via API.".format(payer_id), level="INFO")
    try:
        return fetch_payer_name_from_api(client, payer_id, config, primary_endpoint)
    except Exception as api_error:
        # Step 2: Log API resolution failure and initiate user intervention
        MediLink_ConfigLoader.log("API resolution failed for {}: {}. Initiating user intervention.".format(payer_id, str(api_error)), config, level="WARNING")
        
        # Step 3: Print warning message for user intervention
        print("\n\nWARNING: Unable to verify Payer ID '{}' for patient '{}'!".format(payer_id, parsed_data.get('CHART', 'unknown')))
        print("         Claims for '{}' may be incorrectly routed or fail without intervention.".format(insurance_name))
        print("\nACTION REQUIRED: Please verify the internet connection and the Payer ID by searching for it at the expected endpoint's website or using Google.")
        print("\nNote: If the Payer ID '{}' is incorrect for '{}', \nit may need to be manually corrected.".format(payer_id, insurance_name))
        print("If the Payer ID appears correct, you may skip the correction and force-continue with this one.")
        print("\nPlease check the Payer ID in the Crosswalk and the initial \ndata source (e.g., Carol's CSV) as needed.")
        print("If unsure, llamar a Dani for guidance on manual corrections.")
        
        # In Test Mode, avoid blocking prompts and proceed with a placeholder name after API failure
        if _is_test_mode(config):
            try:
                if payer_id in crosswalk.get('payer_id', {}):
                    _nm = crosswalk['payer_id'][payer_id].get('name', 'TEST INSURANCE')
                    print("TEST MODE: Using crosswalk payer name '{}' after API failure".format(_nm))
                    return _nm
            except Exception:
                pass
            MediLink_ConfigLoader.log("[TEST MODE] API resolution failed; using placeholder payer name", config, level="WARNING")
            print("TEST MODE: Using placeholder payer name 'TEST INSURANCE' after API failure")
            return 'TEST INSURANCE'
    
        # Step 4: Integrate user input logic
        user_decision = input("\nType 'FORCE' to force-continue with the Medisoft name, or press Enter to pause processing and make corrections: ").strip().lower()
        
        if user_decision == 'force':
            # Step 5: Fallback to truncated insurance name
            truncated_name = insurance_name[:10]  # Temporary fallback
            MediLink_ConfigLoader.log("Using truncated insurance name '{}' as a fallback for {}".format(truncated_name, payer_id), config, level="WARNING")
            return truncated_name
        elif not user_decision:
            # Step 6: Prompt user for corrected payer ID
            corrected_payer_id = prompt_user_for_payer_id(insurance_name)
            if corrected_payer_id:
                try:
                    resolved_name = fetch_payer_name_from_api(client, corrected_payer_id, config, primary_endpoint)
                    print("API resolved to insurance name: {}".format(resolved_name))
                    MediLink_ConfigLoader.log("API Resolved to standard insurance name: {} for corrected payer ID: {}".format(resolved_name, corrected_payer_id), config, level="INFO")
    
                    # Step 7: Ask for user confirmation using the helper
                    confirmation_prompt = "Proceed with updating the Payer ID for '{}'? (yes/no): ".format(resolved_name)
                    if get_user_confirmation(confirmation_prompt):
                        # Step 8: Load crosswalk
                        try:
                            config, crosswalk = MediLink_ConfigLoader.load_configuration()
                        except Exception as e:
                            print("Failed to load configuration and crosswalk: {}".format(e))
                            MediLink_ConfigLoader.log("Failed to load configuration and crosswalk: {}".format(e), config, level="ERROR")
                            exit(1)
                        
                        # Step 9: Update the crosswalk with the corrected Payer ID
                        # Note: update_crosswalk_with_corrected_payer_id is imported at module level
                        
                        if update_crosswalk_with_corrected_payer_id(client, payer_id, corrected_payer_id, config, crosswalk):
                            return resolved_name
                        else:
                            print("Failed to update crosswalk with the corrected Payer ID.")
                            MediLink_ConfigLoader.log("Failed to update crosswalk with the corrected Payer ID.", config, level="ERROR")
                            exit(1)  # Consider handling failure differently.
                    else:
                        # Step 10: Handle rejection with recovery path
                        print("User did not confirm the standard insurance name. Manual intervention is required.")
                        MediLink_ConfigLoader.log("User did not confirm the standard insurance name. Manual intervention is required.", config, level="CRITICAL")
                        
                        #   FIXED: CRITICAL ISSUE - Implemented recovery path instead of exit(1)
                        # The insurance name confirmation is primarily a sanity check to verify the API recognizes the payer ID,
                        # not a critical validation for claim processing. The payer name is not used in the crosswalk or in the
                        # actual claims once they are built. This implementation provides a recovery path instead of halting.
                        #
                        # IMPLEMENTATION DETAILS:
                        # - Prompts user for manual insurance name entry
                        # - Uses existing update_crosswalk_with_new_payer_id function for persistence
                        # - Provides graceful fallback to original name if crosswalk update fails
                        # - Maintains full logging and error handling
                        # - Returns to continue processing instead of exiting
                        
                        # Prompt user to manually enter the correct insurance name
                        corrected_name = input("Please enter the correct insurance name: ").strip()
                        
                        if not corrected_name:
                            print("No insurance name provided. Using original name: {}".format(insurance_name))
                            MediLink_ConfigLoader.log("No corrected insurance name provided, using original: {}".format(insurance_name), config, level="WARNING")
                            return insurance_name  # Return original name to continue processing
                        
                        MediLink_ConfigLoader.log("User provided corrected insurance name: {}".format(corrected_name), config, level="INFO")
                        print("Using manually entered insurance name: {}".format(corrected_name))
                        
                        # Update the crosswalk with the corrected payer name using existing infrastructure
                        try:
                            # Use the existing update_crosswalk_with_new_payer_id function
                            # This function handles both new payer IDs and name corrections
                            if update_crosswalk_with_new_payer_id(client, corrected_name, payer_id, config, crosswalk):
                                MediLink_ConfigLoader.log("Successfully updated crosswalk with corrected insurance name: {} -> {}".format(insurance_name, corrected_name), config, level="INFO")
                                print("Crosswalk updated with corrected insurance name")
                                return corrected_name  # Return corrected name to continue processing
                            else:
                                print("Warning: Failed to update crosswalk with corrected name. Continuing with original name.")
                                MediLink_ConfigLoader.log("Failed to update crosswalk with corrected name, using original: {}".format(insurance_name), config, level="WARNING")
                                return insurance_name  # Return original name to continue processing
                        except Exception as e:
                            print("Error updating crosswalk with corrected name: {}. Continuing with original name.".format(str(e)))
                            MediLink_ConfigLoader.log("Error updating crosswalk with corrected name: {}. Using original: {}".format(str(e), insurance_name), config, level="ERROR")
                            return insurance_name  # Return original name to continue processing  
                except Exception as e:
                    # Step 11: Handle exceptions during resolution
                    print("Failed to resolve corrected payer ID to standard insurance name: {}".format(e))
                    MediLink_ConfigLoader.log("Failed to resolve corrected payer ID to standard insurance name: {}".format(e), config, level="ERROR")
                    exit(1)  # Consider handling differently.
            else:
                # Step 12: Handle absence of corrected payer ID
                print("Exiting script. Please make the necessary corrections and retry.")
                MediLink_ConfigLoader.log("Exiting script due to absence of corrected Payer ID.", config, level="CRITICAL")
                exit(1)  # Consider handling differently.
        else:
            # Optional: Handle unexpected user input
            print("Invalid input. Manual intervention is required.")
            MediLink_ConfigLoader.log("Invalid user input during payer name resolution.", config, level="CRITICAL")
            exit(1)  # Consider handling differently.

def handle_missing_payer_id(insurance_name, config, crosswalk, client):
    # Reset config pull to make sure its not using the MediLink config key subset
    config, crosswalk = MediLink_ConfigLoader.load_configuration()
    
    # Step 1: Inform about the missing Payer ID
    print("Missing Payer ID for insurance name: {}".format(insurance_name))
    MediLink_ConfigLoader.log("Missing Payer ID for insurance name: {}".format(insurance_name), config, level="WARNING")
    
    # Step 2: Prompt the user for manual payer ID input
    payer_id = prompt_user_for_payer_id(insurance_name)
    
    if not payer_id:
        # Step 3: Handle absence of payer ID input
        message = "Unable to resolve missing Payer ID. Manual intervention is required."
        MediLink_ConfigLoader.log(message, config, level="CRITICAL")
        print(message)
        return None
    
    # Step 4: Resolve the payer ID to a standard insurance name via API
    try:
        # primary_endpoint=None should kick to the default in the API function.
        standard_insurance_name = resolve_payer_name(payer_id, config, primary_endpoint=None, insurance_name=insurance_name, parsed_data={}, crosswalk=crosswalk, client=client)
        message = "Resolved to standard insurance name: {} for payer ID: {}".format(standard_insurance_name, payer_id)
        print(message)
        MediLink_ConfigLoader.log(message, config, level="INFO")
    except Exception as e:
        # Step 5: Handle exceptions during resolution
        message = "Failed to resolve payer ID to standard insurance name: {}".format(e)
        print(message)
        MediLink_ConfigLoader.log(message, config, level="ERROR")
        return None
    
    # Step 6: Ask for user confirmation
    confirmation_prompt = "Is the standard insurance name '{}' correct? (yes/no): ".format(standard_insurance_name)
    if get_user_confirmation(confirmation_prompt):
        # Step 7: Update the crosswalk with the new payer ID and insurance name mapping
        # Note: update_crosswalk_with_new_payer_id is imported at module level
        try:
            MediLink_ConfigLoader.log("Updating crosswalk with payer ID: {} for insurance name: {}".format(payer_id, insurance_name), config, level="DEBUG")
            update_crosswalk_with_new_payer_id(client, insurance_name, payer_id, config, crosswalk)
            return payer_id  # Return the payer_id after successful update
        except Exception as e:
            # Enhanced error message to include exception type and context
            error_message = "Failed to update crosswalk with new Payer ID: {}. Exception type: {}. Context: {}".format(
                e, type(e).__name__, str(e)
            )
            print(error_message)
            MediLink_ConfigLoader.log(error_message, config, level="ERROR")
            return None
    else:
        # Step 8: Handle rejection
        print("User did not confirm the standard insurance name. Manual intervention is required.")
        MediLink_ConfigLoader.log("User did not confirm the standard insurance name. Manual intervention is required.", config, level="CRITICAL")
        return None





def map_insurance_name_to_payer_id(insurance_name, config, client, crosswalk):
    """
    Maps insurance name to payer ID using the crosswalk configuration.

    Args:
        insurance_name (str): Name of the insurance.
        config (dict): Configuration settings.

    Returns:
        str: The payer ID corresponding to the insurance name.
    """
    try:        
        # Load crosswalk configuration only if 'payer_id' is not initialized
        if 'payer_id' not in crosswalk:
            _, crosswalk = MediLink_ConfigLoader.load_configuration(None, config.get('crosswalkPath', 'crosswalk.json'))
            
            # Ensure crosswalk is initialized and 'payer_id' key is available
            if 'payer_id' not in crosswalk:
                if _is_test_mode(config):
                    MediLink_ConfigLoader.log("[TEST MODE] Crosswalk 'payer_id' missing. Using hardcoded fallback 'TEST01'", config, level="WARNING")
                    print("TEST MODE: Crosswalk 'payer_id' missing. Using fallback payer ID 'TEST01'")
                    return 'TEST01'
                raise ValueError("Crosswalk 'payer_id' not found. Please run MediBot_Preprocessor.py with the --update-crosswalk argument.")

        # Load insurance data from MAINS to get insurance ID
        insurance_to_id = load_insurance_data_from_mains(config)
        
        # Get medisoft ID corresponding to the insurance name
        medisoft_id = insurance_to_id.get(insurance_name)
        if medisoft_id is None:
            # Find closest matches instead of immediately failing
            closest_matches = find_closest_insurance_matches(insurance_name, insurance_to_id)
            
            if closest_matches:
                # In Test Mode, auto-select the best match to avoid interaction
                if _is_test_mode(config):
                    try:
                        auto_name = closest_matches[0][0]
                        medisoft_id = insurance_to_id.get(auto_name)
                        MediLink_ConfigLoader.log("[TEST MODE] Auto-selected closest insurance match '{}' for original '{}'".format(auto_name, insurance_name), config, level="WARNING")
                    except Exception:
                        medisoft_id = None
                else:
                    # Prompt user to select from closest matches
                    selected_insurance_name = prompt_for_insurance_selection(insurance_name, closest_matches, config)
                    
                    if selected_insurance_name:
                        # Use the selected insurance name
                        medisoft_id = insurance_to_id.get(selected_insurance_name)
                        MediLink_ConfigLoader.log("Using selected insurance name '{}' for original '{}'".format(selected_insurance_name, insurance_name), config, level="INFO")
                    else:
                        # Test Mode: fallback to a safe placeholder payer ID and continue
                        if _is_test_mode(config):
                            try:
                                first_key = None
                                for _k in crosswalk.get('payer_id', {}).keys():
                                    first_key = _k
                                    break
                                if first_key:
                                    MediLink_ConfigLoader.log("[TEST MODE] Using fallback payer ID '{}' for insurance '{}'".format(first_key, insurance_name), config, level="WARNING")
                                    print("TEST MODE: Using fallback payer ID '{}' for insurance '{}'".format(first_key, insurance_name))
                                    return first_key
                            except Exception:
                                pass
                            MediLink_ConfigLoader.log("[TEST MODE] Using hardcoded fallback payer ID 'TEST01' for insurance '{}'".format(insurance_name), config, level="WARNING")
                            print("TEST MODE: Using hardcoded fallback payer ID 'TEST01' for insurance '{}'".format(insurance_name))
                            return 'TEST01'
                        # User chose manual intervention
                        error_message = "CLAIM SUBMISSION CANCELLED: Insurance name '{}' not found in MAINS and user chose manual intervention.".format(insurance_name)
                        MediLink_ConfigLoader.log(error_message, config, level="WARNING")
                        print("\n" + "="*80)
                        print("CLAIM SUBMISSION CANCELLED: MANUAL INTERVENTION REQUIRED")
                        print("="*80)
                        print("\nThe system cannot automatically process this claim because:")
                        print("- Insurance name '{}' was not found in the MAINS database".format(insurance_name))
                        print("- Without a valid insurance mapping, the claim cannot be submitted")
                        print("\nTo proceed with this claim, you need to:")
                        print("1. Verify the correct insurance company name")
                        print("2. Ensure the insurance company is in your Medisoft system")
                        print("3. Restart the claim submission process once the insurance is properly configured")
                        print("="*80)
                        raise ValueError(error_message)
            else:
                # No matches found in MAINS
                if _is_test_mode(config):
                    try:
                        first_key = None
                        for _k in crosswalk.get('payer_id', {}).keys():
                            first_key = _k
                            break
                        if first_key:
                            MediLink_ConfigLoader.log("[TEST MODE] No MAINS match. Using fallback payer ID '{}' for '{}'".format(first_key, insurance_name), config, level="WARNING")
                            print("TEST MODE: No MAINS match. Using fallback payer ID '{}' for '{}'".format(first_key, insurance_name))
                            return first_key
                    except Exception:
                        pass
                    MediLink_ConfigLoader.log("[TEST MODE] No MAINS match. Using hardcoded fallback payer ID 'TEST01' for '{}'".format(insurance_name), config, level="WARNING")
                    print("TEST MODE: No MAINS match. Using hardcoded fallback payer ID 'TEST01' for '{}'".format(insurance_name))
                    return 'TEST01'
                error_message = "CLAIM SUBMISSION FAILED: Cannot find Medisoft ID for insurance name: '{}'. No similar matches found in MAINS database.".format(insurance_name)
                MediLink_ConfigLoader.log(error_message, config, level="ERROR")
                print("\n" + "="*80)
                print("CLAIM SUBMISSION ERROR: INSURANCE MAPPING FAILED")
                print("="*80)
                print("\nThe system cannot process this claim because:")
                print("- Insurance name '{}' was not found in the MAINS database".format(insurance_name))
                print("- No similar insurance names were found for manual selection")
                print("- Without a Medisoft ID, the system cannot:")
                print("  - Convert the insurance name to a payer ID")
                print("  - Generate the required 837p claim format")
                print("  - Submit the claim to the insurance company")
                print("\nThis typically happens when:")
                print("- The insurance company name is misspelled or abbreviated")
                print("- The insurance company is not in Medisoft")
                print("- The MAINS database is missing or incomplete")
                print("\nTO FIX THIS:")
                print("1. Check the spelling of the insurance company name")
                print("2. Verify the insurance company exists in Medisoft")
                print("3. If the name is correct, llamar a Dani")
                print("4. The insurance company may need to be added")
                print("="*80)
                raise ValueError(error_message)
        
        # Convert medisoft_id to string to match the JSON data type
        medisoft_id_str = str(medisoft_id)
        
        # Get payer ID corresponding to the medisoft ID
        payer_id = None
        for payer, payer_info in crosswalk['payer_id'].items():
            if medisoft_id_str in payer_info['medisoft_id']:
                payer_id = payer
                break

        # Handle the case where no payer ID is found
        if payer_id is None:
            if _is_test_mode(config):
                try:
                    first_key = None
                    for _k in crosswalk.get('payer_id', {}).keys():
                        first_key = _k
                        break
                    if first_key:
                        MediLink_ConfigLoader.log("[TEST MODE] No payer ID found for Medisoft ID {}. Using fallback '{}'".format(medisoft_id, first_key), config, level="WARNING")
                        payer_id = first_key
                    else:
                        MediLink_ConfigLoader.log("[TEST MODE] No payer ID found for Medisoft ID {}. Using hardcoded 'TEST01'".format(medisoft_id), config, level="WARNING")
                        payer_id = 'TEST01'
                except Exception:
                    payer_id = 'TEST01'
            else:
                error_message = "No payer ID found for Medisoft ID: {}.".format(medisoft_id)
                MediLink_ConfigLoader.log(error_message, config, level="ERROR")
                print(error_message)
                payer_id = handle_missing_payer_id(insurance_name, config, crosswalk, client)

        if payer_id is None:
            raise ValueError("Payer ID cannot be None after all checks.")

        return payer_id

    except ValueError as e:
        if "JSON" in str(e) and "decode" in str(e):
            error_message = "Error decoding the crosswalk JSON file in map_insurance_name_to_payer_id"
            MediLink_ConfigLoader.log(error_message, config, level="CRITICAL")
            raise ValueError(error_message)
        else:
            error_message = "Unexpected error in map_insurance_name_to_payer_id: {}".format(e)
            MediLink_ConfigLoader.log(error_message, config, level="ERROR")
            raise e

# Constructs the NM1 segment for subscriber based on parsed data and configuration.
def create_nm1_subscriber_segment(config, parsed_data, endpoint):
    if endpoint.lower() == 'optumedi':
        entity_identifier_code = config.get('endpoints', {}).get('OPTUMEDI', {}).get('subscriber_entity_code', 'IL')
    else:
        entity_identifier_code = 'IL'  # Default value if endpoint is not 'optumedi'

    return "NM1*{entity_identifier_code}*1*{last_name}*{first_name}*{middle_name}***MI*{policy_number}~".format(
        entity_identifier_code=entity_identifier_code,
        last_name=parsed_data['LAST'].replace('_', ' '), # Replace underscores with spaces in the name.
        first_name=parsed_data['FIRST'].replace('_', ' '),
        middle_name=parsed_data['MIDDLE'],
        policy_number=parsed_data['IPOLICY']
    )

# Constructs the N3 and N4 segments for subscriber address based on parsed data.
def create_subscriber_address_segments(parsed_data):
    return [
        "N3*{}~".format(parsed_data['ISTREET']),
        "N4*{}*{}*{}~".format(
            parsed_data['ICITY'],  
            parsed_data['ISTATE'],  
            parsed_data['IZIP'][:5]
        )
    ]

# Constructs the DMG segment for subscriber based on parsed data.
def create_dmg_segment(parsed_data):
    return "DMG*D8*{}*{}~".format(
        convert_date_format(parsed_data['BDAY']),  
        parsed_data['SEX'] # ensure it returns a string instead of a list if it only returns one segment
    )

def create_nm1_rendering_provider_segment(config, is_rendering_provider_different=False):
    """
    # BUG This is getting placed incorrectly. Has this been fixed??
    
    Constructs the NM1 segment for the rendering provider in the 2310B loop using configuration data.
    
    Placement guidance:
    - This function only constructs NM1/PRV segments. Ensure caller inserts these into loop 2310B
      after billing provider (2010AA) and before service line loops (2400), per 837P spec.
    - Add unit tests around the full EDI build to verify segment ordering for payers sensitive to order.
    
    Parameters:
    - config: Configuration dictionary including rendering provider details.
    - is_rendering_provider_different: Boolean indicating if rendering provider differs from billing provider.
    
    Returns:
    - List containing the NM1 segment for the rendering provider if required, otherwise an empty list.
    """
    if is_rendering_provider_different:
        segments = []
        rp_npi = config.get('rendering_provider_npi', '')
        rp_last_name = config.get('rendering_provider_last_name', '')
        rp_first_name = config.get('rendering_provider_first_name', '')

        # NM1 Segment for Rendering Provider
        segments.append("NM1*82*1*{0}*{1}**XX*{2}~".format(
            rp_last_name, 
            rp_first_name, 
            rp_npi
        ))
        
        # PRV Segment for Rendering Provider Taxonomy
        if config.get('rendering_provider_taxonomy'):
            segments.append("PRV*PE*PXC*{}~".format(config['billing_provider_taxonomy']))
        
        return segments
    else:
        return []



# Constructs the CLM and related segments based on parsed data and configuration.
def create_clm_and_related_segments(parsed_data, config, crosswalk): 
    """
    Insert the claim information (2300 loop), 
    ensuring that details such as claim ID, total charge amount,and service date are included.
    
    The HI segment for Health Care Diagnosis Codes should accurately reflect the diagnosis related to the service line.
    
    Service Line Information (2400 Loop):
    Verify that the service line number (LX), professional service (SV1), and service date (DTP) segments contain
    accurate information and are formatted according to the claim's details.
    
    STRATEGIC NOTE (Enhanced CLM Segment): COB library provides create_enhanced_clm_segment()
    
    CRITICAL STRATEGIC QUESTIONS FOR HIGH-RISK IMPLEMENTATION:
    1. **Claim Frequency Strategy**: How should CLM05-3 be determined?
       - Always "1" (original) for secondary claims?
       - Support "7" (replacement) for corrections?
       - Automatic detection of replacement scenarios?
    
    2. **COB Type Integration**: How should COB information be embedded?
       - Derive from claim_type field automatically?
       - Require explicit COB type configuration?
       - Handle mixed COB scenarios (multiple secondaries)?
    
    3. **835 Data Integration**: How should adjudication data affect CLM?
       - Should 835 paid amounts influence claim totals?
       - Handle discrepancies between calculated vs adjudicated amounts?
       - What when 835 data is missing for secondary claims?
    
    4. **PWK Attachment Strategy**: When should attachments be included?
       - Automatic for non-electronic EOB scenarios?
       - Manual control through UI?
       - Payer-specific attachment requirements?
    
    See MediLink_837p_cob_library.create_enhanced_clm_segment() for enhanced implementation.
    """
    
    # FINAL LINE OF DEFENSE: Validate all claim data before creating segments
    # Ensure crosswalk is a dict to prevent NoneType.get errors downstream
    if not isinstance(crosswalk, dict):
        crosswalk = {}
    validated_data = validate_claim_data_for_837p(parsed_data, config, crosswalk)
    
    segments = []
    
    # Format the claim number
    chart_number = validated_data.get('CHART', '')
    date_of_service = validated_data.get('DATE', '')
    formatted_claim_number = format_claim_number(chart_number, date_of_service)
        
    # CLM - Claim Information
    # TODO (COB ENHANCEMENT): Enhanced claim frequency handling
    # For COB claims, CLM05-3 should be "1" (original) unless replacement logic applies
    claim_frequency = "1"  # Default to original
    # if validated_data.get('claim_type') == 'secondary':
    #     claim_frequency = "1"  # Original for secondary claims
    
    segments.append("CLM*{}*{}***{}:B:{}*Y*A*Y*Y~".format(
        formatted_claim_number,
        validated_data['AMOUNT'],
        validated_data['TOS'],
        claim_frequency))
    
    # HI - Health Care Diagnosis Code
    # Hardcoding "ABK" for ICD-10 codes as they are the only ones used now.
    medisoft_code = ''.join(filter(str.isalnum, validated_data['DIAG']))
    diagnosis_code = next((key for key, value in crosswalk.get('diagnosis_to_medisoft', {}).items() if value == medisoft_code), None)
    
    # This should never be None now due to validation, but keeping as safety check
    if diagnosis_code is None:
        raise ValueError("Diagnosis code mapping failed for patient {} with medisoft code {}".format(chart_number, medisoft_code))

    cleaned_diagnosis_code = ''.join(char for char in diagnosis_code if char.isalnum())
    segments.append("HI*ABK:{}~".format(cleaned_diagnosis_code))
    
    # (2310C Loop) Service Facility Location NPI and Address Information
    segments.extend(create_service_facility_location_npi_segment(config))
    
    # For future reference, SBR - (Loop 2320: OI, NM1 (2330A), N3, N4, NM1 (2330B)) - Other Subscriber Information goes here.
    # STRATEGIC NOTE (COB Loops): COB library is fully implemented with all loop functions
    # Current implementation below (lines 1085-1118) has basic COB loop integration
    # To activate enhanced COB loops, the existing code needs these strategic decisions:
    #
    # IMPLEMENTATION QUESTIONS:
    # 1. Should COB loops be added automatically when claim_type='secondary' or require additional validation?
    # 2. How should missing prior payer information be handled (fail claim, prompt user, use defaults)?
    # 3. Should service-level COB (2430 loop) be enabled by default or require separate configuration?
    # 4. How should COB validation failures affect claim processing (warning, error, or block submission)?
    # 5. Should COB loops be configurable per payer or globally enabled?
    #
    # The COB library provides these ready-to-use functions:
    # - create_2320_other_subscriber_segments() for secondary payer info
    # - create_2330B_prior_payer_segments() for Medicare prior payer  
    # - create_2430_service_line_cob_segments() for service-level adjudication
    # - create_2330C_other_subscriber_name_segments() when patient != subscriber
    #
    # Minimal, safe integration (guarded by feature flag):
    if COB is not None:
        cob_enabled = False
        try:
            # Read feature flag from configuration (expects medi['cob_settings']['enabled'])
            from MediCafe.core_utils import extract_medilink_config
            medi_cfg = extract_medilink_config(config)
            cob_enabled = bool(medi_cfg.get('cob_settings', {}).get('enabled', False))
        except Exception:
            cob_enabled = False
        
        # Only add COB loops when explicitly enabled and claim is secondary
        # TODO (COB VALIDATION): When COB is enabled and claim is secondary, validate required fields:
        # - prior_payer_id/prior_payer_name present
        # - primary_paid_amount present when sending AMT*D (or skip AMT if not available)
        # - cas_adjustments schema if provided (list of {group, reason, amount})
        # If critical fields are missing, log and proceed with best-effort unless config enforces strict mode.
        if cob_enabled and validated_data.get('claim_type') == 'secondary':
            try:
                # 2320 - Other Subscriber Information (OI, AMT, CAS, etc.)
                segments.extend(COB.create_2320_other_subscriber_segments(validated_data, config, crosswalk))
            except Exception as _e1:
                try:
                    MediLink_ConfigLoader.log("COB 2320 insertion failed: {}".format(str(_e1)), config, level="WARNING")
                except Exception:
                    pass
            
            try:
                # 2330B - Prior Payer (Medicare prior payer info, e.g., 00850)
                segments.extend(COB.create_2330B_prior_payer_segments(validated_data, config, crosswalk))
            except Exception as _e2:
                try:
                    MediLink_ConfigLoader.log("COB 2330B insertion failed: {}".format(str(_e2)), config, level="WARNING")
                except Exception:
                    pass
    
    # STRATEGIC NOTE (PWK Attachments): COB library provides create_pwk_attachment_segment()
    # 
    # IMPLEMENTATION QUESTIONS:
    # 1. Should PWK segments be added automatically for all COB claims or only when explicitly required?
    # 2. How should attachment control numbers be generated and tracked?
    # 3. Should attachment requirements be configurable per payer?
    # 4. What validation is needed for attachment references?
    #
    # To activate: Uncomment and configure attachment logic:
    # if cob_enabled and validated_data.get('requires_attachment'):
    #     try:
    #         pwk_segment = COB.create_pwk_attachment_segment(validated_data, config)
    #         if pwk_segment:
    #             segments.append(pwk_segment)
    #     except Exception as e:
    #         MediLink_ConfigLoader.log("PWK attachment error: {}".format(str(e)), level="WARNING")
    
    # LX - Service Line Counter
    segments.append("LX*1~")
    
    # SV1 - Professional Service
    segments.append("SV1*HC:{}:{}*{}*MJ*{}***1~".format(
        validated_data['CODEA'],
        validated_data['POS'],
        validated_data['AMOUNT'],
        validated_data['MINTUES']))
    
    # DTP - Date
    segments.append("DTP*472*D8*{}~".format(convert_date_format(validated_data['DATE'])))
    
    # REF*6R - Line Item Control Number (required for Medicare, optional for private insurance)
    # IMPLEMENTED: Add conditional REF*6R when payer is Medicare
    payer_id = validated_data.get('payer_id', '')
    payer_name = validated_data.get('payer_name', '').upper()
    
    # Check if this is a Medicare payer (compatible with XP SP3 + Python 3.4.4)
    is_medicare = (payer_id == '00850' or 
                   'MEDICARE' in payer_name or 
                   'MCARE' in payer_name or 
                   payer_id in ['MEDICARE', 'CMS', 'MCARE'])
    
    if is_medicare:
        # REF*6R*1 - Provider Control Number for Medicare claims
        # 6R = Provider Control Number qualifier
        # 1 = Sequential line item control number (could be enhanced to actual line number)
        segments.append("REF*6R*1~")
        try:
            MediLink_ConfigLoader.log("Added REF*6R segment for Medicare payer: {}".format(payer_name), config, level="DEBUG")
        except Exception:
            pass  # Don't fail if logging fails
    

    # STRATEGIC NOTE (Service-Level COB): 2430 loop implementation is ready but needs strategic decisions
    # COB library provides create_2430_service_line_cob_segments() for service-level adjudication
    # 
    # CRITICAL STRATEGIC QUESTIONS:
    # 1. **Data Source Strategy**: Where does service_adjudications data come from?
    #    - Direct 835 remittance parsing?
    #    - Manual entry through UI?
    #    - Hybrid approach with validation?
    # 
    # 2. **Activation Logic**: When should 2430 loops be included?
    #    - Only when service_adjudications is populated?
    #    - Required for all secondary claims?
    #    - Optional enhancement based on payer requirements?
    # 
    # 3. **Error Handling**: How should service-level COB failures be handled?
    #    - Continue with claim-level COB only (current approach)?
    #    - Block entire claim submission?
    #    - Provide manual override and logging?
    #
    # To activate: Uncomment and configure the following:
    # if parsed_data.get('service_adjudications') and cob_enabled:
    #     try:
    #         cob_segments = COB.create_2430_service_line_cob_segments(validated_data, config, crosswalk)
    #         segments.extend(cob_segments)
    #     except Exception as e:
    #         MediLink_ConfigLoader.log("Service-level COB error: {}".format(str(e)), level="WARNING")
    
    return segments

def get_endpoint_config(config, endpoint):
    """
    Retrieves the configuration for a specified endpoint.

    Args:
        config (dict): Configuration settings loaded from a JSON file.
        endpoint (str): The endpoint for which the configuration is requested.

    Returns:
        dict: The configuration for the specified endpoint, or raises an error if not found.
    """
    endpoint_config = config.get('endpoints', {}).get(endpoint.upper(), None)
    
    if endpoint_config is None:
        error_message = "Endpoint configuration for '{}' not found.".format(endpoint)
        MediLink_ConfigLoader.log(error_message, config, level="ERROR")
        raise ValueError(error_message)  # Raise an error for invalid endpoint

    return endpoint_config

def create_interchange_elements(config, endpoint, transaction_set_control_number):
    """
    Create interchange headers and trailers for an 837P document.

    Parameters:
    - config: Configuration settings loaded from a JSON file.
    - endpoint: The endpoint for which the data is being processed.
    - transaction_set_control_number: The starting transaction set control number.

    Returns:
    - Tuple containing (ISA header, GS header, GE trailer, IEA trailer).
    """
    endpoint_config = get_endpoint_config(config, endpoint)
    
    # Get the current system time and format it as 'HHMMSS' in 24-hour clock.
    current_time = datetime.now().strftime('%H%M%S')
    isa13 = '000' + current_time  # Format ISA13 with '000HHMMSS'.

    # Check if isa13 could not be generated from the current time
    if len(isa13) != 9:
        # If isa13 cannot be generated from the current time, use the configured value.
        isa13 = endpoint_config.get('isa_13_value', '000000001')
    
    # Create interchange header and trailer using provided library functions.
    isa_header, gs_header, gs06 = create_interchange_header(config, endpoint, isa13)
    ge_trailer, iea_trailer = create_interchange_trailer(config, transaction_set_control_number, isa13, gs06)
    
    return isa_header, gs_header, ge_trailer, iea_trailer

# Generates the ISA and GS segments for the interchange header based on configuration and endpoint.
def create_interchange_header(config, endpoint, isa13):
    """
    Generate ISA and GS segments for the interchange header, ensuring endpoint-specific requirements are met.
    Includes support for Availity, Optum, and PNT_DATA endpoints, with streamlined configuration and default handling.

    Parameters:
    - config: Configuration dictionary with settings and identifiers.
    - endpoint: String indicating the target endpoint ('Availity', 'Optum', 'PNT_DATA').
    - isa13: The ISA13 field value representing the current system time.

    Returns:
    - Tuple containing the ISA segment, GS segment, and group control number (gs06).
    """
    endpoint_config = config.get('endpoints', {}).get(endpoint.upper(), {})
    
    # Set defaults for ISA segment values
    isa02 = isa04 = "          "  # Default value for ISA02 and ISA04
    isa05 = isa07 = 'ZZ'  # Default qualifier
    isa15 = 'P'  # 'T' for Test, 'P' for Production
    
    # Conditional values from config
    isa_sender_id = endpoint_config.get('isa_06_value', config.get('submitterId', '')).rstrip()
    isa07_value = endpoint_config.get('isa_07_value', isa07)
    isa_receiver_id = endpoint_config.get('isa_08_value', config.get('receiverId', '')).rstrip()
    gs_sender_code = endpoint_config.get('gs_02_value', config.get('submitterEdi', ''))
    gs_receiver_code = endpoint_config.get('gs_03_value', config.get('receiverEdi', ''))
    isa15_value = endpoint_config.get('isa_15_value', isa15)

    # Log warnings for empty sender/receiver codes (fallback detection)
    config_warnings = []
    if not isa_sender_id or isa_sender_id.strip() == '':
        config_warnings.append("ISA06 Sender ID is empty - using fallback configuration")
    if not gs_sender_code or gs_sender_code.strip() == '':
        config_warnings.append("GS02 Sender Code is empty - using fallback configuration")
    if not isa_receiver_id or isa_receiver_id.strip() == '':
        config_warnings.append("ISA08 Receiver ID is empty - using fallback configuration")
    if not gs_receiver_code or gs_receiver_code.strip() == '':
        config_warnings.append("GS03 Receiver Code is empty - using fallback configuration")

    if config_warnings:
        warning_msg = "CONFIG FALLBACK DETECTED for endpoint {}: {}".format(endpoint, '; '.join(config_warnings))
        MediLink_ConfigLoader.log(warning_msg, config, level="WARNING")
        # Also log to console for immediate visibility during header creation
        print("WARNING: Configuration fallbacks detected during 837P header creation:")
        for warning in config_warnings:
            print("   - {}".format(warning))

    # ISA Segment
    isa_segment = "ISA*00*{}*00*{}*{}*{}*{}*{}*{}*{}*^*00501*{}*0*{}*:~".format(
        isa02, isa04, isa05, isa_sender_id.ljust(15), isa07_value, isa_receiver_id.ljust(15),
        format_datetime(format_type='isa'), format_datetime(format_type='time'), isa13, isa15_value
    )

    # GS Segment
    # GS04 YYYYMMDD
    # GS06 Group Control Number, Field Length 1/9, must match GE02
    # FIXED: Generate group control number using similar logic to ISA13 for consistency
    current_time = datetime.now().strftime('%H%M%S')
    # Normalize GS06 to suppress leading zeros per X12 numeric element rules
    try:
        _gs06_val = int(current_time[-6:] or '0')
    except Exception:
        _gs06_val = 0
    if _gs06_val < 1:
        _gs06_val = 1
    gs06 = str(_gs06_val)
    
    gs_segment = "GS*HC*{}*{}*{}*{}*{}*X*005010X222A1~".format(
        gs_sender_code, gs_receiver_code, format_datetime(), format_datetime(format_type='time'), gs06
    )

    MediLink_ConfigLoader.log("Created interchange header for endpoint: {} with group control number: {}".format(endpoint, gs06), config, level="INFO")
    
    return isa_segment, gs_segment, gs06

# Generates the GE and IEA segments for the interchange trailer based on the number of transactions and functional groups.
def create_interchange_trailer(config, num_transactions, isa13, gs06, num_functional_groups=1):
    """
    Generate GE and IEA segments for the interchange trailer.
    
    Parameters:
    - config: Configuration dictionary with settings and identifiers.
    - num_transactions: The number of transactions within the functional group.
    - isa13: The ISA13 field value representing the current system time.
    - gs06: The group control number from GS segment (must match GE02).
    - num_functional_groups: The number of functional groups within the interchange. Default is 1.
    
    Returns:
    - Tuple containing the GE and IEA segment strings.
    """
    
    # GE Segment: Functional Group Trailer
    # Indicates the end of a functional group and provides the count of the number of transactions within it.
    
    # GE02 Group Control Number, Field Length 1/9, must match GS06 (Header)
    # FIXED: Use the gs06 parameter passed from the header generation instead of hardcoded placeholder
    ge_segment = "GE*{}*{}~".format(num_transactions, gs06)
    
    # IEA Segment: Interchange Control Trailer (Note: IEA02 needs to equal ISA13)
    iea_segment = "IEA*{}*{}~".format(num_functional_groups, isa13)
    
    MediLink_ConfigLoader.log("Created interchange trailer with matching group control number: {}".format(gs06), config, level="INFO")
    
    return ge_segment, iea_segment

def validate_claim_data_for_837p(parsed_data, config, crosswalk):
    """
    Final line of defense validation for 837P claim data.
    
    This function validates that all required fields have valid values before creating
    the 837P claim. If invalid values are found, it provides detailed user guidance
    and allows manual input to correct the data.
    
    Parameters:
    - parsed_data: Dictionary containing claim data
    - config: Configuration settings
    - crosswalk: Crosswalk data for mappings
    
    Returns:
    - Dictionary with validated claim data, or raises ValueError if validation fails
    """
    # Normalize parsed_data to a dict to avoid NoneType errors downstream
    if not isinstance(parsed_data, dict):
        try:
            MediLink_ConfigLoader.log("validate_claim_data_for_837p received non-dict parsed_data of type {}".format(type(parsed_data)), config, level="ERROR")
        except Exception:
            pass
        parsed_data = {}
    validated_data = parsed_data.copy()
    chart_number = parsed_data.get('CHART', 'UNKNOWN')
    
    # Validate diagnosis code
    medisoft_code = ''.join(filter(str.isalnum, parsed_data.get('DIAG', '')))
    diagnosis_code = next((key for key, value in crosswalk.get('diagnosis_to_medisoft', {}).items() if value == medisoft_code), None)
    
    if not diagnosis_code:
        if _is_test_mode(config):
            # Use a safe placeholder ICD-10 code and update mapping in-memory only
            placeholder_icd = 'R69'  # Unknown and unspecified causes of morbidity
            try:
                if 'diagnosis_to_medisoft' not in crosswalk or not isinstance(crosswalk.get('diagnosis_to_medisoft'), dict):
                    crosswalk['diagnosis_to_medisoft'] = {}
            except Exception:
                pass
            crosswalk['diagnosis_to_medisoft'][placeholder_icd] = medisoft_code or 'R69'
            MediLink_ConfigLoader.log("[TEST MODE] Using placeholder ICD '{}' and updating in-memory mapping".format(placeholder_icd), config, level="WARNING")
            print("TEST MODE: Using placeholder ICD '{}' for chart '{}' (in-memory only)".format(placeholder_icd, chart_number))
        else:
            # Log the error condition with detailed context and prompt user
            error_message = "Diagnosis code is empty for chart number: {}. Please verify. Medisoft code is {}".format(chart_number, medisoft_code)
            MediLink_ConfigLoader.log(error_message, config, level="CRITICAL")
            
            print("\n{}".format("="*80))
            print("CRITICAL: Missing diagnosis code mapping for patient {}".format(chart_number))
            print("{}".format("="*80))
            print("Medisoft code: '{}'".format(medisoft_code))
            print("Patient: {}, {}".format(parsed_data.get('LAST', 'Unknown'), parsed_data.get('FIRST', 'Unknown')))
            print("Service Date: {}".format(parsed_data.get('DATE', 'Unknown')))
            print("\nThis diagnosis code needs to be added to the crosswalk.json file.")
            print("\nCurrent diagnosis_to_medisoft mapping format:")
            
            # Show example entries from the crosswalk
            diagnosis_examples = list(crosswalk.get('diagnosis_to_medisoft', {}).items())[:3]
            for full_code, medisoft_short in diagnosis_examples:
                print("  '{}': '{}'".format(full_code, medisoft_short))
            
            print("\nPlease enter the complete ICD-10 diagnosis code (e.g., H25.10):")
            diagnosis_code = input("> ").strip()
            
            if not diagnosis_code:
                raise ValueError("Cannot proceed without diagnosis code for patient {}".format(chart_number))
            
            # Update the crosswalk dictionary with the new pairing of diagnosis_code and medisoft_code
            crosswalk['diagnosis_to_medisoft'][diagnosis_code] = medisoft_code
            MediLink_ConfigLoader.log("Updated crosswalk with new diagnosis code: {}, for Medisoft code {}".format(diagnosis_code, medisoft_code), config, level="INFO")
            print("\n[SUCCESS] Added '{}' -> '{}' to crosswalk".format(diagnosis_code, medisoft_code))
            
            # Fix: Automatically persist the crosswalk changes
            try:
                # Import the existing save function from MediBot_Crosswalk_Utils
                from MediBot.MediBot_Crosswalk_Utils import save_crosswalk
                if save_crosswalk(None, config, crosswalk, skip_api_operations=True):
                    print("Crosswalk changes saved successfully.")
                    MediLink_ConfigLoader.log("Diagnosis code mapping persisted to crosswalk file", config, level="INFO")
                else:
                    print("Warning: Failed to save crosswalk changes - they may be lost on restart.")
                    MediLink_ConfigLoader.log("Failed to persist diagnosis code mapping", config, level="WARNING")
            except ImportError:
                print("Warning: Could not import save_crosswalk function - changes not persisted.")
                MediLink_ConfigLoader.log("Could not import save_crosswalk for diagnosis persistence", config, level="ERROR")
            except Exception as e:
                print("Warning: Error saving crosswalk changes: {}".format(e))
                MediLink_ConfigLoader.log("Error persisting diagnosis code mapping: {}".format(e), config, level="ERROR")
        
        # TODO (HIGH PRIORITY - Crosswalk Data Persistence and Validation):
        #   FIXED: Diagnosis codes are now automatically persisted to file
        #   FIXED: Manual save requirement has been removed
        #   FIXED: Error handling and logging added for file save failures
        #
        # REMAINING WORKFLOW ISSUES:
        # 1. Validation still happens during encoding (too late in the process) - FUTURE ENHANCEMENT (High Priority - but difficult to implement)
        # 2. No backup or rollback mechanism for crosswalk changes - FUTURE ENHANCEMENT (Lower Priority)
        # 3. No validation of new mappings before they're added - FUTURE ENHANCEMENT (Medium Priority)
        #
        # FUTURE ENHANCEMENTS (NOT CRITICAL):
        # 
        # Phase 2: Upstream Validation (RECOMMENDED)
        # 1. Move validation to data preprocessing stage:
        #    - Add validate_diagnosis_codes_in_csv() function in preprocessing
        #    - Check all diagnosis codes against crosswalk before encoding starts
        #    - Batch collect all missing codes and prompt user once
        # 2. Create interactive crosswalk update session:
        #    - Present all missing codes to user in a single session
        #    - Allow bulk updates with confirmation
        #    - Save all changes at once rather than piecemeal
        #
        # Phase 3: Enhanced Validation (FUTURE)
        # 1. Add ICD-10 code validation against official code sets
        # 2. Suggest similar codes when exact matches aren't found
        # 3. Add crosswalk versioning and change tracking
        # 4. Implement crosswalk sharing across multiple users/systems
        #
        #   IMPLEMENTED:
        # 1.   Found existing crosswalk persistence function: save_crosswalk()
        # 2.   Added call here: save_crosswalk(None, config, crosswalk, skip_api_operations=True)
        # 3.   Removed manual save message
        # 4.   Added error handling for file save failures
        # 5.   Added logging for successful crosswalk updates
        #
        #   TESTING COMPLETED:
        # -   Crosswalk changes persist across application restarts
        # -   Error handling tested for file save failures
        # - Logging verified for successful crosswalk updates 

    # Always return the validated (or minimally normalized) data structure
    return validated_data


def validate_config_sender_codes(config, endpoint):
    """
    Validates sender/receiver identification codes in configuration before claim submission.
    
    This function specifically checks for missing or empty sender and receiver 
    identification codes that are critical for valid 837P interchange headers.
    This is separate from claim data validation and focuses on configuration issues.
    
    IMPORTANT: This function validates the config that has already been loaded by the
    centralized MediCafe config loader. It does NOT reload configuration from disk.
    
    Compatible with: Python 3.4.4, Windows XP SP3, ASCII-only output
    
    Parameters:
    - config: Configuration dictionary (already loaded by centralized loader)
    - endpoint: Endpoint name being processed
    
    Returns:
        list: List of critical configuration issues that would prevent successful submission
    """
    issues = []
    
    # Extract MediLink config safely
    medi_config = {}
    if isinstance(config, dict):
        medi_config = config.get('MediLink_Config', {})
        if not isinstance(medi_config, dict):
            medi_config = config  # Fallback to root config
    
    # Check if we're using default fallback config by examining key characteristics
    # The centralized loader provides a default config when JSON files are missing
    default_characteristics = [
        medi_config.get('local_storage_path') == '.',
        medi_config.get('receiptsRoot') == './receipts',
        not medi_config.get('submitterId', '').strip(),
        not medi_config.get('submitterEdi', '').strip()
    ]
    
    # If most default characteristics match, likely using fallback config
    if sum(default_characteristics) >= 3:
        issues.append("Using default fallback configuration - JSON config file may be missing or inaccessible")
    
    # Check critical sender identification
    submitter_id = medi_config.get('submitterId', '').strip() if isinstance(medi_config.get('submitterId'), str) else ''
    submitter_edi = medi_config.get('submitterEdi', '').strip() if isinstance(medi_config.get('submitterEdi'), str) else ''
    
    if not submitter_id:
        issues.append("submitterId is empty - ISA06 sender ID field will be blank")
    if not submitter_edi:
        issues.append("submitterEdi is empty - GS02 sender code field will be blank")
    
    # Check endpoint-specific overrides
    endpoints_config = medi_config.get('endpoints', {})
    if isinstance(endpoints_config, dict):
        endpoint_config = endpoints_config.get(endpoint, {})
        if isinstance(endpoint_config, dict):
            isa_06 = endpoint_config.get('isa_06_value', '').strip() if isinstance(endpoint_config.get('isa_06_value'), str) else ''
            gs_02 = endpoint_config.get('gs_02_value', '').strip() if isinstance(endpoint_config.get('gs_02_value'), str) else ''
            
            if not isa_06 and not submitter_id:
                issues.append("No ISA06 sender ID configured for endpoint '{}'".format(endpoint))
            if not gs_02 and not submitter_edi:
                issues.append("No GS02 sender code configured for endpoint '{}'".format(endpoint))
    else:
        # No endpoints configuration found
        if not submitter_id:
            issues.append("No endpoints configuration found and submitterId is empty")
        if not submitter_edi:
            issues.append("No endpoints configuration found and submitterEdi is empty")
    
    # Check receiver identification
    receiver_id = medi_config.get('receiverId', '').strip() if isinstance(medi_config.get('receiverId'), str) else ''
    receiver_edi = medi_config.get('receiverEdi', '').strip() if isinstance(medi_config.get('receiverEdi'), str) else ''
    
    if not receiver_id:
        issues.append("receiverId is empty - ISA08 receiver ID field will be blank")
    if not receiver_edi:
        issues.append("receiverEdi is empty - GS03 receiver code field will be blank")
    
    return issues

# Helper: resolve config value with TestMode-only defaults enforcement
# Defaults/placeholders are allowed ONLY in TestMode; otherwise we raise to avoid malformed 837p
DEFAULT_PLACEHOLDER_VALUES = set([
    'DEFAULT NAME', 'DEFAULT ID', 'DEFAULT BCBSF ID', 'DEFAULT RECEIVER NAME',
    'DEFAULT EDI', 'DEFAULT NPI', 'DEFAULT FACILITY NAME', 'DEFAULT FACILITY NPI',
    'DEFAULT PAY-TO NAME', 'DEFAULT PAY-TO ADDRESS', 'DEFAULT PAY-TO CITY',
    'DEFAULT PAY-TO STATE', 'DEFAULT PAY-TO ZIP', 'NO ADDRESS', 'NO CITY',
    'NO STATE', 'NO ZIP', 'NO TAX ID', 'NONE'
])

string_types = (str,)

def _get_value_from_sources(source_dicts, keys):
    # Accept a single key or an ordered list/tuple of keys; scan in priority order
    if not isinstance(keys, (list, tuple)):
        keys = [keys]
    for key in keys:
        for d in source_dicts:
            try:
                if isinstance(d, dict) and key in d:
                    val = d.get(key)
                    if val not in [None, '']:
                        return val
            except Exception:
                pass
    return None

def legacy_require_config_value(source_dicts, key, default_value, context_label, config, endpoint=None, allow_default_in_test=True):
    """
    Fetch a configuration value from one or more dicts.
    - `key` may be a string or a list/tuple of keys to try in order (primary, secondary, ...).
    - If found and equals a known placeholder, allow only in TestMode.
    - If missing, allow default only in TestMode (when allow_default_in_test is True).
    - Otherwise raise ValueError to prevent generating malformed 837p.
    
    TODO Eventually we should get this functionality into configloader in MediCafe so that we can use it in other places.
    """
    value = _get_value_from_sources(source_dicts, key)
    key_label = key if isinstance(key, string_types) else "/".join([k for k in key if isinstance(k, string_types)])
    # Found a value
    if value not in [None, '']:
        if isinstance(value, str) and value in DEFAULT_PLACEHOLDER_VALUES:
            if _is_test_mode(config):
                try:
                    MediLink_ConfigLoader.log("TEST MODE: Placeholder used for {} -> {}".format(key_label, value), level="WARNING")
                except Exception:
                    pass
                print("TEST MODE: Using placeholder '{}' for {} ({})".format(value, key_label, context_label))
                return value
            else:
                msg = "Missing real value for '{}' in {}. Found placeholder '{}'. Endpoint: {}".format(key_label, context_label, value, (endpoint or ''))
                try:
                    MediLink_ConfigLoader.log(msg, level="CRITICAL")
                except Exception:
                    pass
                raise ValueError(msg)
        return value
    # Missing value entirely
    if allow_default_in_test and _is_test_mode(config):
        try:
            MediLink_ConfigLoader.log("TEST MODE: Default used for {} -> {}".format(key_label, default_value), level="WARNING")
        except Exception:
            pass
        print("TEST MODE: Using default '{}' for {} ({})".format(default_value, key_label, context_label))
        return default_value
    msg = "Required configuration '{}' missing for {}. Endpoint: {}".format(key_label, context_label, (endpoint or ''))
    try:
        MediLink_ConfigLoader.log(msg, level="CRITICAL")
    except Exception:
        pass
    raise ValueError(msg)