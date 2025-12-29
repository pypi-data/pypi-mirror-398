# MediLink_837p_cob_library.py
"""
837P Coordination of Benefits (COB) Enhancement Library

This module provides enhanced 837P generation capabilities for:
- Medicare as primary payer (SBR09 = MB/MA)
- Secondary payer claims with embedded COB adjudication
- Optional attachment references (PWK)
- 835-derived adjudication embedding

All functions are currently implemented as placeholder comments to preserve
existing production functionality while providing clear implementation guidance.

IMPLEMENTATION STRATEGY:
1. All functions are commented placeholders to avoid disrupting production code
2. Detailed implementation guidance is provided in comments
3. Integration points are marked with TODO comments in the main encoder
4. Validation logic is included for claim integrity and compliance
5. Medicare-specific payer types (MB/MA) are properly handled
6. 835 data extraction and validation is supported
7. COB loops (2320, 2330B, 2330C, 2430) are fully specified

Key Implementation Notes:
- Medicare Part B uses SBR09 = "MB"
- Medicare Advantage uses SBR09 = "MA" 
- Secondary claims require SBR01 = "S" and proper COB loops
- 835 data integration requires validation of remittance dates and amounts
- SNIP validation level 3+ recommended for COB claims
- Total paid validation: AMT*D in Loop 2320 must match sum of SVD02 values
- CLM05-3 must be "1" (original) for secondary claims unless replacement logic applies

SEGMENT ORDER CONSTRAINTS:
- 1000A: Submitter
- 1000B: Receiver  
- 2000A?2010AA: Billing provider
- 2000B?2010BA/BB: Subscriber and payer
- 2300: Claim
- 2320: Other subscriber info (COB)
- 2330B: Prior payer
- 2400: Service line
- 2430: Line-level COB (if applicable)

VALIDATION REQUIREMENTS:
- SBR09 required if SBR01 = "S"
- NM1*PR in 2330B must match Medicare Payer ID when applicable
- CLM segment must reflect consistent claim frequency and COB type
- 835-derived data must contain remittance date and paid amount per service
- Multi-payer COB handling must be configured appropriately
"""

from datetime import datetime
import sys, os

# Use core utilities for standardized imports
from MediCafe.core_utils import get_shared_config_loader
MediLink_ConfigLoader = get_shared_config_loader()

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.append(project_dir)

# Import utility functions - absolute imports only
try:
    from MediLink_837p_utilities import convert_date_format
except ImportError as e:
    # Fallback implementation for convert_date_format if utilities module is not available
    MediLink_ConfigLoader.log("Warning: Could not import utilities functions: {}".format(e), level="WARNING")
    def convert_date_format(date_str):
        """Fallback date format conversion function"""
        try:
            # Parse the input date string into a datetime object
            input_format = "%m-%d-%Y" if len(date_str) == 10 else "%m-%d-%y"
            date_obj = datetime.strptime(date_str, input_format)
            # Format the datetime object into the desired output format
            return date_obj.strftime("%Y%m%d")
        except (ValueError, TypeError):
            # Return original string if conversion fails
            return date_str

