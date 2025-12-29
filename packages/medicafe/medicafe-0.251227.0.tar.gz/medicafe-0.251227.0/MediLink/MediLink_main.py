# MediLink.py - Orchestrating script for MediLink operations
import os, sys, time
from datetime import datetime, timedelta

# Add workspace directory to Python path for MediCafe imports
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(current_dir)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

# Import centralized logging configuration
try:
    from MediCafe.logging_config import PERFORMANCE_LOGGING
except ImportError:
    # Fallback to local flag if centralized config is not available
    PERFORMANCE_LOGGING = False

# Add timing for import phase
start_time = time.time()
if PERFORMANCE_LOGGING:
    print("Starting MediLink initialization...")


# Now import core utilities after path setup
from MediCafe.core_utils import get_shared_config_loader, setup_module_paths, extract_medilink_config
from MediCafe.error_reporter import collect_support_bundle, capture_unhandled_traceback
from MediCafe.error_reporter import submit_support_bundle_email, list_queued_bundles, submit_all_queued_bundles, delete_all_queued_bundles
setup_module_paths(__file__)

# Import modules after path setup
import MediLink_Down
import MediLink_Up
import MediLink_DataMgmt
import MediLink_UI  # Import UI module for handling all user interfaces
import MediLink_PatientProcessor  # Import patient processing functions

# Use core utilities for standardized config loader
MediLink_ConfigLoader = get_shared_config_loader()

import_time = time.time()
if PERFORMANCE_LOGGING:
    print("Import phase completed in {:.2f} seconds".format(import_time - start_time))

# NOTE: Configuration loading moved to function level to avoid import-time dependencies

# --- Safe logging helpers (XP/3.4.4 compatible) ---
def _safe_log(message, level="INFO"):
    """Attempt to log via MediLink logger, fallback to print on failure."""
    try:
        MediLink_ConfigLoader.log(message, level=level)
    except Exception:
        try:
            print(message)
        except Exception:
            pass

def _safe_debug(message):
    _safe_log(message, level="DEBUG")

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


def _refresh_deductible_cache_if_online(config):
    """Run the headless deductible cache builder when internet is available."""
    _safe_log("Checking internet connectivity for cache refresh", level="INFO")
    try:
        online = MediLink_Up.check_internet_connection()
    except ImportError:
        # If core_utils is not available, this is a configuration issue
        # Log it but don't fail the cache refresh attempt
        _safe_log("Cannot check internet connectivity - core_utils not available. Skipping cache refresh.", level="WARNING")
        return
    except Exception:
        # For other exceptions (network errors, etc.), assume offline
        online = False
    if not online:
        _safe_log("Deductible cache refresh skipped (offline).", level="INFO")
        _print_warning("Offline - deductible cache refresh skipped. Connect to internet and restart to build cache.")
        return
    try:
        _safe_log("Importing deductible cache builder module", level="INFO")
        from MediLink.MediLink_Deductible_v1_5 import run_headless_batch
        _safe_log("Starting headless deductible cache build", level="INFO")
        run_headless_batch(config)
        _safe_log("Deductible cache refresh completed successfully", level="INFO")
    except Exception as exc:
        _safe_log("Deductible cache refresh failed: {}".format(exc), level="ERROR")
        _print_error("Deductible cache build failed: {}. Check logs for details.".format(exc))

# TODO There needs to be a crosswalk auditing feature right alongside where all the names get fetched during initial startup maybe? 
# Vision:
# - Fast audit pass on startup with 3s timeout: report missing names/IDs, do not block.
# - Allow manual remediation flows for Medisoft IDs; only call APIs when beneficial (missing names).
# - XP note: default to console prompts; optional UI later.
# This already happens when MediLink is opened.

# Simple in-process scheduler for ack polls
_last_ack_updated_at = None
_scheduled_ack_checks = []  # list of epoch timestamps

