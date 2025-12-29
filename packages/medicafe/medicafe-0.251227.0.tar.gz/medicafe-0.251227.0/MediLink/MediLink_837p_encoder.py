# MediLink_837p_encoder.py
import re, argparse, os, sys
from datetime import datetime

# Add workspace directory to Python path for MediCafe imports
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(current_dir)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

# Use core utilities for standardized imports and path setup
from MediCafe.core_utils import get_shared_config_loader, get_api_client, setup_module_paths, extract_medilink_config
setup_module_paths(__file__)

MediLink_ConfigLoader = get_shared_config_loader()

# Import api_core for API client fallback
try:
    from MediCafe import api_core
except ImportError:
    api_core = None

# Import DataMgmt functions - absolute imports only
try:
    from MediLink_DataMgmt import parse_fixed_width_data, read_fixed_width_data
except ImportError:
    from MediLink.MediLink_DataMgmt import parse_fixed_width_data, read_fixed_width_data

# Import encoder library - absolute imports only
try:
    import MediLink_837p_encoder_library
except ImportError:
    from MediLink import MediLink_837p_encoder_library

# TODO (COB ENHANCEMENT): Import COB library when implementing Medicare and secondary claim support
# import MediLink_837p_cob_library
#from tqdm import tqdm
# Optional COB library import for low-risk validation/logging
try:
    import MediLink_837p_cob_library as COB
except (ImportError, SystemError):
    COB = None