def create_2320_other_subscriber_segments(patient_data, config, crosswalk):
    """
    Creates Loop 2320 segments for other subscriber information in COB scenarios.
    
    Required segments:
    - SBR: Primary payer relationship (other subscriber perspective)
    - AMT: AMT*D ? Total amount paid by Medicare or other primary
    - CAS: Patient liability (CO/PR adjustments)
    - OI: Other insurance coverage indicator
    
    Parameters:
    - patient_data: Dictionary containing patient and COB information
    - config: Configuration settings
    - crosswalk: Crosswalk data for payer mapping
    
    Returns:
    - List of 2320 loop segments
    """
    segments = []
    
    # Determine if this is a secondary claim
    is_secondary = patient_data.get('claim_type', 'primary') == 'secondary'
    
    if is_secondary:
        # TODO (DATA CONTRACT): If 835-derived fields are present on patient_data, prefer them:
        # - total_paid -> AMT*D
        # - cas_adjustments -> CAS
        # Otherwise accept 'primary_paid_amount' and 'cas_adjustments' provided by upstream workflow.
        # SBR segment for primary payer (other subscriber perspective)
        responsibility_code = "P"  # Primary payer from "other subscriber" perspective
        insurance_type = determine_insurance_type_code(patient_data, config, use_prior_payer=True)
        
        sbr_segment = "SBR*{}*18*******{}~".format(responsibility_code, insurance_type)
        segments.append(sbr_segment)
        
        # AMT*D segment for total amount paid by primary
        # TODO (STRICT MODE): When config['MediLink_Config']['cob_settings']['validation_level'] >= 2,
        # require presence of a numeric total (from 'total_paid' or 'primary_paid_amount').
        total_paid = patient_data.get('total_paid', patient_data.get('primary_paid_amount', '0.00'))
        amt_segment = "AMT*D*{}~".format(total_paid)
        segments.append(amt_segment)
        
        # CAS segments for patient liability adjustments
        cas_adjustments = patient_data.get('cas_adjustments', [])
        for adjustment in cas_adjustments:
            cas_segment = "CAS*{}*{}*{}~".format(
                adjustment.get('group', 'CO'),
                adjustment.get('reason', ''),
                adjustment.get('amount', '0.00')
            )
            segments.append(cas_segment)
        
        # OI segment for other insurance coverage
        oi_segment = "OI***Y***Y~"
        segments.append(oi_segment)
    
    return segments

def create_2330B_prior_payer_segments(patient_data, config, crosswalk):
    """
    Creates Loop 2330B segments for prior payer information.
    
    Required segments:
    - NM1: Prior payer name and ID (e.g., Medicare = 00850)
    - N3: (optional) Address line 1 and 2
    - N4: (optional) City/State/ZIP
    - REF: (optional) Reference ID (e.g., prior auth)
    
    Parameters:
    - patient_data: Dictionary containing prior payer information
    - config: Configuration settings
    - crosswalk: Crosswalk data for payer mapping
    
    Returns:
    - List of 2330B loop segments
    """
    segments = []
    
    # Get prior payer information
    # TODO (CONFIG): Resolve Medicare payer ID from config['MediLink_Config']['cob_settings']['medicare_payer_ids'] if prior_payer_id not provided.
    prior_payer_name = patient_data.get('prior_payer_name', 'MEDICARE')
    prior_payer_id = patient_data.get('prior_payer_id', '00850')
    
    # NM1 segment for prior payer
    nm1_segment = "NM1*PR*2*{}*****PI*{}~".format(prior_payer_name, prior_payer_id)
    segments.append(nm1_segment)
    
    # Optional N3 segment for address
    if patient_data.get('prior_payer_address'):
        n3_segment = "N3*{}*{}~".format(
            patient_data.get('prior_payer_address', ''),
            patient_data.get('prior_payer_address2', '')
        )
        segments.append(n3_segment)
    
    # Optional N4 segment for city/state/zip
    if patient_data.get('prior_payer_city'):
        n4_segment = "N4*{}*{}*{}~".format(
            patient_data.get('prior_payer_city', ''),
            patient_data.get('prior_payer_state', ''),
            patient_data.get('prior_payer_zip', '')
        )
        segments.append(n4_segment)
    
    # Optional REF segment for reference ID
    if patient_data.get('prior_auth_number'):
        ref_segment = "REF*G1*{}~".format(patient_data.get('prior_auth_number'))
        segments.append(ref_segment)
    
    return segments

