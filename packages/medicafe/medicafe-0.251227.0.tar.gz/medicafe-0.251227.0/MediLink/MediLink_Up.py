# MediLink_Up.py
"""
Notes:
- Duplicate detection relies on a JSONL index under MediLink_Config['receiptsRoot'].
  If 'receiptsRoot' is missing, duplicate checks are skipped with no errors.
- The claim_key used for deconfliction is practical rather than cryptographic:
  it combines (patient_id if available, else ''), (payer_id or primary_insurance), DOS, and a simple service/procedure indicator.
  In this file-level flow, we approximate with primary_insurance + DOS + file basename for pre-checks.
  Upstream detection now also flags duplicates per patient record using procedure code when available.
- We do NOT write to the index until a successful submission occurs.
- All I/O uses ASCII-safe defaults.
"""
from datetime import datetime
import os, re, traceback
try:
    from tqdm import tqdm
except ImportError:
    # Fallback for when tqdm is not available
    def tqdm(iterable, **kwargs):
        return iterable
import MediLink_837p_encoder
from MediLink_DataMgmt import operate_winscp

# Use core utilities for standardized imports
from MediCafe.core_utils import get_shared_config_loader, get_api_client
MediLink_ConfigLoader = get_shared_config_loader()
log = MediLink_ConfigLoader.log
load_configuration = MediLink_ConfigLoader.load_configuration

# Import api_core for claim submission
try:
    from MediCafe import api_core
except ImportError:
    api_core = None

# Import submission index helpers (XP-safe JSONL)
try:
    from MediCafe.submission_index import (
        compute_claim_key,
        find_by_claim_key,
        append_submission_record
    )
except Exception:
    compute_claim_key = None
    find_by_claim_key = None
    append_submission_record = None

# Import IP validation utilities for OPTUMEDI endpoint checking
try:
    from MediLink_IP_utils import (
        get_private_ip_addresses,
        get_public_ip_address,
        validate_ip_against_allowed
    )
except ImportError:
    # Fallback if IP utils not available
    get_private_ip_addresses = None
    get_public_ip_address = None
    validate_ip_against_allowed = None

# Pre-compile regex patterns for better performance
GS_PATTERN = re.compile(r'GS\*HC\*[^*]*\*[^*]*\*([0-9]{8})\*([0-9]{4})')
SE_PATTERN = re.compile(r'SE\*\d+\*\d{4}~')
NM1_IL_PATTERN = re.compile(r'NM1\*IL\*1\*([^*]+)\*([^*]+)\*([^*]*)')
DTP_472_PATTERN = re.compile(r'DTP\*472\D*8\*([0-9]{8})')
CLM_PATTERN = re.compile(r'CLM\*[^\*]*\*([0-9]+\.?[0-9]*)')
NM1_PR_PATTERN = re.compile(r'NM1\*PR\*2\*([^*]+)\*')

# Internet Connectivity Check
# Use the central function from core_utils for consistency across all modules
def check_internet_connection(max_retries=3, initial_delay=1):
    """
    Checks if there is an active internet connection with automatic retry logic.
    This function delegates to the central implementation in MediCafe.core_utils
    to ensure consistent behavior across all MediBot and MediLink modules.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1)
    
    Returns: Boolean indicating internet connectivity status.
    
    Raises:
        ImportError: If MediCafe.core_utils cannot be imported (indicates configuration issue)
    """
    try:
        from MediCafe.core_utils import check_internet_connection as central_check
        return central_check(max_retries=max_retries, initial_delay=initial_delay)
    except ImportError as e:
        error_msg = (
            "CRITICAL: Cannot import check_internet_connection from MediCafe.core_utils. "
            "This indicates a configuration or installation issue. "
            "Please ensure MediCafe package is properly installed and core_utils.py is accessible. "
            "Original error: {}".format(e)
        )
        print(error_msg)
        raise ImportError(error_msg) from e

# Fallback allowed IPs for OPTUMEDI if config entry is missing
FALLBACK_OPTUMEDI_IPS = ["99.20.30.89", "99.20.30.90", "99.20.30.91"]