def format_single_claim(patient_data, config, endpoint, transaction_set_control_number, crosswalk, client):
    """
    Formats a single claim into 837P segments based on the provided patient data and endpoint.
    
    Parameters:
    - patient_data: Dictionary containing detailed patient data.
    - config: Configuration settings loaded from a JSON file.
    - endpoint: The endpoint key representing the specific endpoint.
    - transaction_set_control_number: Starting transaction set control number for 837P segments.
    
    Returns:
    - String representation of the formatted 837P claim.
    """
    # Pre-resolve and enrich with Payer Name and ID for special case handling like Florida Blue.
    patient_data = MediLink_837p_encoder_library.payer_id_to_payer_name(patient_data, config, endpoint, crosswalk, client)

    # Low-risk: Log-only COB configuration validation for secondary claims (does not alter behavior)
    if COB is not None and patient_data.get('claim_type') == 'secondary':
        try:
            is_valid, errors = COB.validate_cob_configuration(config)
            if not is_valid:
                MediLink_ConfigLoader.log("COB configuration incomplete: {}".format(errors), config, level="WARNING")
        except Exception as e:
            MediLink_ConfigLoader.log("COB validation check failed: {}".format(str(e)), config, level="WARNING")
    
    segments = []
        
    # Initialize with standard segments for all claims
    segments.append(MediLink_837p_encoder_library.create_st_segment(transaction_set_control_number))
    segments.append(MediLink_837p_encoder_library.create_bht_segment(patient_data))

    # Submitter Name Segment and PER Contact Information (1000A Loop)
    segments.extend(MediLink_837p_encoder_library.create_1000A_submitter_name_segment(patient_data, config, endpoint))
    
    # Receiver Name Segment (1000B Loop)
    segments.extend([MediLink_837p_encoder_library.create_1000B_receiver_name_segment(config, endpoint)])
    
    # Billing Provider Segments (2010AA Loop)
    segments.extend([MediLink_837p_encoder_library.create_hl_billing_provider_segment()])
    segments.extend(MediLink_837p_encoder_library.create_nm1_billing_provider_segment(config, endpoint))

    # Pay-To Address Segment (2010AB Loop) if the Pay-To Address differs from the Billing Provider's address
    #segments.extend(MediLink_837p_encoder_library.create_nm1_payto_address_segments(config))
    
    # PRV Provider Taxonomy Segment
    #segments.extend([MediLink_837p_encoder_library.create_billing_prv_segment(config, endpoint)])
    
    # Subscriber information, possibly including endpoint-specific logic
    segments.extend(MediLink_837p_encoder_library.create_hl_subscriber_segment())
    
    # TODO (COB ENHANCEMENT): Enhanced SBR segment creation for COB scenarios
    # Replace the standard SBR segment creation with enhanced COB-aware version
    # Current: segments.append(MediLink_837p_encoder_library.create_sbr_segment(config, patient_data, endpoint))
    # Enhanced: 
    # if patient_data.get('claim_type') == 'secondary':
    #     enhanced_sbr = MediLink_837p_cob_library.create_enhanced_sbr_segment(patient_data, config, crosswalk)
    #     segments.append(enhanced_sbr)
    # else:
    #     segments.append(MediLink_837p_encoder_library.create_sbr_segment(config, patient_data, endpoint))
    segments.append(MediLink_837p_encoder_library.create_sbr_segment(config, patient_data, endpoint))
    
    segments.append(MediLink_837p_encoder_library.create_nm1_subscriber_segment(config, patient_data, endpoint))
    segments.extend(MediLink_837p_encoder_library.create_subscriber_address_segments(patient_data))
    segments.append(MediLink_837p_encoder_library.create_dmg_segment(patient_data))
    
    # Payer information (2010BB loop)
    # TODO This function now includes detailed outputs and potential user interactions with the new implementation.
    # The new implementation introduces user inputs directly in the flow, which could disrupt automated batch processes. 
    # Ensure that there are mechanisms or workflows in place to handle such interruptions appropriately.
    segments.extend([MediLink_837p_encoder_library.create_2010BB_payer_information_segment(patient_data)])
    #segments.extend(MediLink_837p_encoder_library.create_payer_address_segments(config)) OMITTED
    
    # TODO (COB ENHANCEMENT): COB processing for secondary claims and Medicare adjudication
    # See MediLink_837p_cob_library.process_cob_claim() for complete COB implementation
    # This would include:
    # - Enhanced SBR segments with Medicare payer types (MB/MA)
    # - 2320 loop for other subscriber information
    # - 2330B loop for prior payer (Medicare) information
    # - 2330C loop when patient != subscriber
    # - 2430 loop for service-level COB adjudication
    # - PWK segments for attachment references
    # 
    # Integration point for COB processing:
    # if patient_data.get('claim_type') == 'secondary' or patient_data.get('requires_cob_processing'):
    #     cob_segments = MediLink_837p_cob_library.process_cob_claim(patient_data, config, crosswalk, client)
    #     segments.extend(cob_segments)
    
    # Rendering Provider (2310B Loop)
    segments.extend(MediLink_837p_encoder_library.create_nm1_rendering_provider_segment(config))
    
    # TODO (COB ENHANCEMENT): Enhanced CLM segment creation for COB claims
    # Replace standard CLM creation with COB-aware version
    # Current: segments.extend(MediLink_837p_encoder_library.create_clm_and_related_segments(patient_data, config, crosswalk))
    # Enhanced:
    # if patient_data.get('claim_type') == 'secondary':
    #     enhanced_clm = MediLink_837p_cob_library.create_enhanced_clm_segment(patient_data, config, crosswalk)
    #     segments.append(enhanced_clm)
    #     # Add service line segments separately for COB
    #     segments.extend(MediLink_837p_encoder_library.create_service_line_segments(patient_data, config, crosswalk))
    # else:
    #     segments.extend(MediLink_837p_encoder_library.create_clm_and_related_segments(patient_data, config, crosswalk))
    
    # Claim information 2300, 2310C Service Facility and 2400 loop segments
    segments.extend(MediLink_837p_encoder_library.create_clm_and_related_segments(patient_data, config, crosswalk))

    # Placeholder for the SE segment to be updated with actual segment count later
    segments.append("SE**{transaction_set_control_number:04d}~")

    # Update SE segment with the actual segment count and generate the final formatted 837P string
    formatted_837p = MediLink_837p_encoder_library.generate_segment_counts('\n'.join(filter(None, segments)), transaction_set_control_number)

    # Optionally, print or log the formatted 837P for debugging or verification
    try:
        chart_number = patient_data.get("CHART", "UNDETECTED")  # Default to "UNDETECTED" if CHART is not found
    except Exception as e:
        chart_number = "UNDETECTED"  # Fallback in case of any error

    # Log the formatted 837P with the CHART number
    MediLink_ConfigLoader.log("Formatted 837P for endpoint {}. Chart Number: {}.".format(endpoint, chart_number), config, level="INFO")

    return formatted_837p