def create_2430_service_line_cob_segments(patient_data, config, crosswalk):
    """
    Creates Loop 2430 segments for service line COB information.
    
    Required segments (when service-level adjudication exists):
    - SVD: Paid amount per service line (from 835 SVC03)
    - CAS: Line-level adjustments (from 835 CAS segments)
    - DTP: DTP*573 ? Adjudication date per service
    
    Parameters:
    - patient_data: Dictionary containing service line and adjudication data
    - config: Configuration settings
    - crosswalk: Crosswalk data for service mapping
    
    Returns:
    - List of 2430 loop segments
    """
    segments = []
    
    # Get service line adjudication data
    service_adjudications = patient_data.get('service_adjudications', [])
    
    for service in service_adjudications:
        # SVD segment for service line paid amount
        svd_segment = "SVD*{}*{}*{}*{}~".format(
            service.get('payer_id', '00850'),
            service.get('paid_amount', '0.00'),
            service.get('revenue_code', ''),
            service.get('units', '1')
        )
        segments.append(svd_segment)
        
        # CAS segments for line-level adjustments
        line_adjustments = service.get('adjustments', [])
        for adjustment in line_adjustments:
            cas_segment = "CAS*{}*{}*{}~".format(
                adjustment.get('group', 'CO'),
                adjustment.get('reason', ''),
                adjustment.get('amount', '0.00')
            )
            segments.append(cas_segment)
        
        # DTP*573 segment for adjudication date
        if service.get('adjudication_date'):
            dtp_segment = "DTP*573*D8*{}~".format(
                convert_date_format(service.get('adjudication_date'))
            )
            segments.append(dtp_segment)
    
    return segments

def create_2330C_other_subscriber_name_segments(patient_data, config, crosswalk):
    """
    Creates Loop 2330C segments when patient is not the subscriber.
    
    Required segments:
    - NM1*IL: Other Subscriber Name
    - N3/N4: (optional) Address
    - DMG: (optional) Date of birth / gender
    
    Parameters:
    - patient_data: Dictionary containing other subscriber information
    - config: Configuration settings
    - crosswalk: Crosswalk data for subscriber mapping
    
    Returns:
    - List of 2330C loop segments
    """
    segments = []
    
    # Check if patient is different from subscriber
    if patient_data.get('patient_is_subscriber', True) == False:
        # NM1*IL segment for other subscriber
        nm1_segment = "NM1*IL*1*{}*{}*{}***MI*{}~".format(
            patient_data.get('subscriber_last_name', ''),
            patient_data.get('subscriber_first_name', ''),
            patient_data.get('subscriber_middle_name', ''),
            patient_data.get('subscriber_policy_number', '')
        )
        segments.append(nm1_segment)
        
        # Optional N3 segment for address
        if patient_data.get('subscriber_address'):
            n3_segment = "N3*{}*{}~".format(
                patient_data.get('subscriber_address', ''),
                patient_data.get('subscriber_address2', '')
            )
            segments.append(n3_segment)
        
        # Optional N4 segment for city/state/zip
        if patient_data.get('subscriber_city'):
            n4_segment = "N4*{}*{}*{}~".format(
                patient_data.get('subscriber_city', ''),
                patient_data.get('subscriber_state', ''),
                patient_data.get('subscriber_zip', '')
            )
            segments.append(n4_segment)
        
        # Optional DMG segment for date of birth/gender
        if patient_data.get('subscriber_dob'):
            dmg_segment = "DMG*D8*{}*{}~".format(
                convert_date_format(patient_data.get('subscriber_dob')),
                patient_data.get('subscriber_gender', '')
            )
            segments.append(dmg_segment)
    
    return segments

def create_pwk_attachment_segment(patient_data, config):
    """
    Creates PWK segment for attachment references (non-electronic EOB handling).
    
    Example: PWK*EB*FX*123456~
    
    Parameters:
    - patient_data: Dictionary containing attachment information
    - config: Configuration settings
    
    Returns:
    - PWK segment string or None if not required
    """
    # Check if attachment is required
    if patient_data.get('requires_attachment', False):
        report_type = patient_data.get('attachment_report_type', 'EB')  # EB = Explanation of Benefits
        transmission_code = patient_data.get('attachment_transmission_code', 'FX')  # FX = Fax
        control_number = patient_data.get('attachment_control_number', '')
        
        if control_number:
            pwk_segment = "PWK*{}*{}*{}~".format(report_type, transmission_code, control_number)
            return pwk_segment
    
    return None