def validate_ip_for_endpoint(endpoint, config):
    """
    Validate that the current machine's IP address matches one of the allowed static IPs
    for OPTUMEDI endpoints. Checks both private and public IP addresses.
    
    Args:
        endpoint: Endpoint name (string)
        config: Configuration dictionary
    
    Returns:
        tuple: (is_valid, current_ips_dict, error_message)
            - is_valid: Boolean indicating if validation passed
            - current_ips_dict: Dictionary with 'private' (list) and 'public' (str or None) keys
            - error_message: Formatted error message if validation failed, None if passed
    
    COMPATIBILITY: Python 3.4.4 and Windows XP compatible
    """
    # Check if this is an OPTUMEDI endpoint (case-insensitive)
    if not endpoint or 'optumedi' not in endpoint.lower():
        # Not an OPTUMEDI endpoint, skip validation
        return (True, None, None)
    
    # Check if IP utilities are available
    if not all([get_private_ip_addresses, get_public_ip_address, validate_ip_against_allowed]):
        log("IP validation utilities not available - skipping IP check for endpoint {}".format(endpoint), level="WARNING")
        return (True, None, None)  # Fail open if utilities unavailable
    
    # Normalize configuration for safe access
    if not isinstance(config, dict):
        try:
            config, _ = load_configuration()
        except Exception:
            config = {}
    
    if isinstance(config, dict):
        cfg_candidate = config.get('MediLink_Config')
        if isinstance(cfg_candidate, dict):
            cfg = cfg_candidate
        else:
            cfg = config
    else:
        cfg = {}
    
    # Extract allowed IPs from config
    allowed_ips = None
    try:
        allowed_static_ips = cfg.get('allowed_static_ips', {})
        if isinstance(allowed_static_ips, dict):
            allowed_ips = allowed_static_ips.get('OPTUMEDI')
            if not isinstance(allowed_ips, list):
                allowed_ips = None
    except Exception:
        allowed_ips = None
    
    # Use fallback if config entry not found
    if not allowed_ips:
        log("WARNING: allowed_static_ips not found in MediLink_Config, using fallback IPs for OPTUMEDI validation", level="WARNING")
        allowed_ips = FALLBACK_OPTUMEDI_IPS
    
    # Get current IP addresses
    current_ips = {
        'private': [],
        'public': None
    }
    
    try:
        # Get private IP addresses
        private_ips = get_private_ip_addresses()
        if private_ips:
            current_ips['private'] = private_ips
    except Exception as e:
        log("Error detecting private IP addresses: {}".format(e), level="WARNING")
    
    try:
        # Get public IP address (may fail if offline or service unavailable)
        public_ip = get_public_ip_address(timeout=5)
        if public_ip:
            current_ips['public'] = public_ip
    except Exception as e:
        log("Error detecting public IP address: {}".format(e), level="DEBUG")
    
    # Validate IPs against allowed list
    matched_ip = None
    
    # Check private IPs first
    for private_ip in current_ips['private']:
        if validate_ip_against_allowed(private_ip, allowed_ips):
            matched_ip = private_ip
            break
    
    # Check public IP if no private match found
    if not matched_ip and current_ips['public']:
        if validate_ip_against_allowed(current_ips['public'], allowed_ips):
            matched_ip = current_ips['public']
    
    # If we matched an IP, validation passed
    if matched_ip:
        log("IP validation passed for endpoint {}: matched IP {}".format(endpoint, matched_ip), level="INFO")
        return (True, current_ips, None)
    
    # Validation failed - construct error message
    private_ips_str = ", ".join(current_ips['private']) if current_ips['private'] else "None detected"
    public_ip_str = current_ips['public'] if current_ips['public'] else "Not detected"
    allowed_ips_str = ", ".join(allowed_ips)
    
    error_message = (
        "Current IP addresses do not match any allowed static IP.\n\n"
        "Current IP addresses:\n"
        "  - Private IP(s): {}\n"
        "  - Public IP: {}\n\n"
        "Allowed static IPs for OPTUMEDI:\n"
        "  - {}\n\n"
        "Please verify that this machine is using one of the allowed static IP addresses."
    ).format(private_ips_str, public_ip_str, allowed_ips_str)
    
    log("IP validation failed for endpoint {}: Current IPs do not match allowed list".format(endpoint), level="ERROR")
    
    return (False, current_ips, error_message)