def write_output_file(document_segments, output_directory, endpoint_key, input_file_path, config, suffix=""):
    """
    Writes formatted 837P document segments to an output file with a dynamically generated name.

    Parameters:
    - document_segments: List of strings, where each string is a segment of the 837P document to be written.
    - output_directory: String specifying the directory where the output file will be saved.
    - endpoint_key: String specifying the endpoint for which the claim is processed, used in naming the output file.
    - input_file_path: String specifying the path to the input file being processed, used in naming the output file.
    - config: Configuration settings for logging and other purposes.
    - suffix: Optional string to differentiate filenames, useful for single-patient processing.

    Returns:
    - String specifying the path to the successfully created output file, or None if an error occurred.
    """
    # Ensure the document segments are not empty
    if not document_segments:
        MediLink_ConfigLoader.log("Error: Empty document segments provided. No output file created.", config, level="ERROR")
        return None
    
    # Verify the output directory exists and is writable, create if necessary
    if not os.path.exists(output_directory):
        try:
            os.makedirs(output_directory)
        except OSError as e:
            MediLink_ConfigLoader.log("Error: Failed to create output directory. {}".format(e), config, level="ERROR")
            return None
    elif not os.access(output_directory, os.W_OK):
        MediLink_ConfigLoader.log("Error: Output directory is not writable.", config, level="ERROR")
        return None
    
    # Generate the new output file path
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    timestamp = datetime.now().strftime("%m%d%H%M")
    new_output_file_name = "{}_{}_{}{}.txt".format(base_name, endpoint_key.lower(), timestamp, suffix)
    new_output_file_path = os.path.join(output_directory, new_output_file_name)

    # Write the document to the output file
    try:
        with open(new_output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(document_segments))
        MediLink_ConfigLoader.log("Successfully converted and saved to {}".format(new_output_file_path), config, level="INFO")
        return new_output_file_path
    except Exception as e:
        MediLink_ConfigLoader.log("Error: Failed to write output file. {}".format(e), config, level="ERROR")
        return None

def process_single_file(file_path, config, endpoint_key, transaction_set_control_number, crosswalk, client):
    """
    Process the claim data from a file into the 837P format.

    Args:
        file_path (str): The path to the file containing the claim data.
        config (dict): Configuration settings loaded from a JSON file.
        endpoint_key (str): The key representing the endpoint for which the claim is being processed.
        transaction_set_control_number (int): The starting transaction set control number for 837P segments.
        crosswalk (dict): Crosswalk data for payer information.
        client: API client for payer name resolution.

    Returns:
        tuple: A tuple containing the formatted claim segments and the next transaction set control number.
    """
    valid_claims, validation_errors = read_and_validate_claims(file_path, config)
    
    # Handle validation errors
    if validation_errors:
        if not MediLink_837p_encoder_library.handle_validation_errors(transaction_set_control_number, validation_errors, config):
            return None, transaction_set_control_number  # Halt processing if the user chooses

    # Process each valid claim
    formatted_claims, transaction_set_control_number = format_claims(valid_claims, config, endpoint_key, transaction_set_control_number, crosswalk, client)

    formatted_claims_str = '\n'.join(formatted_claims)  # Join formatted claims into a single string
    return formatted_claims_str, transaction_set_control_number

