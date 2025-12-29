# MediLink_Down.py
import os, shutil, sys

# Add paths
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
current_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Use core utilities for imports
try:
    from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config
    MediLink_ConfigLoader = get_shared_config_loader()
    if MediLink_ConfigLoader is not None:
        log = MediLink_ConfigLoader.log
        load_configuration = MediLink_ConfigLoader.load_configuration
    else:
        raise ImportError("MediLink_ConfigLoader not available")
except ImportError:
    # Fallback for when core_utils is not available
    def log(message, level="INFO"):
        print("[{}] {}".format(level, message))
    def load_configuration():
        return {}, {}

try:
    from MediLink_Decoder import process_decoded_file, display_consolidated_records, write_records_to_csv
except ImportError:
    # Fallback if decoder not available
    process_decoded_file = None
    display_consolidated_records = None
    write_records_to_csv = None

try:
    from MediLink_DataMgmt import operate_winscp
except ImportError:
    operate_winscp = None

try:
    from tqdm import tqdm
except ImportError:
    # Fallback for when tqdm is not available
    def tqdm(iterable, **kwargs):
        return iterable

try:
    from MediCafe.submission_index import append_submission_record as _append_submission_record, ensure_submission_index as _ensure_submission_index, append_ack_event as _append_ack_event
except ImportError:
    # Fallback if submission_index not available
    _append_submission_record = None
    _ensure_submission_index = None
    _append_ack_event = None


def handle_files(local_storage_path, downloaded_files):
    """
    Moves downloaded files to the appropriate directory and translates them to CSV format.
    """
    log("Starting to handle downloaded files.")
    
    # Set the local response directory
    local_response_directory = os.path.join(local_storage_path, "responses")
    os.makedirs(local_response_directory, exist_ok=True)
    
    # Supported file extensions (enable ERA/277/999; keep EBT)
    file_extensions = ['.era', '.277', '.277ibr', '.277ebr', '.999', '.dpt', '.ebt', '.ibt', '.txt']
    
    files_moved = []
    
    for file in downloaded_files:
        lower = file.lower()
        if any(lower.endswith(ext) for ext in file_extensions):  # Case-insensitive match
            source_path = os.path.join(local_storage_path, file)
            destination_path = os.path.join(local_response_directory, os.path.basename(file))
            
            try:
                shutil.move(source_path, destination_path)
                log("Moved '{}' to '{}'".format(file, local_response_directory))
                files_moved.append(destination_path)
            except Exception as e:
                log("Error moving file '{}' to '{}': {}".format(file, destination_path, e), level="ERROR")
        else:
            log("Skipping unsupported file '{}'.".format(file), level="DEBUG")
    
    if not files_moved:
        log("No files were moved. Ensure that files with supported extensions exist in the download directory.", level="WARNING")
    
    # Translate the files
    consolidated_records, translated_files = translate_files(files_moved, local_response_directory)
    
    return consolidated_records, translated_files

def translate_files(files, output_directory):
    """
    Translates given files into CSV format and returns the list of translated files and consolidated records.
    """
    log("Translating files: {}".format(files), level="DEBUG")

    if not files:
        log("No files provided for translation. Exiting translate_files.", level="WARNING")
        return [], []

    translated_files = []
    consolidated_records = []
    
    # Enable processing for ERA, 277 family, 999, and EBT
    file_type_selector = {
        '.era': True,
        '.277': True,
        '.277ibr': True,
        '.277ebr': True,
        '.999': True,
        '.dpt': False,
        '.ebt': True,
        '.ibt': False,
        '.txt': False
    }

    file_counts = {ext: 0 for ext in file_type_selector.keys()}

    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if file_type_selector.get(ext, False):  # Check if the file type is selected
            file_counts[ext] += 1

            try:
                src_path = os.path.join(output_directory, os.path.basename(file))
                records = process_decoded_file(src_path, output_directory, return_records=True)
                # Annotate records with source metadata for downstream persistence
                try:
                    mtime = os.path.getmtime(src_path)
                except Exception:
                    mtime = None
                for r in records:
                    try:
                        setattr(r, 'source_file', src_path)
                        setattr(r, 'source_mtime', mtime)
                    except Exception:
                        pass
                consolidated_records.extend(records)
                csv_file_path = os.path.join(output_directory, os.path.basename(file) + '_decoded.csv')
                translated_files.append(csv_file_path)
                log("Translated file to CSV: {}".format(csv_file_path), level="INFO")
            except ValueError:
                log("Unsupported file type: {}".format(file), level="WARNING")
            except Exception as e:
                log("Error processing file {}: {}".format(file, e), level="ERROR")
        else:
            log("Skipping unselected file type for '{}'.".format(file), level="DEBUG")

    log("Detected and processed file counts by type:")
    for ext, count in file_counts.items():
        log("{}: {} files detected".format(ext, count), level="INFO")

    # Simple, elegant summary for console UI
    try:
        if consolidated_records:
            total = len(consolidated_records)
            num_rejected = 0
            num_accepted = 0
            for r in consolidated_records:
                status = getattr(r, 'status', '') if hasattr(r, 'status') else r.get('Status', '')
                if status:
                    if ('Reject' in status) or (':' in status and status.upper().startswith('R')):
                        num_rejected += 1
                    elif ('Accept' in status) or (':' in status and status.upper().startswith('A')):
                        num_accepted += 1
            print("\nAcknowledgements Summary:")
            print("  Total records: {}".format(total))
            print("  Accepted: {}".format(num_accepted))
            print("  Rejected: {}".format(num_rejected))
            print("")
    except Exception:
        pass

    return consolidated_records, translated_files