def submit_claims(detailed_patient_data_grouped_by_endpoint, config, crosswalk):
    """
    Submits claims for each endpoint, either via WinSCP or API, based on configuration settings.

    Deconfliction (XP-safe):
    - If JSONL index helpers are available and receiptsRoot is configured, compute a claim_key per 837p file
      and skip submit if index already contains that key (duplicate protection).
    - After a successful submission, append an index record.
    """
    # Normalize configuration for safe nested access
    if not isinstance(config, dict):
        try:
            config, _ = load_configuration()
        except Exception:
            config = {}
    if isinstance(config, dict):
        cfg_candidate = config.get('MediLink_Config')
        if isinstance(cfg_candidate, dict):
            cfg = cfg_candidate
        else:
            cfg = config
    else:
        cfg = {}

    # Resolve receipts folder for index (use same path as receipts)
    receipts_root = cfg.get('local_claims_path', None)

    # Accumulate submission results
    submission_results = {}
    
    if not detailed_patient_data_grouped_by_endpoint:
        print("No new files detected for submission.")
        return

    # Iterate through each endpoint and submit claims
    for endpoint, patients_data in tqdm(detailed_patient_data_grouped_by_endpoint.items(), desc="Progress", unit="endpoint"):
        # Debug context to trace NoneType.get issues early
        try:
            log("[submit_claims] Starting endpoint: {}".format(endpoint), level="INFO")
            if patients_data is None:
                log("[submit_claims] Warning: patients_data is None for endpoint {}".format(endpoint), level="WARNING")
            else:
                try:
                    log("[submit_claims] patients_data count: {}".format(len(patients_data)), level="DEBUG")
                except Exception:
                    log("[submit_claims] patients_data length unavailable (type: {})".format(type(patients_data)), level="DEBUG")
        except Exception:
            pass

        if not patients_data:
            continue

        # Determine the submission method (e.g., "winscp" or "api")
        try:
            method = cfg.get('endpoints', {}).get(endpoint, {}).get('submission_method', 'winscp')
        except Exception as e:
            log("[submit_claims] Error deriving submission method for endpoint {}: {}".format(endpoint, e), level="ERROR")
            method = 'winscp'

        if True: #confirm_transmission({endpoint: patients_data}): # Confirm transmission to each endpoint with detailed overview
            try:
                online = check_internet_connection()
            except ImportError:
                log("CRITICAL: Cannot check internet connectivity - configuration issue. Claims submission aborted.", level="ERROR")
                print("CRITICAL: Cannot check internet connectivity - configuration issue. Please check MediCafe installation.")
                return
            if online:
                client = get_api_client()
                if client is None:
                    print("Warning: API client not available via factory")
                    # Fallback to direct instantiation  
                    try:
                        from MediCafe import api_core
                        client = api_core.APIClient()
                    except ImportError:
                        print("Error: Unable to create API client")
                        continue
                # Process files per endpoint
                try:
                    # Sanitize patient data structure before conversion
                    safe_patients = []
                    if isinstance(patients_data, list):
                        safe_patients = [item for item in patients_data if isinstance(item, dict)]
                    elif isinstance(patients_data, dict):
                        safe_patients = [patients_data]
                    else:
                        log("[submit_claims] Unexpected patients_data type for {}: {}".format(endpoint, type(patients_data)), level="ERROR")
                        safe_patients = []

                    # CRITICAL: Validate configuration before submission
                    try:
                        # Import the validation function from the encoder library
                        import MediLink_837p_encoder_library
                        config_issues = MediLink_837p_encoder_library.validate_config_sender_codes(config, endpoint)
                        if config_issues:
                            log("[CRITICAL] Configuration validation failed for endpoint {}: {}".format(endpoint, config_issues), level="ERROR")
                            print("\n" + "="*80)
                            print("CRITICAL: Configuration issues detected for endpoint '{}'".format(endpoint))
                            print("="*80)
                            for i, issue in enumerate(config_issues, 1):
                                print("   {}. {}".format(i, issue))
                            print("\nWARNING: These issues may cause claim rejections at the clearinghouse!")
                            print("   - Claims may be rejected due to missing sender identification")
                            print("   - Processing may fail due to invalid configuration values")
                            print("="*80)
                            
                            should_continue = False
                            while True:
                                user_choice = input("\nContinue with potentially invalid claims anyway? (y/N): ").strip().lower()
                                if user_choice in ['y', 'yes']:
                                    print("WARNING: Proceeding with submission despite configuration issues...")
                                    log("[WARNING] User chose to continue submission despite config issues for endpoint {}".format(endpoint), level="WARNING")
                                    should_continue = True
                                    break
                                elif user_choice in ['n', 'no', '']:
                                    print("SUCCESS: Submission aborted for endpoint '{}' due to configuration issues.".format(endpoint))
                                    log("[INFO] Submission aborted by user for endpoint {} due to config issues".format(endpoint), level="INFO")
                                    should_continue = False
                                    break
                                else:
                                    print("Please enter 'y' for yes or 'n' for no.")
                            
                            # Skip this endpoint if user chose not to continue
                            if not should_continue:
                                continue
                    except Exception as validation_error:
                        # Don't let validation errors block submission entirely
                        log("[ERROR] Configuration validation check failed: {}".format(validation_error), level="ERROR")
                        print("WARNING: Unable to validate configuration - proceeding with submission")

                    converted_files = MediLink_837p_encoder.convert_files_for_submission(safe_patients, config, crosswalk, client)
                except Exception as e:
                    tb = traceback.format_exc()
                    # Log via logger (may fail if logger expects config); also print to stderr to guarantee visibility
                    try:
                        log("[submit_claims] convert_files_for_submission failed for endpoint {}: {}\nTraceback: {}".format(endpoint, e, tb), level="ERROR")
                    except Exception:
                        pass
                    try:
                        import sys as _sys
                        _sys.stderr.write("[submit_claims] convert_files_for_submission failed for endpoint {}: {}\n".format(endpoint, e))
                        _sys.stderr.write(tb + "\n")
                    except Exception:
                        pass
                    raise
                if converted_files:
                    # Deconfliction pre-check per file if helpers available
                    filtered_files = []
                    for file_path in converted_files:
                        if compute_claim_key and find_by_claim_key and receipts_root:
                            try:
                                # Compute a simple service hash from file path (can be improved later)
                                service_hash = os.path.basename(file_path)
                                # Attempt to parse minimal patient_id and DOS from filename if available
                                # For now, rely on patient data embedded in file content via parse_837p_file
                                patients, _ = parse_837p_file(file_path)
                                # If we cannot compute a stable key, skip deconflict
                                if patients:
                                    # Use first patient for keying; future improvement: per-service keys
                                    p = patients[0]
                                    patient_id = ""  # unknown at this stage (facesheet may not contain chart)
                                    payer_id = ""
                                    primary_insurance = p.get('insurance_name', '')
                                    dos = p.get('service_date', '')
                                    claim_key = compute_claim_key(patient_id, payer_id, primary_insurance, dos, service_hash)
                                    existing = find_by_claim_key(receipts_root, claim_key)
                                    if existing:
                                        print("Duplicate detected; skipping file: {}".format(file_path))
                                        continue
                            except Exception:
                                # Fail open (do not block submission)
                                pass
                        filtered_files.append(file_path)

                    if not filtered_files:
                        print("All files skipped as duplicates for endpoint {}.".format(endpoint))
                        submission_results[endpoint] = {}
                    elif method == 'winscp':
                        # Validate IP address for OPTUMEDI endpoints before transmission
                        is_valid, current_ips, error_msg = validate_ip_for_endpoint(endpoint, config)
                        if not is_valid:
                            # Block submission - IP validation failed
                            error_details = (
                                "\n" + "="*80 + "\n"
                                "ERROR: IP Address Validation Failed for endpoint '{}'\n"
                                "="*80 + "\n"
                                "{}\n"
                                "\nSubmission blocked. Please verify network configuration.\n"
                                "="*80 + "\n"
                            ).format(endpoint, error_msg)
                            print(error_details)
                            log("IP validation failed for endpoint {}: {}".format(endpoint, error_msg), level="ERROR")
                            submission_results[endpoint] = {
                                fp: (False, "IP validation failed: Current IP not in allowed list")
                                for fp in filtered_files
                            }
                            continue  # Skip to next endpoint
                        
                        # Transmit files via WinSCP
                        try:
                            operation_type = "upload"
                            endpoint_cfg = cfg.get('endpoints', {}).get(endpoint, {})
                            local_claims_path = cfg.get('local_claims_path', '.')
                            transmission_result = operate_winscp(operation_type, filtered_files, endpoint_cfg, local_claims_path, config)
                            success_dict = handle_transmission_result(transmission_result, config, operation_type, method)
                            # If we attempted uploads but could not derive any status, emit explicit failures per file
                            if (not success_dict) and filtered_files:
                                success_dict = {fp: (False, "No transfer status found in WinSCP log") for fp in filtered_files}
                            submission_results[endpoint] = success_dict
                        except FileNotFoundError as e:
                            msg = "Log file not found - {}".format(str(e))
                            print("Failed to transmit files to {}. Error: {}".format(endpoint, msg))
                            submission_results[endpoint] = {fp: (False, msg) for fp in (filtered_files or [])}
                        except IOError as e:
                            msg = "Input/output error - {}".format(str(e))
                            print("Failed to transmit files to {}. Error: {}".format(endpoint, msg))
                            submission_results[endpoint] = {fp: (False, msg) for fp in (filtered_files or [])}
                        except Exception as e:
                            msg = str(e)
                            print("Failed to transmit files to {}. Error: {}".format(endpoint, msg))
                            submission_results[endpoint] = {fp: (False, msg) for fp in (filtered_files or [])}
                    elif method == 'api':
                        # Transmit files via API
                        try:
                            api_responses = []
                            for file_path in filtered_files:
                                with open(file_path, 'r', encoding='utf-8') as file:
                                    # Optimize string operations by doing replacements in one pass
                                    x12_request_data = file.read().replace('\n', '').replace('\r', '').strip()
                                    try:
                                        from MediCafe import api_core
                                        response = api_core.submit_uhc_claim(client, x12_request_data)
                                    except ImportError:
                                        print("Error: Unable to import api_core for claim submission")
                                        response = {"error": "API module not available"}
                                    api_responses.append((file_path, response))
                            success_dict = handle_transmission_result(api_responses, config, "api", method)
                            # If API call path yielded no status, emit explicit failures per file attempted
                            if (not success_dict) and filtered_files:
                                success_dict = {fp: (False, "No API response parsed") for fp in filtered_files}
                            submission_results[endpoint] = success_dict
                        except Exception as e:
                            msg = str(e)
                            print("Failed to transmit files via API to {}. Error: {}".format(endpoint, msg))
                            submission_results[endpoint] = {fp: (False, msg) for fp in (filtered_files or [])}
                else:
                    print("No files were converted for transmission to {}.".format(endpoint))
            else:
                print("Error: No internet connection detected.")
                log("Error: No internet connection detected.", level="ERROR")
                try_again = input("Do you want to try again? (Y/N): ").strip().lower()
                if try_again != 'y':
                    print("Exiting transmission process. Please try again later.")
                    return  # Exiting the function if the user decides not to retry
        else:
            # This else statement is inaccessible because it is preceded by an if True condition, 
            # which is always true and effectively makes the else clause unreachable.
            # To handle this, we need to decide under what conditions the submission should be canceled. 
            # One option is to replace the if True with a condition that checks for some pre-submission criteria. 
            # For instance, if there is a confirmation step or additional checks that need to be performed before 
            # proceeding with the submission, these could be included here.
            print("Transmission canceled for endpoint {}.".format(endpoint)) 
        
        # Continue to next endpoint regardless of the previous outcomes

    # Build and display receipt
    build_and_display_receipt(submission_results, config)

    # Check for claim submission failures and automatically submit error report if any detected
    try:
        failure_summary = _detect_claim_submission_failures(submission_results)
        if failure_summary:
            log("Claim submission failures detected. Generating automatic error report...", level="INFO")
            try:
                from MediCafe.error_reporter import collect_support_bundle, submit_support_bundle_email
                zip_path = collect_support_bundle(include_traceback=True, claim_failure_summary=failure_summary)
                if zip_path:
                    try:
                        online = check_internet_connection()
                    except ImportError:
                        # If we can't check connectivity during error reporting, assume offline
                        # to preserve the error bundle for later
                        online = False
                        log("Warning: Could not check internet connectivity - preserving error bundle.", level="WARNING")
                    if online:
                        success = submit_support_bundle_email(zip_path)
                        if success:
                            # On success, remove the bundle
                            try:
                                os.remove(zip_path)
                                log("Error report for claim submission failures submitted successfully.", level="INFO")
                            except Exception:
                                pass
                        else:
                            # Preserve bundle for manual retry
                            log("Error report send failed - bundle preserved at {} for retry.".format(zip_path), level="WARNING")
                            print("Error report send failed - bundle preserved at {} for retry.".format(zip_path))
                    else:
                        log("Offline - error bundle queued at {} for retry when online.".format(zip_path), level="INFO")
                        print("Offline - error bundle queued at {} for retry when online.".format(zip_path))
                else:
                    log("Failed to create error report bundle for claim submission failures.", level="ERROR")
                    print("Failed to create error report bundle for claim submission failures.")
            except ImportError:
                log("Error reporting not available - check MediCafe installation.", level="WARNING")
                print("Error reporting not available - check MediCafe installation.")
            except Exception as report_e:
                log("Error report collection failed: {}".format(report_e), level="ERROR")
                print("Error report collection failed: {}".format(report_e))
    except Exception as e:
        # Don't let error reporting failures break the submission process
        log("Unexpected error during automatic error report generation: {}".format(e), level="ERROR")

    # Append index records for successes
    try:
        if append_submission_record and isinstance(submission_results, dict):
            # Resolve receipts root
            if isinstance(config, dict):
                _cfg2 = config.get('MediLink_Config')
                cfg2 = _cfg2 if isinstance(_cfg2, dict) else config
            else:
                cfg2 = {}
            receipts_root2 = cfg2.get('local_claims_path', None)
            if receipts_root2:
                for endpoint, files in submission_results.items():
                    for file_path, result in files.items():
                        try:
                            status, message = result
                            if status:
                                patients, submitted_at = parse_837p_file(file_path)
                                # Take first patient for keying; improve later for per-service handling
                                p = patients[0] if patients else {}
                                claim_key = compute_claim_key("", "", p.get('insurance_name', ''), p.get('service_date', ''), os.path.basename(file_path))
                                record = {
                                    'claim_key': claim_key,
                                    'patient_id': "",
                                    'payer_id': "",
                                    'primary_insurance': p.get('insurance_name', ''),
                                    'dos': p.get('service_date', ''),
                                    'endpoint': endpoint,
                                    'submitted_at': submitted_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'receipt_file': os.path.basename(file_path),
                                    'status': 'success'
                                }
                                append_submission_record(receipts_root2, record)
                        except Exception:
                            continue
    except Exception:
        pass
    
    print("Claim submission process completed.\n")