def read_and_validate_claims(file_path, config):
    """
    Read and validate claim data from a file.

    Args:
        file_path (str): The path to the file containing the claim data.
        config (dict): Configuration settings loaded from a JSON file.

    Returns:
        tuple: A tuple containing a list of valid parsed data and a list of validation errors.
    """
    valid_claims = []  # List to store valid parsed data
    validation_errors = []  # List to store validation errors

    # Iterate over data in the file
    for personal_info, insurance_info, service_info, service_info_2, service_info_3 in read_fixed_width_data(file_path):
        # Process reserved 5-line Medisoft record (currently using 3 lines, 2 reserved)
        medi_cfg = extract_medilink_config(config)
        parsed_data = parse_fixed_width_data(personal_info, insurance_info, service_info, service_info_2, service_info_3, medi_cfg)
        # Validate the parsed data
        try:
            is_valid, errors = validate_claim_data(parsed_data, config)
        except Exception as e:
            import traceback as _tb
            try:
                MediLink_ConfigLoader.log("validate_claim_data crashed: {}\n{}".format(e, _tb.format_exc()), config, level="ERROR")
            except Exception:
                pass
            raise
        if is_valid:
            valid_claims.append(parsed_data)  # Add valid data to the list
        else:
            validation_errors.append(errors)  # Add validation errors to the list
            # Log validation failure
            MediLink_ConfigLoader.log("Validation failed for claim data in file: {}. Errors: {}".format(file_path, errors), config, level="ERROR")

    return valid_claims, validation_errors

def format_claims(parsed_data_list, config, endpoint, starting_transaction_set_control_number, crosswalk, client):
    """
    Formats a list of parsed claim data into 837P segments.

    Parameters:
    - parsed_data_list: List of dictionaries containing parsed claim data.
    - config: Configuration settings loaded from a JSON file.
    - endpoint: The endpoint key representing the specific endpoint.
    - starting_transaction_set_control_number: Starting transaction set control number for 837P segments.
    - crosswalk: Crosswalk data for payer information.
    - client: API client for payer name resolution.

    Returns:
    - A list of formatted 837P claims and the next transaction set control number.
    """
    formatted_claims = []
    transaction_set_control_number = starting_transaction_set_control_number

    for parsed_data in parsed_data_list:
        formatted_claim = format_single_claim(parsed_data, config, endpoint, transaction_set_control_number, crosswalk, client)
        formatted_claims.append(formatted_claim)
        transaction_set_control_number += 1  # Increment for each successfully processed claim

    return formatted_claims, transaction_set_control_number

# Validation Function checks the completeness and correctness of each claim's data
def validate_claim_data(parsed_data, config, required_fields=[]):
    """
    Used by both paths. 
    
    Validates the completeness and correctness of each claim's data based on configurable requirements.

    Parameters:
    - parsed_data: Dictionary containing claim data to validate.
    - config: Configuration settings loaded from a JSON file.
    - required_fields: Optional list of tuples indicating required fields and their respective regex patterns for validation.

    Returns:
    - (bool, list): Tuple containing a boolean indicating whether the data is valid and a list of error messages if any.

    # TODO This required fields thing needs to be redone. 
    
    if required_fields is None:
        required_fields = [
            ('CHART', None),
            ('billing_provider_npi', r'^\\d{10}$'),
            ('IPOLICY', None),
            ('CODEA', None),
            ('DATE', r'^\\d{8}$'),
            ('AMOUNT', None),
            ('TOS', None),
            ('DIAG', None)
        ]
    """    
    errors = []
    MediLink_ConfigLoader.log("Starting claim data validation...")
    if not required_fields:
        # If no required fields are specified, assume validation is true
        return True, []
    
    expected_keys = {field[0] for field in required_fields}  # Set of expected field keys
    received_keys = set(parsed_data.keys())  # Set of keys present in the parsed data

    # Check if there is any intersection between expected keys and received keys
    if not expected_keys & received_keys:
        # Log the preview of expected and received keys
        preview_msg = "Validation skipped: No matching fields found between expected and received data."
        error_msg = "{}\nExpected keys: {}\nReceived keys: {}".format(preview_msg, expected_keys, received_keys)
        MediLink_ConfigLoader.log(error_msg, config, level="WARNING")
        print(error_msg)  # Optionally print to console for immediate feedback
        return True, [preview_msg]  # Return true to say that it's valid data anyway.

    # Check for missing or empty fields and validate patterns
    for field, pattern in required_fields:
        value = parsed_data.get(field)
        if not value:
            errors.append("Missing or empty field: {}".format(field))
        elif pattern and not re.match(pattern, value):
            errors.append("Invalid format in field {}: {}".format(field, value))

    # Validate date fields if required and ensure they are in the correct format
    date_field = 'DATE'
    date_value = parsed_data.get(date_field)
    if date_value:
        try:
            datetime.strptime(date_value, "%Y%m%d")
        except ValueError:
            errors.append("Invalid date format: {}".format(date_value))

    # Log validation errors and return
    if errors:
        for error in errors:
            MediLink_ConfigLoader.log(error, config, level="ERROR")
        return False, errors

    return True, []