def prompt_csv_export(records, output_directory):
    """
    Prompts the user to export consolidated records to a CSV file.
    """
    if records:
        # Persist lightweight ack events into receipts index (optional, best-effort)
        try:
            config, _ = load_configuration()
            medi = extract_medilink_config(config)
            receipts_root = medi.get('local_claims_path', None)
            if receipts_root and _ensure_submission_index and _append_ack_event:
                _ensure_submission_index(receipts_root)
                for rec in records:
                    try:
                        # rec may be UnifiedRecord; convert
                        if hasattr(rec, 'to_dict'):
                            d = rec.to_dict()
                        else:
                            d = rec
                        claim_no = d.get('Claim #', '')
                        status_text = d.get('Status', '')
                        # infer ack_type by presence of fields
                        ack_type = ''
                        if d.get('Paid', '') != '' or d.get('Allowed', '') != '':
                            ack_type = 'ERA'
                        elif status_text and ':' in status_text:
                            ack_type = '277'
                        else:
                            ack_type = 'EBT'  # default for text notifications
                        # Use file metadata when available
                        file_name = os.path.basename(getattr(rec, 'source_file', '')) if hasattr(rec, 'source_file') else 'responses'
                        ts = getattr(rec, 'source_mtime', None)
                        control_ids = {}
                        if claim_no:
                            _append_ack_event(
                                receipts_root,
                                '',  # claim_key unknown here
                                status_text,
                                ack_type,
                                file_name,
                                control_ids,
                                'download_ack',
                                int(ts) if isinstance(ts, (int, float)) else None
                            )
                    except Exception:
                        continue
        except Exception:
            pass
        
        user_input = input("Do you want to export the consolidated records to a CSV file? (y/n): ")
        if user_input.lower() == 'y':
            output_file_path = os.path.join(output_directory, "Consolidated_Records.csv")
            write_records_to_csv(records, output_file_path)
            log("Consolidated CSV file created at: {}".format(output_file_path), level="INFO")
        else:
            log("CSV export skipped by user.", level="INFO")

def main(desired_endpoint=None):
    """
    Main function for running MediLink_Down as a standalone script. 
    Simplified to handle only CLI operations and delegate the actual processing to the high-level function.
    """
    log("Running MediLink_Down.main with desired_endpoint={}".format(desired_endpoint))

    if not desired_endpoint:
        log("No specific endpoint provided. Aborting operation.", level="ERROR")
        return None, None
    
    try:
        config, _ = load_configuration()
        medi = extract_medilink_config(config)
        endpoint_config = medi.get('endpoints', {}).get(desired_endpoint)
        if not endpoint_config or 'remote_directory_down' not in endpoint_config:
            log("Configuration for endpoint '{}' is incomplete or missing 'remote_directory_down'.".format(desired_endpoint), level="ERROR")
            return None, None

        local_storage_path = medi.get('local_storage_path', '.')
        log("Local storage path set to {}".format(local_storage_path))
        
        downloaded_files = operate_winscp("download", None, endpoint_config, local_storage_path, config)
        
        if downloaded_files:
            log("From main(), WinSCP Downloaded the following files: \n{}".format(downloaded_files))
            consolidated_records, translated_files = handle_files(local_storage_path, downloaded_files)
            
            # Convert UnifiedRecord instances to dictionaries before displaying
            dict_consolidated_records = [record.to_dict() for record in consolidated_records]
            display_consolidated_records(dict_consolidated_records)

            # Prompt for CSV export
            prompt_csv_export(consolidated_records, local_storage_path)
            
            return consolidated_records, translated_files
        else:
            log("No files were downloaded for endpoint: {}. Exiting...".format(desired_endpoint), level="WARNING")
            return None, None
    
    except Exception as e:
        log("An error occurred in MediLink_Down.main: {}".format(e), level="ERROR")
        return None, None