def _attempt_cache_build(config):
    """
    Attempt to build the insurance type cache.
    Returns (success: bool, error_message: str or None)
    """
    try:
        _safe_log("Attempting auto-build of insurance type cache", level="INFO")
        try:
            online = MediLink_Up.check_internet_connection()
        except ImportError:
            # If core_utils is not available, this is a configuration issue
            _safe_log("Cannot check internet connectivity - core_utils not available. Skipping cache build.", level="WARNING")
            return False, "Configuration issue - cannot check internet connectivity"
        if not online:
            _safe_log("Cache auto-build skipped: offline", level="INFO")
            return False, "Offline - cannot build cache without internet connection"
        
        from MediLink.MediLink_Deductible_v1_5 import run_headless_batch
        _safe_log("Starting cache auto-build", level="INFO")
        run_headless_batch(config)
        _safe_log("Cache auto-build completed successfully", level="INFO")
        return True, None
    except Exception as exc:
        error_msg = str(exc)
        _safe_log("Cache auto-build failed: {}".format(error_msg), level="ERROR")
        return False, error_msg

def _report_cache_build_failure(error_message):
    """
    Submit error report for cache build failure via MediCafe error reporting.
    Continues execution regardless of report success/failure.
    
    Args:
        error_message: Error message from the failed cache build attempt
    """
    try:
        if collect_support_bundle is None or submit_support_bundle_email is None:
            _safe_log("Error reporting not available for cache build failure", level="WARNING")
            return
        
        _safe_log("Collecting error report for cache build failure: {}".format(error_message), level="INFO")
        zip_path = collect_support_bundle(include_traceback=True)
        if not zip_path:
            _safe_log("Failed to create error report bundle for cache build failure", level="WARNING")
            return
        
        try:
            online = MediLink_Up.check_internet_connection()
        except ImportError:
            # If core_utils is not available, this is a configuration issue
            # Assume offline to preserve the error bundle
            online = False
            print("Warning: Could not check internet connectivity - preserving error bundle.")
        except Exception:
            # For other exceptions (network errors, etc.), assume offline
            online = False
        
        if online:
            success = submit_support_bundle_email(zip_path)
            if success:
                try:
                    os.remove(zip_path)
                    _safe_log("Error report for cache build failure submitted successfully", level="INFO")
                except Exception:
                    pass
            else:
                _safe_log("Error report send failed - bundle preserved at {} for retry".format(zip_path), level="WARNING")
        else:
            _safe_log("Offline - error bundle queued at {} for retry when online".format(zip_path), level="INFO")
    except Exception as report_exc:
        _safe_log("Error report collection failed for cache build failure: {}".format(str(report_exc)), level="WARNING")

def _check_cache_status(config):
    """
    Check cache status and attempt auto-build if needed.
    Distinguishes between missing cache, empty cache, and recently updated cache.
    Submits error report if auto-build fails, but continues execution.
    """
    try:
        from MediLink.insurance_type_cache import get_csv_dir_from_config, load_cache, get_cache_path
        csv_dir = get_csv_dir_from_config(config) if get_csv_dir_from_config else ''
        if not csv_dir:
            _safe_log("Cache status check skipped: csv_dir is empty", level="INFO")
            return
        
        cache_path = get_cache_path(csv_dir)
        cache_exists = os.path.exists(cache_path) if cache_path else False
        
        cache_dict = load_cache(csv_dir)
        patient_count = len(cache_dict.get('by_patient_id', {}))
        
        _safe_log("Cache status: file exists={}, patients in cache={}, directory='{}'".format(
            cache_exists, patient_count, csv_dir), level="INFO")
        
        # Check if cache was recently updated (within last 5 minutes) - indicates cache build just ran
        cache_recently_updated = False
        if cache_exists and cache_dict:
            try:
                last_updated_str = cache_dict.get('lastUpdated', '')
                if last_updated_str:
                    last_updated = datetime.strptime(last_updated_str, '%Y-%m-%dT%H:%M:%SZ')
                    time_diff = datetime.utcnow() - last_updated
                    cache_recently_updated = time_diff.total_seconds() < 300  # 5 minutes
            except Exception:
                pass
        
        # Helper function to handle build result
        def _handle_build_result(build_success, error_msg):
            """Handle the result of a cache build attempt."""
            if build_success:
                # Re-check cache status after build
                cache_dict = load_cache(csv_dir)
                patient_count = len(cache_dict.get('by_patient_id', {}))
                if patient_count > 0:
                    _safe_log("Cache build completed successfully. {} patients in cache.".format(patient_count), level="INFO")
                else:
                    _print_warning("Build attempt just completed but found no valid patients. Check CSV file and payer ID configuration. Claims will default to code 12.")
            else:
                # Build failed - submit error report and continue
                _print_warning("Cache build failed: {}. Error report submitted. Claims will default to code 12.".format(error_msg))
                _report_cache_build_failure(error_msg)
        
        # Handle different scenarios
        if not cache_exists:
            # Cache file missing - attempt auto-build
            _print_warning("Insurance type cache is missing. Attempting auto-build...")
            build_success, error_msg = _attempt_cache_build(config)
            _handle_build_result(build_success, error_msg)
        elif patient_count == 0:
            # Cache exists but is empty
            if cache_recently_updated:
                # Cache was just built but found no patients - likely CSV/payer ID issue
                _print_warning("Detected recently built cache with no valid patients. Check CSV file and payer ID configuration. Claims will default to code 12.")
            else:
                # Cache exists but is old and empty - attempt auto-build
                _print_warning("Insurance type cache is empty. Attempting auto-build...")
                build_success, error_msg = _attempt_cache_build(config)
                _handle_build_result(build_success, error_msg)
        # If cache exists and has patients, no action needed
    except Exception as e:
        _safe_log("Cache status check error: {}".format(str(e)), level="WARNING")