def validate_cob_claim_integrity(patient_data, config):
    """
    Validates COB claim integrity and compliance.
    
    Validation checks:
    - SBR09 required if SBR01 = "S"
    - NM1*PR in 2330B must match Medicare Payer ID when applicable
    - CLM segment must reflect consistent claim frequency and COB type
    - Total paid validation: AMT*D in Loop 2320 matches sum of SVD02 values
    
    Parameters:
    - patient_data: Dictionary containing claim data
    - config: Configuration settings
    
    Returns:
    - Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Validate SBR09 for secondary claims
    if patient_data.get('claim_type') == 'secondary':
        insurance_type = determine_medicare_payer_type(patient_data, config)
        if not insurance_type:
            errors.append("SBR09 required when SBR01 = S (secondary claim)")
    
    # Validate Medicare Payer ID
    if patient_data.get('prior_payer_id') == '00850':  # Medicare
        if patient_data.get('prior_payer_name') != 'MEDICARE':
            errors.append("NM1*PR must match Medicare Payer ID 00850")
    
    # Validate claim frequency for COB claims
    if patient_data.get('claim_type') == 'secondary':
        claim_frequency = patient_data.get('claim_frequency', '1')
        if claim_frequency != '1':
            errors.append("CLM05-3 must be '1' for original COB claims")
    
    # Validate total paid amount
    amt_d_total = float(patient_data.get('primary_paid_amount', '0.00'))
    svd_amounts = [float(s.get('paid_amount', '0.00')) for s in patient_data.get('service_adjudications', [])]
    if abs(amt_d_total - sum(svd_amounts)) > 0.01:  # Allow for rounding differences
        errors.append("AMT*D total must match sum of SVD02 amounts")
    
    return len(errors) == 0, errors

def extract_835_adjudication_data(patient_data, config):
    """
    Extracts and validates 835-derived adjudication data for COB embedding.
    
    Extracts:
    - CLP02 ? AMT*D (2320)
    - CAS segments ? CAS (2320 and/or 2430)
    - SVC03 ? SVD02 (2430)
    - DTP segments ? DTP*573 (2430)
    
    Parameters:
    - patient_data: Dictionary containing 835 data
    - config: Configuration settings
    
    Returns:
    - Dictionary of extracted adjudication data or None if invalid
    """
    adjudication_data = {}
    
    # Extract total paid amount from CLP02
    adjudication_data['total_paid'] = patient_data.get('clp02_amount', '0.00')
    
    # Extract CAS adjustments
    cas_adjustments = patient_data.get('cas_segments', [])
    adjudication_data['cas_adjustments'] = []
    for cas in cas_adjustments:
        adjustment = {
            'group': cas.get('group', 'CO'),
            'reason': cas.get('reason', ''),
            'amount': cas.get('amount', '0.00')
        }
        adjudication_data['cas_adjustments'].append(adjustment)
    
    # Extract service line paid amounts from SVC03
    service_adjudications = patient_data.get('svc_segments', [])
    adjudication_data['service_paid_amounts'] = []
    for svc in service_adjudications:
        service = {
            'payer_id': svc.get('payer_id', '00850'),
            'paid_amount': svc.get('paid_amount', '0.00'),
            'revenue_code': svc.get('revenue_code', ''),
            'units': svc.get('units', '1'),
            'adjudication_date': svc.get('adjudication_date', ''),
            'adjustments': svc.get('adjustments', [])
        }
        adjudication_data['service_paid_amounts'].append(service)
    
    # Validate 835 structure
    if not validate_835_structure(patient_data):
        return None
    
    return adjudication_data

def validate_835_structure(patient_data):
    """
    Validates that 835 data has required structure for COB processing.
    
    Parameters:
    - patient_data: Dictionary containing 835 data
    
    Returns:
    - Boolean indicating if 835 structure is valid
    """
    required_fields = ['clp02_amount', 'cas_segments', 'svc_segments']
    
    for field in required_fields:
        if field not in patient_data:
            return False
    
    return True

def determine_medicare_payer_type(patient_data, config, use_prior_payer=False):
    """
    Determines Medicare payer type for proper SBR09 assignment.
    
    Parameters:
    - patient_data: Dictionary containing payer information
    - config: Configuration settings
    - use_prior_payer: If True, check prior_payer_id instead of payer_id (default: False)
    
    Returns:
    - "MB" for Medicare Part B
    - "MA" for Medicare Advantage
    - None if not Medicare
    """
    if use_prior_payer:
        payer_id = patient_data.get('prior_payer_id', '')
        medicare_advantage_flag = patient_data.get('prior_payer_medicare_advantage', False)
    else:
        payer_id = patient_data.get('payer_id', '')
        medicare_advantage_flag = patient_data.get('medicare_advantage', False)
    
    if payer_id == "00850":  # Medicare
        # Check if this is Medicare Advantage
        if medicare_advantage_flag:
            return "MA"
        else:
            return "MB"
    
    return None

def determine_insurance_type_code(patient_data, config, use_prior_payer=False):
    """
    Determines insurance type code for SBR09, with Medicare-specific handling.
    
    This function consolidates the insurance type determination logic used
    in both Loop 2000B and Loop 2320 SBR segment creation.
    
    Parameters:
    - patient_data: Dictionary containing payer information
    - config: Configuration settings
    - use_prior_payer: If True, determine type for prior payer (Loop 2320),
                       otherwise for current payer (Loop 2000B) (default: False)
    
    Returns:
    - Insurance type code string (e.g., "MB", "MA", "18", etc.)
    """
    # Determine Medicare payer type with appropriate context
    medicare_type = determine_medicare_payer_type(patient_data, config, use_prior_payer=use_prior_payer)
    if medicare_type:
        return medicare_type
    
    # Fall back to insurance type from patient_data
    if use_prior_payer:
        insurance_type = patient_data.get('prior_payer_insurance_type', patient_data.get('insurance_type', '18'))
    else:
        insurance_type = patient_data.get('insurance_type', '18')
    
    return insurance_type

def create_enhanced_sbr_segment(patient_data, config, crosswalk):
    """
    Enhanced SBR segment creation supporting secondary indicators and Medicare payer types.
    
    Enhancement:
    - Support secondary indicator (SBR01 = "S")
    - Proper payer type in SBR09 ("MB" for Medicare Part B, "MA" for Medicare Advantage)
    
    Parameters:
    - patient_data: Dictionary containing patient and payer information
    - config: Configuration settings
    - crosswalk: Crosswalk data for payer mapping
    
    Returns:
    - Enhanced SBR segment string
    """
    # Determine responsibility code
    responsibility_code = "S" if patient_data.get('claim_type') == 'secondary' else "P"
    
    # Determine insurance type code using shared helper (for current/secondary payer)
    insurance_type = determine_insurance_type_code(patient_data, config, use_prior_payer=False)
        
    sbr_segment = "SBR*{}*18*******{}~".format(responsibility_code, insurance_type)
    
    return sbr_segment

def create_enhanced_clm_segment(patient_data):
    """
    Enhanced CLM segment creation ensuring proper claim frequency for COB.
    
    Enhancement:
    - Ensure CLM05-3 is explicitly set to "1" (original) for secondary claims
    - Unless claim replacement logic applies
    
    Parameters:
    - patient_data: Dictionary containing claim information
    
    Returns:
    - Enhanced CLM segment string
    """
    # Get claim details
    claim_number = patient_data.get('CHART', '')
    amount = patient_data.get('AMOUNT', '0.00')
    type_of_service = patient_data.get('TOS', '')
    
    # Determine claim frequency
    if patient_data.get('claim_type') == 'secondary':
        claim_frequency = "1"  # Original for secondary claims
    else:
        claim_frequency = patient_data.get('claim_frequency', '1')
    
    clm_segment = "CLM*{}*{}***{}:B:{}*Y*A*Y*Y~".format(
        claim_number, amount, type_of_service, claim_frequency)
    
    return clm_segment

def validate_cob_multi_payer_handling(patient_data, config):
    """
    Validates COB multi-payer handling configuration.
    
    Mode: single_payer_only (Options: single_payer_only, multi_payer_supported)
    Rejection action: raise configuration error if >1 COB payer detected
    
    Parameters:
    - patient_data: Dictionary containing COB payer information
    - config: Configuration settings
    
    Returns:
    - Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Count COB payers
    cob_payers = len(patient_data.get('cob_payers', []))
    cob_mode = get_cob_configuration(config).get('cob_mode', 'single_payer_only')
    
    if cob_payers > 1 and cob_mode == 'single_payer_only':
        errors.append("Multiple COB payers detected but single_payer_only mode enabled")
    
    return len(errors) == 0, errors