def handle_transmission_result(transmission_result, config, operation_type, method):
    """
    Analyze the outcomes of file transmissions based on WinSCP log entries or API responses.

    Parameters:
    - transmission_result: List of paths for files that were attempted to be transmitted or API response details.
    - config: Configuration dictionary containing paths and settings.
    - operation_type: The type of operation being performed (e.g., "upload").
    - method: The transmission method used ("winscp" or "api").

    Returns:
    - Dictionary mapping each file path or API response to a tuple indicating successful transmission and any relevant messages.
    """
    success_dict = {}

    if method == "winscp":
        # Define the log filename based on the operation type
        log_filename = "winscp_{}.log".format(operation_type)
        # XP/WinSCP NOTE:
        # - Historically this used 'local_claims_path' which is typically the UPLOAD staging directory.
        # - On some XP setups, WinSCP writes logs to a different directory than where files are uploaded or downloaded.
        # - To avoid brittle assumptions, allow an explicit 'winscp_log_dir' override while preserving legacy default.
        # - Fallback remains 'local_claims_path' to preserve current behavior.
        # Ensure cfg is a dict for safe access
        if isinstance(config, dict):
            _cfg_candidate = config.get('MediLink_Config')
            if isinstance(_cfg_candidate, dict):
                cfg = _cfg_candidate
            else:
                cfg = config
        else:
            cfg = {}
        winscp_log_dir = (
            cfg.get('winscp_log_dir')
            or cfg.get('local_claims_path')
            or '.'
        )
        # If you observe missing logs, verify WinSCP's real log location in the ini or via command-line switches.
        # Consider adding a scheduled cleanup (daily) to prevent unbounded log growth on XP machines.
        log_path = os.path.join(winscp_log_dir, log_filename)
        
        try:
            # Read the contents of the WinSCP log file
            with open(log_path, 'r', encoding='utf-8') as log_file:
                log_contents = log_file.readlines()

            if not log_contents:
                # Handle the case where the log file is empty
                log("Log file '{}' is empty.".format(log_path))
                success_dict = {file_path: (False, "Log file empty") for file_path in transmission_result}
            else:
                # Process the last few lines of the log file for transfer status
                last_lines = log_contents[-35:]
                for file_path in transmission_result:
                    # Pre-format success messages to avoid repeated string formatting
                    success_message = "Transfer done: '{}'".format(file_path)
                    additional_success_message = "Upload of file '{}' was successful, but error occurred while setting the permissions and/or timestamp.".format(file_path)
                    # Use any() with generator expression for better performance
                    success = any(success_message in line or additional_success_message in line for line in last_lines)
                    message = "Success" if success else "Transfer incomplete or error occurred"
                    success_dict[file_path] = (success, message)

        except FileNotFoundError:
            # Log file not found, handle the error
            log("Log file '{}' not found.".format(log_path))
            success_dict = {file_path: (False, "Log file not found") for file_path in transmission_result}
        except IOError as e:
            # Handle IO errors, such as issues reading the log file
            log("IO error when handling the log file '{}': {}".format(log_path, e))
            success_dict = {file_path: (False, "IO error: {}".format(e)) for file_path in transmission_result}
        except Exception as e:
            # Catch all other exceptions and log them
            log("Error processing the transmission log: {}".format(e))
            success_dict = {file_path: (False, "Error: {}".format(e)) for file_path in transmission_result}

    elif method == "api":
        # Process each API response to determine the success status
        for file_path, response in transmission_result:
            try:
                # Handle responses that may be None or non-dict safely
                if isinstance(response, dict):
                    message = response.get('message', 'No message provided')
                    success = message in [
                        "Claim validated and sent for further processing",
                        "Acknowledgement pending"
                    ]
                else:
                    message = str(response) if response is not None else 'No response received'
                    success = False
                success_dict[file_path] = (success, message)
            except Exception as e:
                # Handle API exception
                log("Error processing API response: {}".format(e))
                success_dict[file_path] = (False, str(e))

    return success_dict