def _tools_menu(config, medi):
    """Low-use maintenance tools submenu."""
    while True:
        print("\nMaintenance Tools:")
        options = [
            "Rebuild submission index now",
            "Submit Error Report (email)",
            "Resolve Queued Error Reports",
            "Export NACOR XML",
            "Back"
        ]
        MediLink_UI.display_menu(options)
        choice = MediLink_UI.get_user_choice().strip()
        if choice == '1':
            receipts_root = medi.get('local_claims_path', None)
            if not receipts_root:
                print("No receipts folder configured (local_claims_path missing).")
                continue
            try:
                from MediCafe.submission_index import build_initial_index
                receipts_root = os.path.normpath(receipts_root)
                print("Rebuilding submission index... (this may take a while)")
                count = build_initial_index(receipts_root)
                print("Index rebuild complete. Indexed {} records.".format(count))
            except Exception as e:
                print("Index rebuild error: {}".format(e))
        elif choice == '2':
            try:
                if submit_support_bundle_email is None:
                    print("Email submission module not available.")
                else:
                    print("\nSubmitting Error Report (email)...")
                    zip_path = collect_support_bundle(include_traceback=True)
                    if not zip_path:
                        print("Failed to create support bundle.")
                    else:
                        ok = submit_support_bundle_email(zip_path)
                        if ok:
                            # Optional: remove the file upon success to avoid re-sending on next startup
                            try:
                                os.remove(zip_path)
                            except Exception:
                                pass
                        else:
                            print("Submission failed. Bundle saved at {} for manual handling.".format(zip_path))
            except Exception as e:
                print("Error during email report submission: {}".format(e))
        elif choice == '3':
            try:
                queued = list_queued_bundles()
                if not queued:
                    print("No queued bundles found.")
                else:
                    print("Found {} queued bundle(s).".format(len(queued)))
                    print("Attempting to send now...")
                    sent, failed = submit_all_queued_bundles()
                    print("Queued send complete. Sent: {} Failed: {}".format(sent, failed))
            except Exception as e:
                print("Error while processing queued bundles: {}".format(e))
        elif choice == '4':
            try:
                from MediLink.MediLink_NACOR_Export import run_nacor_export
                print("\nNACOR XML Export")
                print("="*60)
                result = run_nacor_export(config)
                if result.get('success'):
                    print("\nExport completed successfully!")
                else:
                    print("\nExport completed with errors. See summary above.")
                input("\nPress Enter to continue...")
            except ImportError as e:
                print("Error: NACOR export module not available: {}".format(e))
            except Exception as e:
                print("Error during NACOR export: {}".format(e))
                import traceback
                traceback.print_exc()
        elif choice == '5':
            break
        else:
            MediLink_UI.display_invalid_choice()