def log_cob_validation_results(validation_results, config):
    """
    Logs COB validation results for audit and debugging.
    
    Parameters:
    - validation_results: Dictionary containing validation results
    - config: Configuration settings
    """
    for validation_type, result in validation_results.items():
        if result['is_valid']:
            MediLink_ConfigLoader.log("COB validation passed: {}".format(validation_type), config, level="INFO")
        else:
            MediLink_ConfigLoader.log("COB validation failed: {}".format(validation_type), config, level="ERROR")
            for error in result['errors']:
                MediLink_ConfigLoader.log("  - {}".format(error), config, level="ERROR")

# Configuration enhancement functions

def get_cob_configuration(config):
    """
    Retrieves COB-specific configuration settings.
    
    Parameters:
    - config: Main configuration dictionary
    
    Returns:
    - COB configuration dictionary
    """
    from MediCafe.core_utils import extract_medilink_config
    medi = extract_medilink_config(config)
    cob_config = medi.get('cob_settings', {})
    return cob_config

def validate_cob_configuration(config):
    """
    Validates COB configuration completeness and correctness.
    
    Parameters:
    - config: Configuration settings
    
    Returns:
    - Tuple of (is_valid, error_messages)
    """
    errors = []
    
    cob_config = get_cob_configuration(config)
    required_fields = ['medicare_payer_ids', 'cob_mode', 'validation_level']
    
    for field in required_fields:
        if field not in cob_config:
            errors.append("Missing required COB configuration field: {}".format(field))
    
    return len(errors) == 0, errors