def check_for_new_remittances(config=None, is_boot_scan=False):
    """
    Function to check for new remittance files across all configured endpoints.
    Loads the configuration, validates it, and processes each endpoint to download and handle files.
    Accumulates results from all endpoints and processes them together at the end.
    
    Args:
        config: Configuration object
        is_boot_scan: If True, suppresses "No records" message for boot-time scans
    
    Returns:
        bool: True if new records were found, False otherwise
    """
    # Start the process and log the initiation
    log("Starting check_for_new_remittances function")
    if not is_boot_scan:
        print("\nChecking for new files across all endpoints...")
    log("Checking for new files across all endpoints...")

    # Step 1: Load and validate the configuration
    if config is None:
        config, _ = load_configuration()

    medi = extract_medilink_config(config)
    if not medi or 'endpoints' not in medi:
        log("Error: Config is missing necessary sections. Aborting...", level="ERROR")
        return False

    endpoints = medi.get('endpoints')
    if not isinstance(endpoints, dict):
        log("Error: 'endpoints' is not a dictionary. Aborting...", level="ERROR")
        return False

    # DIAGNOSTIC: Log endpoint configuration details
    log("Found {} configured endpoints: {}".format(len(endpoints), list(endpoints.keys())), level="INFO")
    for endpoint_key, endpoint_info in endpoints.items():
        log("Endpoint '{}': session_name={}, remote_directory_down={}, has_filemask={}".format(
            endpoint_key,
            endpoint_info.get('session_name', 'NOT_SET'),
            endpoint_info.get('remote_directory_down', 'NOT_SET'),
            'filemask' in endpoint_info
        ), level="DEBUG")

    # Lists to accumulate all consolidated records and translated files across all endpoints
    all_consolidated_records = []
    all_translated_files = []
    endpoint_results = {}  # Track results per endpoint for diagnostics

    # Step 2: Process each endpoint and accumulate results
    for endpoint_key, endpoint_info in tqdm(endpoints.items(), desc="Processing endpoints"):
        log("=== Processing endpoint: {} ===".format(endpoint_key), level="INFO")
        
        # Validate endpoint structure
        if not endpoint_info or not isinstance(endpoint_info, dict):
            log("Error: Invalid endpoint structure for {}. Skipping...".format(endpoint_key), level="ERROR")
            endpoint_results[endpoint_key] = {"status": "error", "reason": "invalid_structure"}
            continue

        if 'remote_directory_down' in endpoint_info:
            # Process the endpoint and handle the files
            log("Processing endpoint: {} with remote_directory_down: {}".format(
                endpoint_key, endpoint_info.get('remote_directory_down')), level="INFO")
            
            consolidated_records, translated_files = process_endpoint(endpoint_key, endpoint_info, config)
            
            # Track results for diagnostics
            endpoint_results[endpoint_key] = {
                "status": "processed",
                "records_found": len(consolidated_records) if consolidated_records else 0,
                "files_translated": len(translated_files) if translated_files else 0
            }
            
            # Accumulate the results for later processing
            if consolidated_records:
                all_consolidated_records.extend(consolidated_records)
                log("Added {} records from endpoint {}".format(len(consolidated_records), endpoint_key), level="INFO")
            if translated_files:
                all_translated_files.extend(translated_files)
                log("Added {} translated files from endpoint {}".format(len(translated_files), endpoint_key), level="INFO")
        else:
            log("Skipping endpoint '{}'. 'remote_directory_down' not configured.".format(endpoint_info.get('name', 'Unknown')), level="WARNING")
            endpoint_results[endpoint_key] = {"status": "skipped", "reason": "no_remote_directory_down"}

    # DIAGNOSTIC: Log summary of endpoint processing
    log("=== Endpoint Processing Summary ===", level="INFO")
    for endpoint_key, result in endpoint_results.items():
        if result["status"] == "processed":
            log("Endpoint '{}': {} records found, {} files translated".format(
                endpoint_key, result["records_found"], result["files_translated"]), level="INFO")
        else:
            log("Endpoint '{}': {} ({})".format(
                endpoint_key, result["status"], result.get("reason", "unknown")), level="WARNING")

    # Step 3: After processing all endpoints, handle the accumulated results
    if all_consolidated_records:
        log("Total records found across all endpoints: {}".format(len(all_consolidated_records)), level="INFO")
        display_consolidated_records(all_consolidated_records)  # Ensure this is called only once
        prompt_csv_export(all_consolidated_records, medi.get('local_storage_path', '.'))
        return True
    else:
        log("No records to display after processing all endpoints.", level="WARNING")
        # Enhanced diagnostic message when no records found
        if not is_boot_scan:
            print("No records to display after processing all endpoints.")
            print("\nDiagnostic Information:")
            print("- Total endpoints configured: {}".format(len(endpoints)))
            print("- Endpoints with remote_directory_down: {}".format(
                sum(1 for ep in endpoints.values() if 'remote_directory_down' in ep)))
            print("- Endpoints processed: {}".format(
                sum(1 for result in endpoint_results.values() if result["status"] == "processed")))
            print("- Endpoints skipped: {}".format(
                sum(1 for result in endpoint_results.values() if result["status"] == "skipped")))
            print("- Endpoints with errors: {}".format(
                sum(1 for result in endpoint_results.values() if result["status"] == "error")))
        return False