def main_menu():
    """
    Initializes the main menu loop and handles the overall program flow,
    including loading configurations and managing user input for menu selections.
    """
    global _last_ack_updated_at, _scheduled_ack_checks
    menu_start_time = time.time()
    
    # Load configuration settings and display the initial welcome message.
    config_start_time = time.time()
    if PERFORMANCE_LOGGING:
        print("Loading configuration...")
    config, crosswalk = MediLink_ConfigLoader.load_configuration() 
    config_end_time = time.time()
    if PERFORMANCE_LOGGING:
        print("Configuration loading completed in {:.2f} seconds".format(config_end_time - config_start_time))
    
    # Check to make sure payer_id key is available in crosswalk, otherwise, go through that crosswalk initialization flow
    crosswalk_check_start = time.time()
    if 'payer_id' not in crosswalk:
        print("\n" + "="*60)
        print("SETUP REQUIRED: Payer Information Database Missing")
        print("="*60)
        print("\nThe system needs to build a database of insurance company information")
        print("before it can process claims. This is a one-time setup requirement.")
        print("\nThis typically happens when:")
        print("- You're running MediLink for the first time")
        print("- The payer database was accidentally deleted or corrupted")
        print("- You're using a new installation of the system")
        print("\nTO FIX THIS:")
        print("1. Open a command prompt/terminal")
        print("2. Navigate to the MediCafe directory")
        print("3. Run: python MediBot/MediBot_Preprocessor.py --update-crosswalk")
        print("4. Wait for the process to complete (this may take a few minutes)")
        print("5. Return here and restart MediLink")
        print("\nThis will download and build the insurance company database.")
        print("="*60)
        print("\nPress Enter to exit...")
        input()
        return  # Graceful exit instead of abrupt halt
    
    crosswalk_check_end = time.time()
    if PERFORMANCE_LOGGING:
        print("Crosswalk validation completed in {:.2f} seconds".format(crosswalk_check_end - crosswalk_check_start))

    # Check if the application is in test mode
    test_mode_start = time.time()
    if config.get("MediLink_Config", {}).get("TestMode", False):
        print("\n--- MEDILINK TEST MODE --- \nTo enable full functionality, please update the config file \nand set 'TestMode' to 'false'.")
    test_mode_end = time.time()
    if PERFORMANCE_LOGGING:
        print("Test mode check completed in {:.2f} seconds".format(test_mode_end - test_mode_start))

    # Refresh deductible cache silently when online
    _refresh_deductible_cache_if_online(config)

    # Boot-time one-time ack poll (silent policy: just show summary output)
    # TEMPORARILY DISABLED - Will be re-enabled with improved implementation
    # try:
    #     print("\nChecking acknowledgements (boot-time scan)...")
    #     ack_result = MediLink_Down.check_for_new_remittances(config, is_boot_scan=True)
    #     _last_ack_updated_at = int(time.time())
    # except Exception:
    #     ack_result = False
    #     pass
    
    # Temporary placeholder - set default values for disabled boot scan
    ack_result = False
    _last_ack_updated_at = int(time.time())

    # TODO: Once we start building out the whole submission tracking persist structure,
    # this boot-time scan should check when the last acknowledgement check was run
    # and skip if it was run recently (e.g., within the last day) to avoid
    # constantly running it on every startup. The submission tracking system should
    # store the timestamp of the last successful acknowledgement check and use it
    # to determine if a new scan is needed.

    # Clear screen before showing menu header
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception as e:
        _safe_debug("Clear screen failed: {}".format(e))  # Fallback if cls/clear fails

    # Display Welcome Message
    welcome_start = time.time()
    MediLink_UI.display_welcome()
    welcome_end = time.time()
    if PERFORMANCE_LOGGING:
        print("Welcome display completed in {:.2f} seconds".format(welcome_end - welcome_start))

    # Startup: (removed) automatic HTTP queue flush for error reports to simplify UX

    # Show message if new records were found during boot-time scan. TODO we need this to use the 'Last acknowledgements update:' timestamp to decide if it has already run in the last day so 
    # that we're not running it multiple times in rapid succession automatically. (user-initiated checks are fine like via selection of (1. Check for new remittances))
    if ack_result:
        print("\n[INFO] New records were found during the boot-time acknowledgement scan.")
        print("You can view them by selecting 'Check for new remittances' from the menu.")

    # Normalize the directory path for file operations.
    path_norm_start = time.time()
    medi = extract_medilink_config(config)
    input_file_path = medi.get('inputFilePath')
    if not input_file_path:
        raise ValueError("Configuration error: 'inputFilePath' missing in MediLink_Config")
    directory_path = os.path.normpath(input_file_path)
    path_norm_end = time.time()
    if PERFORMANCE_LOGGING:
        print("Path normalization completed in {:.2f} seconds".format(path_norm_end - path_norm_start))

    # NEW: Submission index upkeep (XP-safe, inline)
    try:
        receipts_root = medi.get('local_claims_path', None)
        if receipts_root:
            from MediCafe.submission_index import ensure_submission_index
            ensure_submission_index(os.path.normpath(receipts_root))
    except Exception:
        # Silent failure - do not block menu
        pass

    # Detect files and determine if a new file is flagged.
    file_detect_start = time.time()
    if PERFORMANCE_LOGGING:
        print("Starting file detection...")
    all_files, file_flagged = MediLink_DataMgmt.detect_new_files(directory_path)
    file_detect_end = time.time()
    if PERFORMANCE_LOGGING:
        print("File detection completed in {:.2f} seconds".format(file_detect_end - file_detect_start))
        print("Found {} files, flagged: {}".format(len(all_files), file_flagged))
    MediLink_ConfigLoader.log("Found {} files, flagged: {}".format(len(all_files), file_flagged), level="INFO")

    menu_init_end = time.time()
    if PERFORMANCE_LOGGING:
        print("Main menu initialization completed in {:.2f} seconds".format(menu_init_end - menu_start_time))

    

    while True:
        # Run any due scheduled ack checks before showing menu
        try:
            now_ts = int(time.time())
            if _scheduled_ack_checks:
                due = [t for t in _scheduled_ack_checks if t <= now_ts]
                if due:
                    print("\nAuto-checking acknowledgements (scheduled)...")
                    MediLink_Down.check_for_new_remittances(config, is_boot_scan=False)
                    _last_ack_updated_at = now_ts
                    # remove executed
                    _scheduled_ack_checks = [t for t in _scheduled_ack_checks if t > now_ts]
        except Exception as e:
            _safe_log("Scheduled acknowledgements check skipped: {}".format(e), level="WARNING")

        # Define static menu options for consistent numbering
        options = ["Check for new remittances", "Submit claims", "Exit", "Tools"]

        # Display the menu options.
        menu_display_start = time.time()
        # Show last updated info if available
        try:
            if _last_ack_updated_at:
                ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(_last_ack_updated_at))
                print("Last acknowledgements update: {}".format(ts_str))
        except Exception as e:
            _safe_debug("Display of last ack update failed: {}".format(e))
        MediLink_UI.display_menu(options)
        menu_display_end = time.time()
        if PERFORMANCE_LOGGING:
            print("Menu display completed in {:.2f} seconds".format(menu_display_end - menu_display_start))
        
        # Retrieve user choice and handle it.
        choice_start = time.time()
        choice = MediLink_UI.get_user_choice()
        choice_end = time.time()
        if PERFORMANCE_LOGGING:
            print("User choice retrieval completed in {:.2f} seconds".format(choice_end - choice_start))

        if choice == '1':
            # Handle remittance checking.
            remittance_start = time.time()
            result = MediLink_Down.check_for_new_remittances(config, is_boot_scan=False)
            _last_ack_updated_at = int(time.time())
            remittance_end = time.time()
            if PERFORMANCE_LOGGING:
                print("Remittance check completed in {:.2f} seconds".format(remittance_end - remittance_start))
            
            # If no records found, offer connectivity diagnostics
            if not result:
                print("\nNo records found. Would you like to run connectivity diagnostics? (y/n): ", end="")
                try:
                    diagnostic_choice = input().strip().lower()
                    if diagnostic_choice in ['y', 'yes']:
                        print("\nRunning connectivity diagnostics...")
                        connectivity_results = MediLink_Down.test_endpoint_connectivity(config)
                        print("\nConnectivity Test Results:")
                        for endpoint, result in connectivity_results.items():
                            print("  {}: {} - {}".format(
                                endpoint, 
                                result["status"], 
                                "; ".join(result["details"])
                            ))
                except Exception:
                    pass  # Ignore input errors
            
            # UX hint: suggest deeper United details
            try:
                print("Tip: For United details, run the United Claims Status checker.")
            except Exception:
                pass
        elif choice == '2':
            if not all_files:
                print("No files available to submit. Please check for new remittances first.")
                continue
            # Handle the claims submission flow if any files are present.
            submission_start = time.time()
            if file_flagged:
                # Extract the newest single latest file from the list if a new file is flagged.
                selected_files = [max(all_files, key=os.path.getctime)]
            else:
                # Prompt the user to select files if no new file is flagged.
                selected_files = MediLink_UI.user_select_files(all_files)

            # Check cache status before processing claims
            _check_cache_status(config)
            
            # Collect detailed patient data for selected files.
            patient_data_start = time.time()
            detailed_patient_data = MediLink_PatientProcessor.collect_detailed_patient_data(selected_files, config, crosswalk)
            patient_data_end = time.time()
            if PERFORMANCE_LOGGING:
                print("Patient data collection completed in {:.2f} seconds".format(patient_data_end - patient_data_start))
            
            # Process the claims submission.
            handle_submission(detailed_patient_data, config, crosswalk)
            # Schedule ack checks for SFTP-based systems post-submit: T+90s and T+7200s
            try:
                now_ts2 = int(time.time())
                _scheduled_ack_checks.append(now_ts2 + 90)
                _scheduled_ack_checks.append(now_ts2 + 7200)
                print("Scheduled acknowledgements checks in 1-2 minutes and again ~2 hours.")
            except Exception:
                pass
            submission_end = time.time()
            if PERFORMANCE_LOGGING:
                print("Claims submission flow completed in {:.2f} seconds".format(submission_end - submission_start))
        elif choice == '3':
            MediLink_UI.display_exit_message()
            break
        elif choice == '4':
            _tools_menu(config, medi)
        else:
            # Display an error message if the user's choice does not match any valid option.
            MediLink_UI.display_invalid_choice()