# Insurance type code enhancement

def get_enhanced_insurance_options(config):
    """
    Retrieves enhanced insurance options including Medicare-specific codes.
    
    Parameters:
    - config: Configuration settings
    
    Returns:
    - Enhanced insurance options dictionary
    """
    from MediCafe.core_utils import extract_medilink_config
    medi = extract_medilink_config(config)
    base_options = medi.get('insurance_options', {})
    medicare_options = {
        'MB': 'Medicare Part B',
        'MA': 'Medicare Advantage',
        'MC': 'Medicare Part C'
    }
    enhanced_options = base_options.copy()
    enhanced_options.update(medicare_options)
    return enhanced_options

# Main COB processing function

def process_cob_claim(patient_data, config, crosswalk, client):
    """
    Main function for processing COB claims with enhanced 837P generation.
    
    This function orchestrates the creation of all COB-related segments
    and validates the complete claim for compliance.
    
    Parameters:
    - patient_data: Dictionary containing patient and COB information
    - config: Configuration settings
    - crosswalk: Crosswalk data for mapping
    - client: API client for external data retrieval
    
    Returns:
    - List of all 837P segments including COB enhancements
    """
    segments = []
    
    # 1. Validate COB configuration
    is_valid, errors = validate_cob_configuration(config)
    if not is_valid:
        raise ValueError("Invalid COB configuration: {}".format(errors))
    
    # 2. Extract 835 adjudication data if available
    adjudication_data = extract_835_adjudication_data(patient_data, config)
    if adjudication_data:
        # Merge 835 data into patient_data
        patient_data.update(adjudication_data)
    
    # 3. Note: Loop 2000B SBR segment should be created by main encoder
    # (create_sbr_segment() in encoder_library), not here, to avoid duplication.
    # This function only creates COB-specific loops (2320, 2330B, 2330C, 2430).
    
    # 4. Create 2320 other subscriber segments if COB
    if patient_data.get('claim_type') == 'secondary':
        segments.extend(create_2320_other_subscriber_segments(patient_data, config, crosswalk))
    
    # 5. Create 2330B prior payer segments
    segments.extend(create_2330B_prior_payer_segments(patient_data, config, crosswalk))
    
    # 6. Create 2330C other subscriber segments if patient != subscriber
    if not patient_data.get('patient_is_subscriber', True):
        segments.extend(create_2330C_other_subscriber_name_segments(patient_data, config, crosswalk))
    
    # 7. Create enhanced CLM segment
    enhanced_clm = create_enhanced_clm_segment(patient_data, config, crosswalk)
    if enhanced_clm:
        segments.append(enhanced_clm)
    
    # 8. Create 2430 service line COB segments if service-level adjudication
    if patient_data.get('service_adjudications'):
        segments.extend(create_2430_service_line_cob_segments(patient_data, config, crosswalk))
    
    # 9. Create PWK attachment segment if required
    pwk_segment = create_pwk_attachment_segment(patient_data, config)
    if pwk_segment:
        segments.append(pwk_segment)
    
    # 10. Validate final claim integrity
    is_valid, errors = validate_cob_claim_integrity(patient_data, config)
    if not is_valid:
        raise ValueError("COB claim validation failed: {}".format(errors))
    
    # 11. Log validation results
    log_cob_validation_results({'integrity': {'is_valid': is_valid, 'errors': errors}}, config)
    
    return segments 