def process_and_write_file(file_path, config, endpoint, crosswalk, client, starting_tscn=1):
    """        
    Process a single file, create complete 837P document with headers and trailers, and write to output file.

    Parameters:
    - file_path: Path to the .DAT file to be processed.
    - config: Configuration settings.
    - endpoint: Endpoint key.
    - crosswalk: Crosswalk data for payer information.
    - client: API client for payer name resolution.
    - starting_tscn: Starting Transaction Set Control Number.
    """
    print("Processing: {}".format(file_path))
    MediLink_ConfigLoader.log("Processing: {}".format(file_path))
    formatted_data, transaction_set_control_number = process_single_file(file_path, config, endpoint, starting_tscn, crosswalk, client)
    isa_header, gs_header, ge_trailer, iea_trailer = MediLink_837p_encoder_library.create_interchange_elements(config, endpoint, transaction_set_control_number - 1)
    
    # Combine everything into a single document
    complete_document = "{}\n{}\n{}\n{}\n{}".format(
        isa_header,
        gs_header,
        formatted_data,
        ge_trailer,            
        iea_trailer
    )
    
    # Write to output file
    output_file_path = write_output_file([complete_document], config.get('outputFilePath', ''), endpoint, file_path, config)
    print("File processed. Output saved to: {}".format(output_file_path))

def main():
    """
    Converts fixed-width files to 837P format for health claim submissions.

    Usage:
    ------
    1. Convert a single file:
        python MediLink_837p_encoder.py -e [endpoint] -p [file_path]

    2. Convert all files in a directory:
        python MediLink_837p_encoder.py -e [endpoint] -p [directory_path] -d

    Arguments:
    ----------
    - "-e": Specify endpoint ("AVAILITY", "OPTUMEDI", "PNT_DATA").
    - "-p": Path to file/directory for processing.
    - "-d": Flag for directory processing.

    Note: Ensure correct config file path.
    """
    parser = argparse.ArgumentParser(
        description="Converts fixed-width files to the 837P format for health claim submissions. Supports processing individual files or all files within a directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-e", "--endpoint", 
        required=True,
        choices=["AVAILITY", "OPTUMEDI", "PNT_DATA", "UHCAPI", "CLAIMSHUTTLE"], # This should read from the config?
        help="Specify the endpoint for which the conversion is intended."
    )
    parser.add_argument(
        "-p", "--path", 
        required=True,
        help="Path to the input fixed-width file or directory to process. If a directory is provided, all .DAT files within will be processed."
    )
    parser.add_argument(
        "-d", "--is-directory", 
        action='store_true',
        help="Flag indicating the path provided is a directory. If set, all .DAT files within the directory will be processed."
    )
    args = parser.parse_args()

    print("Starting the conversion process for {}. Processing {} at '{}'.".format(args.endpoint, 'directory' if args.is_directory else 'file', args.path))

    config, crosswalk = MediLink_ConfigLoader.load_configuration()
    
    # Create API client for payer name resolution
    from MediCafe.core_utils import get_api_client
    client = get_api_client()
    if client is None:
        print("Warning: API client not available via factory")
        # Fallback to direct instantiation
        client = api_core.APIClient()
    
    process_dat_files(args.path, config, args.endpoint, args.is_directory, crosswalk, client)
    print("Conversion complete.")