def process_endpoint(endpoint_key, endpoint_info, config):
    """
    Helper function to process a single endpoint.
    Downloads files from the endpoint, processes them, and returns the consolidated records and translated files.
    """
    try:
        # Process the files for the given endpoint
        medi = extract_medilink_config(config)
        local_storage_path = medi.get('local_storage_path', '.')
        log("[Process Endpoint] Local storage path set to {}".format(local_storage_path))
        
        # DIAGNOSTIC: Check WinSCP availability and configuration
        try:
            from MediLink_DataMgmt import get_winscp_path
            winscp_path = get_winscp_path(config)
            if os.path.exists(winscp_path):
                log("[Process Endpoint] WinSCP found at: {}".format(winscp_path), level="INFO")
            else:
                log("[Process Endpoint] WinSCP not found at: {}".format(winscp_path), level="ERROR")
                return [], []
        except Exception as e:
            log("[Process Endpoint] Error checking WinSCP path: {}".format(e), level="ERROR")
            return [], []
        
        # DIAGNOSTIC: Log endpoint configuration details
        log("[Process Endpoint] Endpoint config - session_name: {}, remote_directory_down: {}, filemask: {}".format(
            endpoint_info.get('session_name', 'NOT_SET'),
            endpoint_info.get('remote_directory_down', 'NOT_SET'),
            endpoint_info.get('filemask', 'NOT_SET')
        ), level="DEBUG")
        
        # DIAGNOSTIC: Check if we're in test mode
        if config.get("MediLink_Config", {}).get("TestMode", False):
            log("[Process Endpoint] Test mode is enabled - simulating download", level="WARNING")
        
        downloaded_files = operate_winscp("download", None, endpoint_info, local_storage_path, config)
        
        if downloaded_files:
            log("[Process Endpoint] WinSCP Downloaded the following files: \n{}".format(downloaded_files))
            consolidated_records, translated_files = handle_files(local_storage_path, downloaded_files)
            log("[Process Endpoint] File processing complete - {} records, {} translated files".format(
                len(consolidated_records) if consolidated_records else 0,
                len(translated_files) if translated_files else 0
            ), level="INFO")
            return consolidated_records, translated_files
        else:
            log("[Process Endpoint] No files were downloaded for endpoint: {}.".format(endpoint_key), level="WARNING")
            
            # DIAGNOSTIC: Check if WinSCP log exists and analyze it
            try:
                log_filename = "winscp_download.log"
                log_path = os.path.join(local_storage_path, log_filename)
                if os.path.exists(log_path):
                    log("[Process Endpoint] WinSCP log exists at: {}".format(log_path), level="INFO")
                    # Read last few lines of log for diagnostics
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                last_lines = lines[-5:]  # Last 5 lines
                                log("[Process Endpoint] Last 5 lines of WinSCP log:", level="DEBUG")
                                for line in last_lines:
                                    log("[Process Endpoint] Log: {}".format(line.strip()), level="DEBUG")
                    except Exception as e:
                        log("[Process Endpoint] Error reading WinSCP log: {}".format(e), level="ERROR")
                else:
                    log("[Process Endpoint] WinSCP log not found at: {}".format(log_path), level="WARNING")
            except Exception as e:
                log("[Process Endpoint] Error checking WinSCP log: {}".format(e), level="ERROR")
            
            return [], []

    except Exception as e:
        # Handle any exceptions that occur during the processing
        log("Error processing endpoint {}: {}".format(endpoint_key, e), level="ERROR")
        import traceback
        log("Full traceback: {}".format(traceback.format_exc()), level="DEBUG")
        return [], []