# Configuration Documentation and Examples

"""
COB CONFIGURATION STRUCTURE

The COB library requires specific configuration settings to be added to the main config.json file.
Below is the recommended structure for COB configuration:

{
  "MediLink_Config": {
    "cob_settings": {
      "medicare_payer_ids": ["00850"],
      "cob_mode": "single_payer_only",
      "validation_level": 3,
      "medicare_advantage_identifiers": ["MA", "MC"],
      "default_medicare_type": "MB",
      "require_835_validation": true,
      "attachment_handling": {
        "enable_pwk_segments": true,
        "default_report_type": "EB",
        "default_transmission_code": "FX"
      },
      "service_level_adjudication": {
        "enable_2430_loop": true,
        "require_adjudication_date": true,
        "validate_paid_amounts": true
      },
      "validation_rules": {
        "require_sbr09_for_secondary": true,
        "validate_medicare_payer_id": true,
        "require_claim_frequency_1": true,
        "validate_total_paid_amount": true
      }
    },
    "insurance_options": {
      "MB": "Medicare Part B",
      "MA": "Medicare Advantage", 
      "MC": "Medicare Part C",
      "18": "Medicare",
      "12": "Medicaid",
      "16": "Self Pay"
    }
  }
}

COB INTEGRATION GUIDE

1. DATA STRUCTURE REQUIREMENTS

Patient data for COB claims should include:
- claim_type: "primary" or "secondary" (required for secondary claims)
- payer_id: Payer identifier for CURRENT/SECONDARY payer (e.g., secondary payer receiving this claim)
- medicare_advantage: Boolean indicating if CURRENT payer is Medicare Advantage (for Loop 2000B SBR)
- insurance_type: Insurance type code for CURRENT payer (defaults to '18' if not Medicare)
- prior_payer_id: Primary payer ID (e.g., "00850" for Medicare) - required for Loop 2320 SBR
- prior_payer_name: Name of prior payer (e.g., "MEDICARE")
- prior_payer_insurance_type: Optional - insurance type code for PRIMARY payer (defaults to '18' if not Medicare)
- prior_payer_medicare_advantage: Optional - boolean for Medicare Advantage determination of PRIMARY payer
- primary_paid_amount: Amount paid by primary payer
- cas_adjustments: List of adjustment objects
- service_adjudications: List of service-level adjudication data
- patient_is_subscriber: Boolean indicating if patient is subscriber
- requires_attachment: Boolean indicating if attachment required

Note: Clear separation between payer contexts:
- payer_id, medicare_advantage, insurance_type = CURRENT/SECONDARY payer (Loop 2000B)
- prior_payer_id, prior_payer_medicare_advantage, prior_payer_insurance_type = PRIMARY payer (Loop 2320)

2. 835 DATA INTEGRATION

For 835-derived adjudication data, include:
- clp02_amount: Total amount paid by primary
- cas_segments: List of CAS adjustment segments
- svc_segments: List of service line segments with:
  - payer_id: Payer identifier
  - paid_amount: Amount paid for service
  - revenue_code: Revenue code
  - units: Number of units
  - adjudication_date: Date of adjudication
  - adjustments: List of line-level adjustments

3. VALIDATION REQUIREMENTS

The library performs comprehensive validation:
- SBR09 required for secondary claims
- Medicare payer ID validation
- Claim frequency validation
- Total paid amount validation
- 835 data structure validation

4. INTEGRATION POINTS

Key integration points in the main encoder:
- Enhanced SBR segment creation
- COB loop processing (2320, 2330B, 2330C, 2430)
- Enhanced CLM segment creation
- PWK attachment segment creation

5. ERROR HANDLING

The library provides detailed error messages for:
- Configuration validation failures
- Claim integrity violations
- 835 data structure issues
- Medicare payer type determination failures

6. LOGGING

Comprehensive logging is provided for:
- COB validation results
- Configuration validation
- Claim processing steps
- Error conditions

7. FUTURE ENHANCEMENTS

Planned enhancements include:
- Multi-payer COB support
- Advanced 835 data extraction
- Enhanced validation rules
- Attachment workflow integration
- Real-time payer verification

USAGE EXAMPLE

# Basic COB claim processing (Medicare primary, secondary payer)
patient_data = {
    'claim_type': 'secondary',
    # Current/Secondary payer information (for Loop 2000B SBR)
    'payer_id': '87726',  # Secondary payer receiving this claim
    'medicare_advantage': False,  # For secondary payer (if applicable)
    'insurance_type': '18',  # For secondary payer (if not Medicare)
    # Primary payer information (for Loop 2320 SBR)
    'prior_payer_id': '00850',  # Medicare primary payer
    'prior_payer_name': 'MEDICARE',
    'prior_payer_medicare_advantage': False,  # Medicare Part B (not Advantage)
    'prior_payer_insurance_type': '18',  # Optional, defaults to '18' if not Medicare
    # COB adjudication data
    'primary_paid_amount': '150.00',
    'cas_adjustments': [
        {'group': 'CO', 'reason': '45', 'amount': '25.00'}
    ],
    'service_adjudications': [
        {
            'payer_id': '00850',  # Primary payer ID
            'paid_amount': '125.00',
            'revenue_code': '0001',
            'units': '1',
            'adjudication_date': '01-15-2024',
            'adjustments': []
        }
    ]
}

# Process COB claim
cob_segments = process_cob_claim(patient_data, config, crosswalk, client)

# Validate configuration
is_valid, errors = validate_cob_configuration(config)
if not is_valid:
    print("Configuration errors:", errors)

# Get enhanced insurance options
insurance_options = get_enhanced_insurance_options(config)
""" 