def process_dat_files(path, config, endpoint, is_directory, crosswalk, client):
    """
    Processes either a single file or all files within a directory.

    Parameters:
    - path: Path to the input fixed-width file or directory to process.
    - config: Configuration settings loaded from a JSON file.
    - endpoint: The endpoint for which the conversion is intended.
    - is_directory: Boolean flag indicating if the path is a directory.
    - crosswalk: Crosswalk data for payer information.
    - client: API client for payer name resolution.

    Returns:
    - None
    """
    if is_directory:
        MediLink_ConfigLoader.log("Processing all .DAT files in: {}".format(path))
        for file_name in os.listdir(path):
            if file_name.endswith(".DAT"):
                file_path = os.path.join(path, file_name)
                process_and_write_file(file_path, config, endpoint, crosswalk, client)
    else:
        MediLink_ConfigLoader.log("Processing the single file: {}".format(path))
        process_and_write_file(path, config, endpoint, crosswalk, client)

if __name__ == "__main__":
    main()
    
# The functions below are the ones that are used as non-main library by outside scripts.
#######################################################################################

def convert_files_for_submission(detailed_patient_data, config, crosswalk, client): 
    """
    Processes detailed patient data for submission based on their confirmed endpoints,
    generating separate 837P files for each endpoint according to the configured submission type.

    Parameters:
    - detailed_patient_data: A list containing detailed patient data with endpoint information.
    - config: Configuration settings loaded from a JSON file.

    Returns:
    - A list of paths to the converted files ready for submission.

    Note:
    - This function currently supports batch and single-patient submissions based on the configuration.
    - Future implementation may include progress tracking using tools like `tqdm`.
    """

    # Ensure crosswalk is a dictionary to avoid NoneType access downstream
    if not isinstance(crosswalk, dict):
        try:
            MediLink_ConfigLoader.log("[convert_files_for_submission] crosswalk is not a dict; type={}".format(type(crosswalk)), config, level="WARNING")
        except Exception:
            pass
        crosswalk = {}

    # Initialize a dictionary to hold patient data segregated by confirmed endpoints
    data_by_endpoint = {}

    # Sanitize input: filter out None or non-dict entries to avoid NoneType.get errors
    if detailed_patient_data is None:
        detailed_patient_data = []
    safe_records = []
    for record in detailed_patient_data:
        if isinstance(record, dict):
            safe_records.append(record)
        else:
            try:
                MediLink_ConfigLoader.log("Skipping invalid patient record of type {}".format(type(record)), config, level="WARNING")
            except Exception:
                pass

    # Group patient data by endpoint
    for data in safe_records:
        endpoint = data.get('confirmed_endpoint')
        if endpoint:
            if endpoint not in data_by_endpoint:
                data_by_endpoint[endpoint] = []
            data_by_endpoint[endpoint].append(data)

    # List to store paths of converted files for each endpoint
    converted_files_paths = []

    # Iterate over each endpoint and process its corresponding patient data
    for endpoint, patient_data_list in data_by_endpoint.items():
        try:
            MediLink_ConfigLoader.log("[convert_files_for_submission] Endpoint {} has {} records".format(endpoint, len(patient_data_list)), config, level="INFO")
        except Exception:
            pass
        # Retrieve submission type from config; default to "batch" if not specified
        medi = extract_medilink_config(config)
        endpoint_cfg = medi.get('endpoints', {}).get(endpoint)
        if not isinstance(endpoint_cfg, dict):
            endpoint_cfg = {}
        submission_type = endpoint_cfg.get('submission_type', 'batch')
        try:
            MediLink_ConfigLoader.log("[convert_files_for_submission] submission_type for {}: {}".format(endpoint, submission_type), config, level="DEBUG")
        except Exception:
            pass

        if submission_type == 'single':
            # Process each patient's data individually for single-patient submissions
            for patient_data in patient_data_list:
                # Generate a unique suffix for each patient, e.g., using a truncated chart number
                chart_number = patient_data.get('CHART', 'UNKNOWN')#[:5] truncation might cause collisions.
                suffix = "_{}".format(chart_number)
                # Process and convert each patient's data to a separate file
                converted_path = process_claim(config, endpoint, [patient_data], crosswalk, client, suffix)
                if converted_path:
                    converted_files_paths.append(converted_path)
        else:
            # Process all patient data together for batch submissions
            try:
                converted_path = process_claim(config, endpoint, patient_data_list, crosswalk, client)
            except Exception as e:
                import traceback as _tb
                tb_s = _tb.format_exc()
                try:
                    MediLink_ConfigLoader.log("[convert_files_for_submission] process_claim failed for {}: {}\nTraceback: {}".format(endpoint, e, tb_s), config, level="ERROR")
                except Exception:
                    pass
                raise
            if converted_path:
                converted_files_paths.append(converted_path)

    return converted_files_paths