def test_endpoint_connectivity(config=None, endpoint_key=None):
    """
    Test basic connectivity to a specific endpoint or all endpoints.
    This is a diagnostic function to help identify connection issues.
    
    Args:
        config: Configuration object
        endpoint_key: Specific endpoint to test, or None for all endpoints
    
    Returns:
        dict: Results of connectivity tests
    """
    if config is None:
        config, _ = load_configuration()
    
    medi = extract_medilink_config(config)
    if not medi or 'endpoints' not in medi:
        log("Error: Config is missing necessary sections.", level="ERROR")
        return {}
    
    endpoints = medi.get('endpoints')
    results = {}
    
    # Determine which endpoints to test
    if endpoint_key:
        if endpoint_key in endpoints:
            test_endpoints = {endpoint_key: endpoints[endpoint_key]}
        else:
            log("Error: Endpoint '{}' not found in configuration.".format(endpoint_key), level="ERROR")
            return {}
    else:
        test_endpoints = endpoints
    
    log("Testing connectivity for {} endpoint(s)...".format(len(test_endpoints)), level="INFO")
    
    for ep_key, ep_info in test_endpoints.items():
        log("Testing endpoint: {}".format(ep_key), level="INFO")
        result = {"status": "unknown", "details": []}
        
        # Check basic configuration
        if not ep_info.get('session_name'):
            result["status"] = "error"
            result["details"].append("Missing session_name")
        elif not ep_info.get('remote_directory_down'):
            result["status"] = "error"
            result["details"].append("Missing remote_directory_down")
        else:
            result["details"].append("Configuration appears valid")
            
            # Check WinSCP availability
            try:
                from MediLink_DataMgmt import get_winscp_path
                winscp_path = get_winscp_path(config)
                if os.path.exists(winscp_path):
                    result["details"].append("WinSCP found at: {}".format(winscp_path))
                else:
                    result["status"] = "error"
                    result["details"].append("WinSCP not found at: {}".format(winscp_path))
            except Exception as e:
                result["status"] = "error"
                result["details"].append("Error checking WinSCP: {}".format(e))
            
            # Check test mode
            if config.get("MediLink_Config", {}).get("TestMode", False):
                result["details"].append("Test mode is enabled - no real connection will be made")
                result["status"] = "test_mode"
        
        results[ep_key] = result
    
    return results


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("MediLink_Down Standalone Testing Tool")
    print("=" * 60)
    print()
    
    # Check if endpoint was provided as command line argument
    if len(sys.argv) > 1:
        desired_endpoint = sys.argv[1]
        print("Testing specific endpoint: {}".format(desired_endpoint))
        print()
        main(desired_endpoint)
    else:
        # No specific endpoint provided - run connectivity diagnostics
        print("No specific endpoint provided.")
        print("Running connectivity diagnostics for all endpoints...")
        print()
        
        try:
            config, _ = load_configuration()
            connectivity_results = test_endpoint_connectivity(config)
            
            if connectivity_results:
                print("Connectivity Test Results:")
                print("-" * 40)
                
                for endpoint, result in connectivity_results.items():
                    status = result["status"]
                    details = result["details"]
                    
                    if status == "error":
                        print("[ERROR] {}: {}".format(endpoint, status))
                    elif status == "test_mode":
                        print("[TEST] {}: {} (Test Mode)".format(endpoint, status))
                    else:
                        print("[OK] {}: {}".format(endpoint, status))
                    
                    for detail in details:
                        print("    - {}".format(detail))
                    print()
                
                # Show available endpoints for testing
                medi = extract_medilink_config(config)
                endpoints = medi.get('endpoints', {})
                if endpoints:
                    print("Available endpoints for testing:")
                    print("-" * 30)
                    for endpoint in endpoints.keys():
                        print("  - {}".format(endpoint))
                    print()
                    print("To test a specific endpoint, run:")
                    print("  python MediLink_Down.py <endpoint_name>")
            else:
                print("ERROR: No connectivity test results returned.")
                
        except Exception as e:
            print("ERROR: Failed to run diagnostics: {}".format(e))
            import traceback
            traceback.print_exc()