def _detect_claim_submission_failures(submission_results):
    """
    Detect and summarize claim submission failures from submission_results.
    
    Returns a dictionary with failure summary (endpoint names, error types/counts, statistics)
    or None if no failures detected. Summary contains NO PHI (no patient names, dates, amounts, etc.).
    
    Parameters:
    - submission_results: Dictionary containing submission results grouped by endpoint.
    
    Returns:
    - dict or None: Failure summary with endpoint names, error message types/counts, and statistics.
    """
    if not isinstance(submission_results, dict):
        return None
    
    # Import _safe_ascii from error_reporter to avoid duplication
    try:
        from MediCafe.error_reporter import _safe_ascii
    except ImportError:
        # Fallback implementation if import fails (shouldn't happen in normal operation)
        def _safe_ascii(text):
            try:
                if text is None:
                    return ''
                if isinstance(text, bytes):
                    try:
                        text = text.decode('ascii', 'ignore')
                    except Exception:
                        text = text.decode('utf-8', 'ignore')
                else:
                    text = str(text)
                return text.encode('ascii', 'ignore').decode('ascii', 'ignore')
            except Exception:
                return ''
    
    failures_by_endpoint = {}
    error_message_counts = {}
    total_successes = 0
    total_failures = 0
    
    # Iterate through submission results to identify failures
    for endpoint, files in submission_results.items():
        if not isinstance(files, dict):
            continue
        
        endpoint_failures = []
        endpoint_successes = 0
        
        for file_path, result in files.items():
            # Normalize result tuple shape
            try:
                status, message = result
            except Exception:
                # If result is not a tuple, treat as failure
                status = False
                try:
                    message = str(result)
                except Exception:
                    message = "Unknown result"
            
            if status:
                endpoint_successes += 1
                total_successes += 1
            else:
                endpoint_failures.append(message)
                total_failures += 1
                # Sanitize and count error message occurrences
                # Use full message for counting to avoid grouping different errors
                error_key = _safe_ascii(str(message))
                error_message_counts[error_key] = error_message_counts.get(error_key, 0) + 1
        
        if endpoint_failures:
            failures_by_endpoint[endpoint] = {
                'failure_count': len(endpoint_failures),
                'success_count': endpoint_successes,
                'error_messages': list(set(endpoint_failures))  # Unique error messages
            }
    
    # If no failures detected, return None
    if not failures_by_endpoint:
        return None
    
    # Build summary (HIPAA-safe: no PHI)
    # Truncate long error messages in summary for readability (but keep full messages in counts)
    summary = {
        'total_failures': total_failures,
        'total_successes': total_successes,
        'endpoints_with_failures': list(failures_by_endpoint.keys()),
        'failures_by_endpoint': {
            endpoint: {
                'failure_count': data['failure_count'],
                'success_count': data['success_count'],
                'unique_error_count': len(data['error_messages'])
            }
            for endpoint, data in failures_by_endpoint.items()
        },
        'error_message_summary': [
            '{}: {} occurrence(s)'.format(
                (msg[:150] + '...' if len(msg) > 150 else msg),  # Truncate for display only
                count
            )
            for msg, count in sorted(error_message_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    }
    
    return summary

def build_and_display_receipt(submission_results, config):
    """
    Builds and displays a receipt for submitted claims, including both successful and failed submissions.
    A receipt of submitted claims is typically attached to each printed facesheet for recordkeeping confirming submission.
    
    Parameters:
    - submission_results: Dictionary containing submission results with detailed information for each endpoint.
    - config: Configuration settings loaded from a JSON file.

    Returns:
    - None
    """
    # Prepare data for receipt
    receipt_data = prepare_receipt_data(submission_results)

    # Build the receipt
    receipt_content = build_receipt_content(receipt_data)

    # Print the receipt to the screen
    log("Printing receipt...")
    print(receipt_content)

    # Save the receipt to a text file
    save_receipt_to_file(receipt_content, config)

    log("Receipt has been generated and saved.")

def prepare_receipt_data(submission_results):
    """
    Prepare submission results for a receipt, including data from both successful and failed submissions.

    This function extracts patient names, dates of service, amounts billed, and insurance names from an 837p file.
    It also includes the date and time of batch claim submission, and the receiver name from the 1000B segment.
    Data is organized by receiver name and includes both successful and failed submissions.

    Parameters:
    - submission_results (dict): Contains submission results grouped by endpoint, with detailed status information.

    Returns:
    - dict: Organized data for receipt preparation, including both successful and failed submission details.
    """
    receipt_data = {}
    for endpoint, files in submission_results.items():
        log("Processing endpoint: {}".format(endpoint), level="INFO")
        for file_path, file_result in files.items():
            log("File path: {}".format(file_path), level="DEBUG")
            log("File result: {}".format(file_result), level="DEBUG")

            # Ensure endpoint bucket exists even if result shape is unexpected
            if endpoint not in receipt_data:
                receipt_data[endpoint] = {
                    "patients": [],
                    "date_of_submission": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            # Normalize result tuple shape; on unexpected shape, degrade to (False, stringified)
            try:
                status, message = file_result
            except Exception:
                status = False
                try:
                    message = str(file_result)
                except Exception:
                    message = "Unknown result"

            log("Status: {}, Message: {}".format(status, message), level="DEBUG")

            # Parse patient details and add the result status and message
            patient_data, _ = parse_837p_file(file_path)
            for patient in patient_data:
                patient['status'] = status
                patient['message'] = message

            receipt_data[endpoint]["patients"].extend(patient_data)
    
    validate_data(receipt_data)
    log("Receipt data: {}".format(receipt_data), level="DEBUG")
    
    return receipt_data

def validate_data(receipt_data):
    # Simple validation to check if data fields are correctly populated
    for endpoint, data in receipt_data.items():
        patients = data.get("patients", [])
        for index, patient in enumerate(patients, start=1):
            missing_fields = [field for field in ('name', 'service_date', 'amount_billed', 'insurance_name', 'status') if patient.get(field) in (None, '')]
            
            if missing_fields:
                # Log the missing fields without revealing PHI
                log("Receipt Data validation error for endpoint '{}', patient {}: Missing information in fields: {}".format(endpoint, index, ", ".join(missing_fields)))
    return True

def parse_837p_file(file_path):
    """
    Parse an 837p file to extract patient details and date of submission.

    This function reads the specified 837p file, extracts patient details such as name, service date, and amount billed,
    and retrieves the date of submission from the GS segment. It then organizes this information into a list of dictionaries
    containing patient data. If the GS segment is not found, it falls back to using the current date and time.

    Parameters:
    - file_path (str): The path to the 837p file to parse.

    Returns:
    - tuple: A tuple containing two elements:
        - A list of dictionaries, where each dictionary represents patient details including name, service date, and amount billed.
        - A string representing the date and time of submission in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    patient_details = []
    date_of_submission = None
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            log("Parsing submitted 837p...")

            # Extract the submission date from the GS segment
            gs_match = GS_PATTERN.search(content)
            if gs_match:
                date = gs_match.group(1)
                time = gs_match.group(2)
                date_of_submission = datetime.strptime("{}{}".format(date, time), "%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Fallback to the current date and time if GS segment is not found
                date_of_submission = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Split content using 'SE*{count}*{control_number}~' as delimiter
            patient_records = SE_PATTERN.split(content)
            
            # Remove any empty strings from list that may have been added from split
            patient_records = [record for record in patient_records if record.strip()]
            
            for record in patient_records:
                # Extract patient name
                name_match = NM1_IL_PATTERN.search(record)
                # Extract service date
                service_date_match = DTP_472_PATTERN.search(record)
                # Extract claim amount
                amount_match = CLM_PATTERN.search(record)
                # Extract insurance name (payer_name)
                insurance_name_match = NM1_PR_PATTERN.search(record)
                
                if name_match and service_date_match and amount_match:
                    # Handle optional middle name
                    middle_name = name_match.group(3).strip() if name_match.group(3) else ""
                    patient_name = "{} {} {}".format(name_match.group(2), middle_name, name_match.group(1)).strip()
                    
                    # Optimize date formatting
                    service_date_raw = service_date_match.group(1)
                    service_date = "{}-{}-{}".format(service_date_raw[:4], service_date_raw[4:6], service_date_raw[6:])
                    
                    amount_billed = float(amount_match.group(1))
                    insurance_name = insurance_name_match.group(1) if insurance_name_match else ""
                    
                    patient_details.append({
                        "name": patient_name,
                        "service_date": service_date,
                        "amount_billed": amount_billed,
                        "insurance_name": insurance_name
                    })
    except Exception as e:
        print("Error reading or parsing the 837p file: {0}".format(str(e)))
    
    return patient_details, date_of_submission

def build_receipt_content(receipt_data):
    """
    Build the receipt content in a human-readable ASCII format with a tabular data presentation for patient information.

    Args:
        receipt_data (dict): Dictionary containing receipt data with patient details.

    Returns:
        str: Formatted receipt content as a string.
    """
    # Build the receipt content in a human-readable ASCII format
    receipt_lines = ["Submission Receipt", "=" * 60, ""]  # Header

    for endpoint, data in receipt_data.items():
        header = "Endpoint: {0} (Submitted: {1})".format(endpoint, data['date_of_submission'])
        receipt_lines.extend([header, "-" * len(header)])
        
        # Table headers
        table_header = "{:<20} | {:<15} | {:<15} | {:<20} | {:<10}".format("Patient", "Service Date", "Amount Billed", "Insurance", "Status")
        receipt_lines.append(table_header)
        receipt_lines.append("-" * len(table_header))
        
        # Pre-format the status display to avoid repeated conditional checks
        for patient in data["patients"]:
            status_display = "SUCCESS" if patient['status'] else patient['message']
            # Use join for better performance than multiple format calls
            patient_info = " | ".join([
                "{:<20}".format(patient['name']),
                "{:<15}".format(patient['service_date']),
                "${:<14}".format(patient['amount_billed']),
                "{:<20}".format(patient['insurance_name']),
                "{:<10}".format(status_display)
            ])
            receipt_lines.append(patient_info)
        
        receipt_lines.append("")  # Blank line for separation
    
    receipt_content = "\n".join(receipt_lines)
    return receipt_content

def save_receipt_to_file(receipt_content, config):
    """
    Saves the receipt content to a text file and opens it for the user.

    Parameters:
    - receipt_content (str): The formatted content of the receipt.
    - config: Configuration settings loaded from a JSON file.

    Returns:
    - None
    """
    try:
        file_name = "Receipt_{0}.txt".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
        # Ensure cfg is a dict for safe path resolution
        if isinstance(config, dict):
            cfg_candidate = config.get('MediLink_Config')
            if isinstance(cfg_candidate, dict):
                cfg = cfg_candidate
            else:
                cfg = config
        else:
            cfg = {}
        file_path = os.path.join(cfg.get('local_claims_path', '.'), file_name)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(receipt_content)
        
        log("Receipt saved to:", file_path)
        # Open the file automatically for the user (Windows-specific)
        if os.name == 'nt':
            os.startfile(file_path)
    except Exception as e:
        print("Failed to save or open receipt file:", e)

# Secure File Transmission
def confirm_transmission(detailed_patient_data_grouped_by_endpoint):
    """
    Displays detailed patient data ready for transmission and their endpoints, 
    asking for user confirmation before proceeding.

    :param detailed_patient_data_grouped_by_endpoint: Dictionary with endpoints as keys and 
            lists of detailed patient data as values.
    :param config: Configuration settings loaded from a JSON file.
    """ 
    # Clear terminal for clarity
    os.system('cls')
    
    print("\nReview of patient data ready for transmission:")
    for endpoint, patient_data_list in detailed_patient_data_grouped_by_endpoint.items():
        print("\nEndpoint: {0}".format(endpoint))
        for patient_data in patient_data_list:
            patient_info = "({1}) {0}".format(patient_data['patient_name'], patient_data['patient_id'])
            print("- {:<33} | {:<5}, ${:<6}, {}".format(
                patient_info, patient_data['surgery_date'][:5], patient_data['amount'], patient_data['primary_insurance']))
    
    while True:
        confirmation = input("\nProceed with transmission to all endpoints? (Y/N): ").strip().lower()
        if confirmation in ['y', 'n']:
            return confirmation == 'y'
        else:
            print("Invalid input. Please enter 'Y' for yes or 'N' for no.")

# Entry point if this script is run directly. Probably needs to be handled better.
if __name__ == "__main__":
    print("Please run MediLink directly.")