def process_claim(config, endpoint, patient_data_list, crosswalk, client, suffix=""): 
    """
    Processes patient data for a specified endpoint, converting it into the 837P format.
    Can handle both batch and single-patient submissions.

    Parameters:
    - config: Configuration settings loaded from a JSON file.
    - endpoint: The key representing the endpoint for which the data is being processed.
    - patient_data_list: A list of dictionaries, each containing detailed patient data.
    - suffix: An optional suffix to differentiate filenames for single-patient processing.

    Returns:
    - Path to the converted file, or None if an error occurs.
    """
    # Ensure we're accessing the correct configuration key
    medi = extract_medilink_config(config)
    
    # Retrieve the output directory from the configuration
    output_directory = MediLink_837p_encoder_library.get_output_directory(medi)
    if not output_directory:
        return None

    transaction_set_control_number = 1
    document_segments = []

    for patient_data in patient_data_list:
        # TODO (SECONDARY PREP): Upstream should mark secondary claims and provide Medicare prior payer info when applicable.
        # Expected minimal keys for Medicare-secondary:
        # - claim_type='secondary'
        # - prior_payer_name='MEDICARE'
        # - prior_payer_id from config cob_settings.medicare_payer_ids (default '00850')
        # - optional: primary_paid_amount, cas_adjustments
        # Validate each patient's data before processing
        is_valid, validation_errors = validate_claim_data(patient_data, medi)
        if is_valid:
            # Format the claim into 837P segments
            formatted_claim = format_single_claim(patient_data, medi, endpoint, transaction_set_control_number, crosswalk, client)
            document_segments.append(formatted_claim)
            transaction_set_control_number += 1
        else:
            # Log any validation errors encountered
            MediLink_ConfigLoader.log("Validation errors for patient data: {}".format(validation_errors), config, level="ERROR")
            if MediLink_837p_encoder_library.handle_validation_errors(transaction_set_control_number, validation_errors, config):
                continue # Skip the current patient

    if not document_segments:
        # If no valid segments were created, log the issue and return None
        MediLink_ConfigLoader.log("No valid document segments created.", config, level="ERROR")
        return None

    # Create interchange elements with the final transaction set control number
    isa_header, gs_header, ge_trailer, iea_trailer = MediLink_837p_encoder_library.create_interchange_elements(medi, endpoint, transaction_set_control_number - 1)

    # Insert headers at the beginning and append trailers at the end of document segments
    document_segments.insert(0, gs_header)
    document_segments.insert(0, isa_header)
    document_segments.extend([ge_trailer, iea_trailer])

    # Use the first patient's file path as a reference for output file naming
    input_file_path = patient_data_list[0].get('file_path', 'UNKNOWN')
    # Write the complete 837P document to an output file
    converted_file_path = write_output_file(document_segments, output_directory, endpoint, input_file_path, medi, suffix)
    return converted_file_path