def handle_submission(detailed_patient_data, config, crosswalk):
    """
    Handles the submission process for claims based on detailed patient data.
    This function orchestrates the flow from user decision on endpoint suggestions to the actual submission of claims.
    """
    insurance_edited = False  # Flag to track if insurance types were edited

    # Ask the user if they want to edit insurance types
    edit_insurance = input("Do you want to edit insurance types? (y/n): ").strip().lower()
    if edit_insurance in ['y', 'yes', '']:
        insurance_edited = True  # User chose to edit insurance types
        
        # Get insurance options from config
        medi = extract_medilink_config(config)
        insurance_options = medi.get('insurance_options', {})
        
        while True:
            # Bulk edit insurance types
            MediLink_DataMgmt.bulk_edit_insurance_types(detailed_patient_data, insurance_options)
    
            # Review and confirm changes
            if MediLink_DataMgmt.review_and_confirm_changes(detailed_patient_data, insurance_options):
                break  # Exit the loop if changes are confirmed
            else:
                print("Returning to bulk edit insurance types.")
    
    # Initiate user interaction to confirm or adjust suggested endpoints.
    adjusted_data, updated_crosswalk = MediLink_UI.user_decision_on_suggestions(detailed_patient_data, config, insurance_edited, crosswalk)
    
    # Update crosswalk reference if it was modified
    if updated_crosswalk:
        crosswalk = updated_crosswalk

    # Upstream duplicate prompt: flag and allow user to exclude duplicates before submission
    try:
        medi_cfg = extract_medilink_config(config)
        receipts_root = medi_cfg.get('local_claims_path', None)
        if receipts_root:
            try:
                from MediCafe.submission_index import compute_claim_key, find_by_claim_key
            except Exception:
                compute_claim_key = None
                find_by_claim_key = None
            if compute_claim_key and find_by_claim_key:
                for data in adjusted_data:
                    try:
                        # Use precomputed claim_key when available, else build it
                        claim_key = data.get('claim_key', None)
                        if not claim_key:
                            claim_key = compute_claim_key(
                                data.get('patient_id', ''),
                                '',
                                data.get('primary_insurance', ''),
                                data.get('surgery_date_iso', data.get('surgery_date', '')),
                                data.get('primary_procedure_code', '')
                            )
                        existing = find_by_claim_key(receipts_root, claim_key) if claim_key else None
                        if existing:
                            # Show informative prompt
                            print("\nPotential duplicate detected:")
                            print("- Patient: {} ({})".format(data.get('patient_name', ''), data.get('patient_id', '')))
                            print("- DOS: {} | Insurance: {} | Proc: {}".format(
                                data.get('surgery_date', ''),
                                data.get('primary_insurance', ''),
                                data.get('primary_procedure_code', '')
                            ))
                            print("- Prior submission: {} via {} (receipt: {})".format(
                                existing.get('submitted_at', 'unknown'),
                                existing.get('endpoint', 'unknown'),
                                existing.get('receipt_file', 'unknown')
                            ))
                            ans = input("Submit anyway? (Y/N): ").strip().lower()
                            if ans not in ['y', 'yes']:
                                data['exclude_from_submission'] = True
                    except Exception:
                        # Do not block flow on errors
                        continue
    except Exception:
        pass
    
    # Filter out excluded items prior to confirmation and submission
    adjusted_data = [d for d in adjusted_data if not d.get('exclude_from_submission')]
    
    # Confirm all remaining suggested endpoints.
    confirmed_data = MediLink_DataMgmt.confirm_all_suggested_endpoints(adjusted_data)
    if confirmed_data:  # Proceed if there are confirmed data entries.
        # Organize data by confirmed endpoints for submission.
        organized_data = MediLink_DataMgmt.organize_patient_data_by_endpoint(confirmed_data)
        # Confirm transmission with the user and check for internet connectivity.
        if MediLink_Up.confirm_transmission(organized_data):
            try:
                if MediLink_Up.check_internet_connection():
                    # Submit claims if internet connectivity is confirmed.
                    _ = MediLink_Up.submit_claims(organized_data, config, crosswalk)
            except ImportError:
                _print_error("Cannot check internet connectivity - configuration issue. Please check MediCafe installation.")
                return
            else:
                # Notify the user of an internet connection error.
                print("Internet connection error. Please ensure you're connected and try again.")
        else:
            # Notify the user if the submission is cancelled.
            print("Submission cancelled. No changes were made.")

if __name__ == "__main__":
    total_start_time = time.time()
    exit_code = 0
    try:
        # Install unhandled exception hook to capture tracebacks
        try:
            sys.excepthook = capture_unhandled_traceback
        except Exception:
            pass
        main_menu()
    except ValueError as e:
        # Graceful domain error: show concise message without traceback, then exit
        sys.stderr.write("\n" + "="*60 + "\n")
        sys.stderr.write("PROCESS HALTED\n")
        sys.stderr.write("="*60 + "\n")
        sys.stderr.write(str(e) + "\n")
        sys.stderr.write("\nPress Enter to exit...\n")
        try:
            input()
        except Exception:
            pass
        exit_code = 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        exit_code = 1
    except Exception as e:
        sys.stderr.write("An unexpected error occurred; process halted.\n")
        sys.stderr.write(str(e) + "\n")
        from MediCafe.error_reporter import collect_support_bundle
        zip_path = collect_support_bundle(include_traceback=True)
        if not zip_path:
            print("Failed to create bundle - exiting.")
            exit_code = 1
        else:
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
                    print("Send failed - bundle preserved at {} for retry.".format(zip_path))
            else:
                ans = input("Offline. Connect to internet, then press Y to retry or N to discard: ").strip().lower()
                if ans == 'y':
                    try:
                        online = check_internet_connection()
                    except ImportError:
                        print("Warning: Could not check internet connectivity - preserving error bundle.")
                        online = False
                    if online:
                        success = submit_support_bundle_email(zip_path)
                        if success:
                            try:
                                os.remove(zip_path)
                            except Exception:
                                pass
                        else:
                            print("Send failed - bundle preserved at {} for retry.".format(zip_path))
                    else:
                        print("Still offline - preserving bundle at {} for retry.".format(zip_path))
                else:
                    print("Discarding bundle at user request.")
                    try:
                        os.remove(zip_path)
                    except Exception:
                        pass
        exit_code = 1
    finally:
        if exit_code == 0 and PERFORMANCE_LOGGING:
            total_end_time = time.time()
            print("Total MediLink execution time: {:.2f} seconds".format(total_end_time - total_start_time))
    sys.exit(exit_code)
