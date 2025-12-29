# MediLink_Deductible_v1_5.py
# Streamlined, headless deductible batch runner (OptumAI-first with safe Legacy fallback).
# Reuse-first: relies on MediCafe and existing MediLink helpers; no duplication of parsing/merge logic.
#
# Behavior:
# - Batch (default): Exclude PATIDs whose cache remaining_amount parses as 0; fetch others via OptumAI, fallback to Legacy on safe failures.
# - Persist: Write insurance type code (SBR09) and remaining_amount to insurance_type_cache.json by PATID.
# - Logging: No PHI (no names, full DOBs, or member IDs). Progress bar + concise summary only.
#
# XP / Python 3.4.4 compatible.
#
# REFACTORING NOTES (2024-11-17):
# - Cache infrastructure updated: Now supports multiple policies per patient with service_date matching.
# - Plan dates (plan_start_date, plan_end_date) are now extracted from merge_responses() and stored in cache.
# - Policy status determination: Uses plan_end_date to show "Active Policy" vs "Past Policy".
# - Cache function: This module uses put_entry_from_enhanced_result() exclusively for cache persistence.
#   - Extracts insurance_type, remaining_amount, patient_id, service_date, plan_start_date, plan_end_date
#   - Validates codes, handles service_date parsing, and calls low-level put_entry() internally.
# - Cache cleanup: Uses service_date for staleness determination (720 days max age), not cached_at timestamp.
# - Cache lookup: When return_full=True, now returns plan_start_date and plan_end_date for policy status determination.

from __future__ import print_function

import os
import sys
import time
from datetime import datetime, timedelta

# Ensure MediCafe module path is available (mirror v1 pattern)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from MediCafe.core_utils import (
        setup_project_path,
        get_shared_config_loader,
        get_api_core_client,
        create_config_cache,
    )
    project_dir = setup_project_path(__file__)
    _Logger = get_shared_config_loader()
except Exception:
    _Logger = None
    def _dummy():
        return None
    get_api_core_client = _dummy
    def create_config_cache():
        def _get_cfg():
            return {}, {}
        return _get_cfg, ({}, {})

try:
    from MediCafe.error_reporter import (
        capture_unhandled_traceback,
        submit_support_bundle_email,
        collect_support_bundle,
    )
except Exception:
    capture_unhandled_traceback = None
    submit_support_bundle_email = None
    collect_support_bundle = None

# Best-effort imports (reuse-first)
try:
    from MediCafe import api_core
except Exception:
    api_core = None

try:
    from MediCafe.deductible_utils import (
        merge_responses,
        resolve_payer_ids_from_csv,
        get_payer_id_for_patient,
        classify_api_failure,
        is_ok_200,
        _extract_service_date_from_csv_row,
        is_valid_insurance_code,
        collect_insurance_type_mapping_from_response,
        validate_and_format_date,
    )
except Exception:
    merge_responses = None
    resolve_payer_ids_from_csv = None
    get_payer_id_for_patient = None
    classify_api_failure = None
    _extract_service_date_from_csv_row = None
    collect_insurance_type_mapping_from_response = None
    validate_and_format_date = None
    def is_ok_200(status):
        try:
            return int(status) == 200
        except Exception:
            return False

try:
    from MediLink.insurance_type_cache import (
        get_csv_dir_from_config,
        lookup as cache_lookup,
        put_entry_from_enhanced_result,  # High-level function for enhanced_result dicts - handles all extraction automatically
        load_cache,
    )
except Exception:
    get_csv_dir_from_config = None
    cache_lookup = None
    put_entry_from_enhanced_result = None
    load_cache = None

try:
    from MediBot import MediBot_Preprocessor_lib
except Exception:
    MediBot_Preprocessor_lib = None

try:
    from MediCafe.core_utils import check_internet_connection
except ImportError as e:
    error_msg = (
        "CRITICAL: Cannot import check_internet_connection from MediCafe.core_utils. "
        "This indicates a configuration or installation issue. "
        "Please ensure MediCafe package is properly installed and core_utils.py is accessible. "
        "Original error: {}".format(e)
    )
    print(error_msg)
    raise ImportError(error_msg) from e

# Internal helpers

def _render_progress_bar(current, total, width=40):
    """ASCII-only progress bar text (XP / Py3.4.4 compatible)."""
    try:
        if total <= 0:
            filled = 0
        else:
            ratio = float(max(0, min(current, total))) / float(total)
            filled = int(round(width * ratio))
    except Exception:
        filled = 0
        total = max(total, 1)
    filled = max(0, min(width, filled))
    empty = width - filled
    return "[{}{}] {}/{}".format("#" * filled, "-" * empty, current, total if total > 0 else 0)


def _print_progress(current, total):
    """Render progress bar on a single console line."""
    try:
        bar = _render_progress_bar(current, total)
        sys.stdout.write("\r" + bar)
        sys.stdout.flush()
    except Exception:
        pass


def _install_exception_hook():
    try:
        if capture_unhandled_traceback is not None:
            sys.excepthook = capture_unhandled_traceback
    except Exception:
        pass


def _report_batch_failure(exc):
    _log("Deductible_v1.5 batch failure: {}".format(exc), level="ERROR")
    if collect_support_bundle is None or submit_support_bundle_email is None:
        return
    try:
        zip_path = collect_support_bundle(include_traceback=True, insurance_type_mapping=_insurance_type_mapping_monitor if _insurance_type_mapping_monitor else None)
        if not zip_path:
            return
        try:
            online = check_internet_connection()
        except Exception:
            online = True
        if online:
            success = submit_support_bundle_email(zip_path)
            if success:
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            else:
                print("Error report send failed - bundle preserved at {} for retry.".format(zip_path))
        else:
            print("Offline - error bundle queued at {} for retry when online.".format(zip_path))
    except Exception as report_exc:
        print("Error report collection failed: {}".format(report_exc))


def _log(message, level="INFO"):
    try:
        if _Logger and hasattr(_Logger, "log"):
            _Logger.log(message, level=level)
    except (OSError, IOError):
        # Windows logging stream flush can fail with OSError [Errno 22] - ignore silently
        pass
    except Exception:
        pass

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

# Silent insurance type mapping monitor (accumulates across batch for error reporting)
_insurance_type_mapping_monitor = {}

def _parse_amount_to_float(value):
    # Accept numeric or string like "0", "0.00", "$0.00", "1,234.56"; returns (ok, float_value)
    try:
        if value is None:
            return False, 0.0
        if isinstance(value, (int, float)):
            return True, float(value)
        s = str(value).strip()
        if not s:
            return False, 0.0
        if s.lower() == "not found":
            return False, 0.0
        # Strip currency symbols and commas
        s = s.replace("$", "").replace(",", "")
        return True, float(s)
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

def _is_ready_from_cache_payload(payload):
    # payload may include {'remaining_amount': '...', 'code': '...'}
    try:
        if not isinstance(payload, dict):
            return False
        # Validate insurance code is a valid short code
        cached_code = payload.get("code", "")
        if not _is_valid_insurance_code(cached_code):
            # Invalid code (description, "Not Available", etc.) - skip cache
            return False
        amt = payload.get("remaining_amount")
        ok, f = _parse_amount_to_float(amt)
        return ok and (f <= 0.0)
    except Exception:
        return False

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

def _safe_get_csv_dir(config):
    try:
        if get_csv_dir_from_config:
            return get_csv_dir_from_config(config)
    except Exception:
        pass
    try:
        return os.path.dirname(config.get("CSV_FILE_PATH", "")) if isinstance(config, dict) else ""
    except Exception:
        return ""

def _normalize_dob_to_iso(dob_str):
    """
    Normalize DOB string to ISO format (YYYY-MM-DD) for consistent comparison.
    
    FIX #4: Now delegates to centralized validate_and_format_date() function
    to ensure consistent date parsing across all modules.
    
    Args:
        dob_str: Date of birth string in any format
    
    Returns:
        Normalized DOB in YYYY-MM-DD format, or original string if parsing fails
    """
    if not dob_str:
        return dob_str
    
    # Use centralized date parsing function
    if validate_and_format_date:
        try:
            normalized = validate_and_format_date(dob_str)
            if normalized:
                return normalized
        except Exception:
            pass
    
    # If parsing fails, return original (better than losing the patient)
    return dob_str

def _parse_service_date_to_iso(service_date):
    """
    Parse service_date to YYYY-MM-DD format string.
    
    FIX #4: Now delegates to centralized validate_and_format_date() function
    to ensure consistent date parsing across all modules.
    
    Handles datetime objects and various string formats.
    Returns None if parsing fails.
    """
    if not service_date:
        return None
    try:
        if isinstance(service_date, datetime):
            if service_date != datetime.min:
                return service_date.strftime('%Y-%m-%d')
        elif isinstance(service_date, str) and service_date.strip():
            # Use centralized date parsing function
            if validate_and_format_date:
                return validate_and_format_date(service_date.strip())
    except Exception:
        pass
    return None

def get_patients_from_cache_for_refresh(csv_dir, max_stale_days=120):
    """
    Scan the insurance cache for patients with non-zero remaining_amount that need refresh.
    Returns patients whose cached_at is older than 24 hours and are not stale.
    
    Args:
        csv_dir: Directory containing the cache file
        max_stale_days: Maximum age in days for service_date before patient is considered stale (default 120)
    
    Returns:
        List of patient tuples: (patid, dob_iso, member_id, payer_id, service_date)
    """
    if not load_cache or not csv_dir:
        return []
    
    try:
        cache_dict = load_cache(csv_dir)
        if not isinstance(cache_dict, dict):
            return []
        
        by_patient_id = cache_dict.get('by_patient_id', {})
        if not isinstance(by_patient_id, dict):
            return []
        
        patients_to_refresh = []
        now_utc = datetime.utcnow()
        cache_refresh_threshold = timedelta(hours=_RECENT_CACHE_MAX_AGE_HOURS)
        
        for patient_id, patient_data in by_patient_id.items():
            if not isinstance(patient_data, dict):
                continue
            
            policies = patient_data.get('policies', [])
            if not isinstance(policies, list) or not policies:
                continue
            
            # Track latest service_date across ALL policies for stale check (must check all, not just ones needing refresh)
            latest_service_date = None
            latest_service_dt = None
            
            # First pass: Track latest service_date across all policies
            for policy in policies:
                if not isinstance(policy, dict):
                    continue
                service_date = policy.get('service_date', '')
                if service_date:
                    try:
                        service_dt = None
                        for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%m/%d/%Y']:
                            try:
                                service_dt = datetime.strptime(str(service_date).strip(), fmt)
                                break
                            except ValueError:
                                continue
                        if service_dt:
                            if latest_service_dt is None or service_dt > latest_service_dt:
                                latest_service_dt = service_dt
                                latest_service_date = service_date
                    except Exception:
                        pass
            
            # Check if patient is stale (120+ days after latest service_date) - do this before processing refresh candidates
            if latest_service_dt:
                if _is_stale_patient(latest_service_dt, max_age_days=max_stale_days):
                    # Patient is stale - skip entirely
                    continue
            
            # Second pass: Find policies that need refresh (non-zero remaining_amount, older than 24h)
            policies_needing_refresh = []
            
            for policy in policies:
                if not isinstance(policy, dict):
                    continue
                
                # Extract remaining_amount and check if non-zero
                remaining_amount_str = policy.get('remaining_amount', '')
                ok_amount, amount_value = _parse_amount_to_float(remaining_amount_str)
                
                if not ok_amount or amount_value <= 0.0:
                    # Skip zero or invalid amounts
                    continue
                
                # Check cached_at timestamp
                cached_at = policy.get('cached_at', '')
                if not cached_at:
                    # Missing cached_at - treat as needing refresh
                    policies_needing_refresh.append(policy)
                    continue
                
                try:
                    cached_dt = datetime.strptime(str(cached_at), '%Y-%m-%dT%H:%M:%SZ')
                    age = now_utc - cached_dt
                    if age >= cache_refresh_threshold:
                        # Cache is older than 24 hours - needs refresh
                        policies_needing_refresh.append(policy)
                except (ValueError, TypeError):
                    # Invalid cached_at - treat as needing refresh
                    policies_needing_refresh.append(policy)
            
            # Skip if no policies need refresh
            if not policies_needing_refresh:
                continue
            
            # Use the most recent policy needing refresh (or first if all equal)
            # Prefer policy with most recent cached_at or service_date
            selected_policy = None
            for policy in policies_needing_refresh:
                if not selected_policy:
                    selected_policy = policy
                    continue
                
                # Prefer policy with more recent service_date
                policy_service_date = policy.get('service_date', '')
                selected_service_date = selected_policy.get('service_date', '')
                
                if policy_service_date and selected_service_date:
                    try:
                        policy_dt = None
                        selected_dt = None
                        for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%m/%d/%Y']:
                            try:
                                if not policy_dt:
                                    policy_dt = datetime.strptime(str(policy_service_date).strip(), fmt)
                                if not selected_dt:
                                    selected_dt = datetime.strptime(str(selected_service_date).strip(), fmt)
                                if policy_dt and selected_dt:
                                    break
                            except ValueError:
                                continue
                        if policy_dt and selected_dt and policy_dt > selected_dt:
                            selected_policy = policy
                            continue
                    except Exception:
                        pass
                
                # Fallback: prefer policy with more recent cached_at
                policy_cached_at = policy.get('cached_at', '')
                selected_cached_at = selected_policy.get('cached_at', '')
                if policy_cached_at and selected_cached_at:
                    try:
                        policy_cached_dt = datetime.strptime(str(policy_cached_at), '%Y-%m-%dT%H:%M:%SZ')
                        selected_cached_dt = datetime.strptime(str(selected_cached_at), '%Y-%m-%dT%H:%M:%SZ')
                        if policy_cached_dt > selected_cached_dt:
                            selected_policy = policy
                    except Exception:
                        pass
            
            if not selected_policy:
                continue
            
            # Extract patient identifiers from selected policy
            patid = str(patient_id).strip()
            dob = selected_policy.get('dob', '')
            member_id = selected_policy.get('member_id', '')
            payer_id = selected_policy.get('payer_id', '')
            service_date = selected_policy.get('service_date', '')
            
            # Validate required fields
            if not (patid and dob and member_id):
                continue
            
            # Convert service_date to datetime if it's a string
            service_date_dt = None
            if service_date:
                if isinstance(service_date, datetime):
                    service_date_dt = service_date
                elif isinstance(service_date, str):
                    for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y']:
                        try:
                            service_date_dt = datetime.strptime(service_date.strip(), fmt)
                            break
                        except ValueError:
                            continue
            
            # Add patient tuple
            patients_to_refresh.append((patid, dob, member_id, payer_id, service_date_dt))
        
        return patients_to_refresh
    except Exception as e:
        _log("Error scanning cache for refresh candidates: {}".format(str(e)), level="WARNING")
        return []

def _validate_eligibility_params(payer_id, provider_last_name, dob_iso, member_id, npi):
    """
    Validate required parameters before making eligibility API calls.
    Returns (is_valid, validation_errors) tuple where validation_errors is a list of error messages.
    """
    errors = []
    
    # Validate payer_id
    if not payer_id:
        errors.append("payer_id is missing or empty")
    else:
        try:
            payer_id_str = str(payer_id).strip()
            if not payer_id_str:
                errors.append("payer_id is empty after conversion to string")
        except Exception:
            errors.append("payer_id cannot be converted to string")
    
    # Validate provider_last_name
    if not provider_last_name:
        errors.append("provider_last_name is missing or empty")
    else:
        try:
            provider_last_name_str = str(provider_last_name).strip()
            if not provider_last_name_str:
                errors.append("provider_last_name is empty after conversion to string")
        except Exception:
            errors.append("provider_last_name cannot be converted to string")
    
    # Validate dob_iso (should be in YYYY-MM-DD format)
    if not dob_iso:
        errors.append("dob_iso (date of birth) is missing or empty")
    else:
        try:
            dob_clean = str(dob_iso).strip()
            # Validate ISO date format (YYYY-MM-DD)
            datetime.strptime(dob_clean, '%Y-%m-%d')
        except (ValueError, TypeError):
            # Limit length to avoid PHI exposure
            dob_preview = str(dob_iso)[:20] if dob_iso else "None"
            errors.append("dob_iso must be in YYYY-MM-DD format, got: '{}'".format(dob_preview))
        except Exception:
            errors.append("dob_iso cannot be converted to string")
    
    # Validate member_id (should be alphanumeric, 2-80 chars after normalization)
    if not member_id:
        errors.append("member_id is missing or empty")
    else:
        try:
            member_clean = str(member_id).strip()
            # Normalize to alphanumeric only
            normalized = ''.join(c for c in member_clean if c.isalnum())
            if len(normalized) < 2:
                errors.append("member_id must be at least 2 alphanumeric characters after normalization")
            elif len(normalized) > 80:
                errors.append("member_id must be at most 80 alphanumeric characters after normalization")
        except Exception:
            errors.append("member_id cannot be converted to string")
    
    # Validate npi (should be 10 digits)
    if not npi:
        errors.append("npi is missing or empty")
    else:
        try:
            npi_clean = str(npi).strip()
            if not npi_clean.isdigit():
                errors.append("npi must contain only digits")
            elif len(npi_clean) != 10:
                errors.append("npi must be exactly 10 digits, got {} digits".format(len(npi_clean)))
        except Exception:
            errors.append("npi cannot be converted to string")
    
    return (len(errors) == 0, errors)


def _optumai_first_with_legacy_fallback(client, payer_id, provider_last_name, dob_iso, member_id, npi, service_date=None):
    # Try OptumAI eligibility; on safe failure categories, fall back to Legacy.
    # Returns normalized merged result dict when possible; else None.
    # service_date: Optional datetime object or string in YYYY-MM-DD format for plan selection
    opt_data = None
    legacy_data = None
    # Flag to track if we should force fallback due to non-200 with no usable data
    force_legacy_fallback = False

    # Normalize DOB to ISO format (YYYY-MM-DD) before validation
    # The dob_iso parameter may come in various formats (MM/DD/YYYY, etc.) from CSV
    dob_normalized = _normalize_dob_to_iso(dob_iso) if dob_iso else dob_iso
    
    # Validate required parameters before making API calls (use normalized DOB)
    is_valid, validation_errors = _validate_eligibility_params(payer_id, provider_last_name, dob_normalized, member_id, npi)
    if not is_valid:
        error_msg = "Pre-API validation failed: {}".format("; ".join(validation_errors))
        _log(error_msg, level="WARNING")
        # Return None to skip API call - validation errors should be caught before this point
        return None
    
    # Attempt OptumAI
    try:
        if api_core and hasattr(api_core, "get_eligibility_super_connector"):
            # Extract service_start and service_end from service_date if provided
            service_start = _parse_service_date_to_iso(service_date)
            service_end = service_start  # Single day surgeries
            
            opt_data = api_core.get_eligibility_super_connector(
                client, payer_id, provider_last_name, "MemberIDDateOfBirth", dob_normalized, member_id, npi,
                service_start=service_start, service_end=service_end
            )
            # Check if we got usable data, even if there are warnings/errors
            has_usable_data = False
            if opt_data and isinstance(opt_data, dict):
                # Check if we have patient/member data (indicates usable response)
                has_member_id = bool(opt_data.get("memberId"))
                has_patient_name = bool(opt_data.get("firstName") or opt_data.get("lastName"))
                has_insurance_info = bool(opt_data.get("policyNumber") or opt_data.get("eligibilityStartDate"))
                # Also check rawGraphQLResponse for eligibility records
                raw_response = opt_data.get("rawGraphQLResponse", {})
                if raw_response:
                    data = raw_response.get("data", {})
                    check_eligibility = data.get("checkEligibility", {})
                    eligibility_list = check_eligibility.get("eligibility", [])
                    has_eligibility_records = bool(eligibility_list and len(eligibility_list) > 0)
                    has_usable_data = has_member_id or has_patient_name or has_insurance_info or has_eligibility_records
                else:
                    has_usable_data = has_member_id or has_patient_name or has_insurance_info
            
            # If statuscode present and non-200, check if we still have usable data
            try:
                status_code = opt_data.get("statuscode")
                if status_code is not None and not is_ok_200(status_code):
                    # If we have usable data despite non-200 status, log warning but keep the data
                    if has_usable_data:
                        warning_msg = opt_data.get("message", "Unknown error")
                        graphql_warning = opt_data.get("graphql_warning", {})
                        if graphql_warning and graphql_warning.get("is_unsupported_feature"):
                            _log("OptumAI returned usable data with unsupported feature warning: {}. Using OptumAI data.".format(
                                graphql_warning.get("message", warning_msg)
                            ), level="WARNING")
                        else:
                            _log("OptumAI returned usable data with non-200 status ({}): {}. Using OptumAI data.".format(
                                status_code, warning_msg
                            ), level="WARNING")
                        # Keep opt_data - it has usable information
                    else:
                        # No usable data, flag for fallback
                        force_legacy_fallback = True
                        opt_data = None  # Clear opt_data to trigger fallback
                        _log("OptumAI non-200 status ({}): No usable data. Will attempt legacy fallback.".format(
                            status_code
                        ), level="WARNING")
            except Exception:
                pass
    except Exception as e:
        # Before falling back, check if opt_data was set and contains usable data
        # Sometimes exceptions are raised even when we got usable data
        # Initialize variable to track if we have usable data
        has_usable_data_from_exception = False
        try:
            if opt_data and isinstance(opt_data, dict):
                has_member_id = bool(opt_data.get("memberId"))
                has_patient_name = bool(opt_data.get("firstName") or opt_data.get("lastName"))
                has_insurance_info = bool(opt_data.get("policyNumber") or opt_data.get("eligibilityStartDate"))
                raw_response = opt_data.get("rawGraphQLResponse", {})
                if raw_response:
                    data = raw_response.get("data", {})
                    check_eligibility = data.get("checkEligibility", {})
                    eligibility_list = check_eligibility.get("eligibility", [])
                    has_eligibility_records = bool(eligibility_list and len(eligibility_list) > 0)
                    has_usable_data_from_exception = has_member_id or has_patient_name or has_insurance_info or has_eligibility_records
                else:
                    has_usable_data_from_exception = has_member_id or has_patient_name or has_insurance_info
        except Exception:
            # If checking for usable data fails, assume we don't have it
            has_usable_data_from_exception = False
        
        # Initialize error classification variables (needed for logging below)
        error_str = str(e)
        is_validation_error = False
        is_unsupported_feature = False
        
        # If we have usable data, don't fallback - use what we got
        if has_usable_data_from_exception:
            _log("OptumAI exception occurred but usable data was received. Using OptumAI data: {}".format(
                str(e)[:200]
            ), level="WARNING")
            # opt_data is already set, continue with it (don't set to None)
            # The merge_responses function will handle it
        else:
            # No usable data, proceed with fallback logic
            # Check for GraphQL validation errors specifically
            validation_terms = ["BACKEND_VALIDATION_FAILED", "ED270BR", "mandatory attributes", "Bad request"]
            for term in validation_terms:
                if term in error_str:
                    is_validation_error = True
                    break
            
            # Exclude payer-specific unsupported feature errors from validation error category
            # These should trigger fallback but are not validation errors (e.g., "PSPFNS : Currently not Supported for UMR")
            unsupported_feature_terms = ["not supported", "pspfns", "currently not supported"]
            for term in unsupported_feature_terms:
                if term.lower() in error_str.lower():
                    is_unsupported_feature = True
                    break
            
            # If it's an unsupported feature error, don't treat it as a validation error
            if is_unsupported_feature:
                is_validation_error = False
            
            # Enhanced error logging for payer-specific unsupported feature errors
            if is_unsupported_feature:
                _log("OptumAI payer-specific feature not supported (no usable data): {}. Will attempt legacy fallback.".format(
                    error_str[:200]  # Limit error message length
                ), level="WARNING")
        
        # Enhanced error logging for validation errors - log sanitized parameters
        # (Only log if we don't have usable data, to avoid duplicate logs)
        if is_validation_error and not has_usable_data_from_exception:
            # Log sanitized parameter summary (no PHI)
            try:
                dob_format_check = "invalid"
                if dob_normalized:
                    try:
                        dob_str = str(dob_normalized).strip()
                        if len(dob_str) == 10:  # YYYY-MM-DD format
                            dob_format_check = "valid"
                    except Exception:
                        pass
                
                member_id_len = 0
                if member_id:
                    try:
                        member_id_len = len(str(member_id).strip())
                    except Exception:
                        pass
                
                npi_len = 0
                if npi:
                    try:
                        npi_len = len(str(npi).strip())
                    except Exception:
                        pass
                
                param_summary = "payer_id={}, provider_last_name={}, dob_format={}, member_id_len={}, npi_len={}".format(
                    "present" if payer_id else "missing",
                    "present" if provider_last_name else "missing",
                    dob_format_check,
                    member_id_len,
                    npi_len
                )
            except Exception:
                # Fallback if parameter summary construction fails
                param_summary = "parameter summary unavailable"
            _log("OptumAI GraphQL validation error - Parameters: {}. Error: {}. Will attempt legacy fallback.".format(
                param_summary, error_str[:200]  # Limit error message length
            ), level="WARNING")
        
        # Classify, then decide to fallback
        try:
            if classify_api_failure:
                code, message = classify_api_failure(e, "OPTUMAI eligibility API")
                if is_validation_error:
                    # Log validation errors as WARNING (not ERROR) - these are expected in some cases
                    _log("OptumAI GraphQL validation error: {} - {}. Will attempt legacy fallback.".format(code, message), level="WARNING")
                else:
                    _log("OptumAI failure classified: {} - {}".format(code, message), level="WARNING")
            else:
                if is_validation_error:
                    _log("OptumAI GraphQL validation error (unclassified): {}. Will attempt legacy fallback.".format(error_str), level="WARNING")
                else:
                    _log("OptumAI failure (unclassified): {}".format(error_str), level="WARNING")
        except Exception:
            pass
        
        # Only set opt_data to None if we don't have usable data
        # (has_usable_data_from_exception is only set if we checked and found data)
        if not has_usable_data_from_exception:
            opt_data = None

    # Determine if fallback needed (either no opt_data or force_legacy_fallback flag set)
    need_fallback = opt_data is None or force_legacy_fallback

    if need_fallback:
        try:
            if api_core and hasattr(api_core, "get_eligibility_v3") and client and hasattr(client, "get_access_token"):
                token = client.get_access_token("UHCAPI")
                if token:
                    # Extract service dates for legacy API too
                    service_start = _parse_service_date_to_iso(service_date)
                    service_end = service_start  # Single day surgeries
                    
                    legacy_data = api_core.get_eligibility_v3(
                        client, payer_id, provider_last_name, "MemberIDDateOfBirth", dob_normalized, member_id, npi,
                        service_start=service_start, service_end=service_end
                    )
                else:
                    _log("Legacy fallback skipped: no access token", level="WARNING")
        except Exception as e:
            _log("Legacy fallback failed: {}".format(str(e)), level="WARNING")
            legacy_data = None

    # Merge using existing utility - pass service_date for plan selection when multiple plans found
    try:
        if merge_responses:
            # Convert service_date to YYYY-MM-DD string format for merge_responses
            service_date_str = _parse_service_date_to_iso(service_date)
            
            merged = merge_responses(opt_data, legacy_data, dob_normalized, member_id, service_date=service_date_str)
        else:
            merged = opt_data or legacy_data or None
        
        # Silent insurance type mapping collection (for error reporting)
        try:
            if collect_insurance_type_mapping_from_response is not None:
                mapping_entry = None
                if merged:
                    mapping_entry = collect_insurance_type_mapping_from_response(merged)
                if not mapping_entry and opt_data:
                    mapping_entry = collect_insurance_type_mapping_from_response(opt_data)
                if not mapping_entry and legacy_data:
                    mapping_entry = collect_insurance_type_mapping_from_response(legacy_data)
                
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
        
        return merged
    except Exception as e:
        _log("merge_responses error: {}".format(str(e)), level="WARNING")
        return opt_data or legacy_data or None

# Public API
def run_batch_from_csv(config):
    """
    Default batch behavior:
    - Read CSV rows
    - Resolve PATID, DOB(ISO), Member ID, and payer id if possible
    - Exclude PATIDs with cached remaining_amount parsed as 0
    - Fetch eligibility OptumAI-first (Legacy fallback), persist code & remaining_amount
    """
    _log("Starting deductible cache build process", level="INFO")
    try:
        _get_config, (_cfg_cache, _crosswalk_cache) = create_config_cache()
    except Exception:
        def _get_config():
            return config or {}, {}

    cfg, crosswalk = _get_config()
    if isinstance(config, dict) and config:
        # Prefer provided config when passed in
        cfg.update(config)

    csv_path = cfg.get("CSV_FILE_PATH", "")
    if not csv_path:
        _log("CSV_FILE_PATH not configured in config.json", level="INFO")
        _print_error("CSV_FILE_PATH not configured in config.json. Cache build skipped.")
        return []
    
    if not os.path.exists(csv_path):
        _log("CSV file not found at: {}".format(csv_path), level="INFO")
        _print_error("CSV file not found at: {}. Cache build skipped.".format(csv_path))
        return []
    
    if not MediBot_Preprocessor_lib or not hasattr(MediBot_Preprocessor_lib, "load_csv_data"):
        _log("MediBot_Preprocessor_lib not available or missing load_csv_data", level="INFO")
        _print_error("MediBot_Preprocessor_lib not available. Cache build skipped.")
        return []
    
    try:
        rows = MediBot_Preprocessor_lib.load_csv_data(csv_path)
        _log("Loaded {} rows from CSV".format(len(rows) if rows else 0), level="INFO")
    except Exception as e:
        _log("Failed to load CSV: {}".format(str(e)), level="INFO")
        _print_error("Failed to load CSV file at: {}. Error: {}. Cache build skipped.".format(csv_path, str(e)))
        return []

    # Resolve payer mapping cache for O(N) lookups when utilities exist
    payer_cache = {}
    try:
        if resolve_payer_ids_from_csv:
            payer_cache = resolve_payer_ids_from_csv(rows, cfg, crosswalk, None)
    except Exception:
        payer_cache = {}

    csv_dir = _safe_get_csv_dir(cfg)
    if csv_dir:
        _log("Cache directory resolved: '{}'".format(csv_dir), level="INFO")
    else:
        _log("WARNING: Cache directory empty", level="INFO")
        _print_warning("Cache directory is empty. Check CSV_FILE_PATH in config.json.")
    
    # Build patient tuples with service dates from CSV
    patients = []
    # Track (dob, member_id) tuples to avoid duplicates when merging with cache
    # DOB is normalized to ISO format (YYYY-MM-DD) for consistent comparison
    patient_keys = set()
    
    for row in rows:
        try:
            patid = str(row.get("Patient ID #2", row.get("Patient ID", ""))).strip()
            dob_raw = row.get("Patient DOB", row.get("DOB", "")).strip()
            member_id = str(row.get("Primary Policy Number", row.get("Ins1 Member ID", ""))).strip()
            if not (patid and dob_raw and member_id):
                continue
            
            # Normalize DOB to ISO format for consistent comparison
            dob_normalized = _normalize_dob_to_iso(dob_raw)
            
            # payer id (best-effort): try cache first, then fallback to direct CSV extraction
            payer_id = None
            try:
                if get_payer_id_for_patient and payer_cache is not None:
                    # Use original dob for payer lookup (cache may expect original format)
                    payer_id = get_payer_id_for_patient(dob_raw, member_id, payer_cache)
            except Exception:
                payer_id = None
            
            # Fallback: Extract payer ID directly from CSV row if cache lookup failed
            if not payer_id:
                try:
                    payer_id_raw = row.get("Ins1 Payer ID", "").strip()
                    if payer_id_raw:
                        payer_id = payer_id_raw
                except Exception:
                    payer_id = None
            
            # Extract service date from CSV row if utility available
            service_date = None
            try:
                if _extract_service_date_from_csv_row:
                    _, service_date_dt = _extract_service_date_from_csv_row(row)
                    if service_date_dt and service_date_dt != datetime.min:
                        service_date = service_date_dt
            except Exception:
                pass
            
            # Store original dob in patient tuple (for API calls), but use normalized for key
            patients.append((patid, dob_raw, member_id, payer_id, service_date))
            # Track patient key with normalized DOB for duplicate detection
            patient_keys.add((dob_normalized, member_id))
        except Exception:
            continue

    _log("Built {} patient tuples for processing".format(len(patients)), level="INFO")

    # Get patients from cache that need refresh
    cache_patients = []
    if csv_dir:
        try:
            cache_patients = get_patients_from_cache_for_refresh(csv_dir, max_stale_days=120)
            if cache_patients:
                _log("Found {} patients from cache needing refresh".format(len(cache_patients)), level="INFO")
        except Exception as e:
            _log("Error getting cache patients for refresh: {}".format(str(e)), level="WARNING")
    
    # Merge cache patients with CSV patients, avoiding duplicates
    for cache_patient in cache_patients:
        if len(cache_patient) >= 3:
            (patid, dob_raw, member_id) = cache_patient[:3]
            # Normalize cache DOB to ISO format for consistent comparison with CSV patients
            dob_normalized = _normalize_dob_to_iso(dob_raw)
            cache_key = (dob_normalized, member_id)
            if cache_key not in patient_keys:
                # Not in CSV - add to patients list
                patients.append(cache_patient)
                patient_keys.add(cache_key)
            # If already in CSV, prefer CSV version (it's more current)

    return run_batch(patients, cfg)

def run_batch(patients, config):
    """
    Run eligibility for patients excluding those with cached remaining_amount == 0.
    patients: list of tuples (patid, dob_iso, member_id, payer_id_or_None, service_date_or_None)
    """
    _log("Processing {} patients for cache build".format(len(patients) if patients else 0), level="INFO")
    if not patients:
        print("Deductible_v1.5: No patients to process.")
        return []

    client = get_api_core_client()
    if client is None and api_core:
        try:
            client = api_core.APIClient()
        except Exception:
            client = None
    if client is None:
        print("Deductible_v1.5: API client unavailable.")
        return []

    cfg = config or {}
    csv_dir = _safe_get_csv_dir(cfg)
    provider_last_name = cfg.get("MediLink_Config", {}).get("default_billing_provider_last_name", "Unknown")
    npi = cfg.get("MediLink_Config", {}).get("default_billing_provider_npi", "Unknown")

    # Get valid payer IDs for OPTUMAI endpoint (used for filtering before API calls)
    valid_payer_ids = set()
    try:
        if api_core and hasattr(api_core, "get_valid_payer_ids_for_endpoint") and client:
            # Get valid payer IDs for OPTUMAI endpoint
            valid_payer_ids = set(api_core.get_valid_payer_ids_for_endpoint(client, 'OPTUMAI'))
    except Exception:
        # If we can't get valid payer IDs, we'll still process but may get errors later
        pass

    processed = []
    cache_hits_zero = 0
    cache_hits_recent = 0
    fetched = 0
    patients_to_process = []
    api_eligible_count = 0  # Patients with valid payer_id (API-eligible)
    invalid_payer_count = 0  # Patients with invalid payer_id (filtered out)
    validation_failures = 0  # Pre-API validation failures
    api_call_failures = 0  # API call failures (not validation)

    # Partition patients: cache (remaining <=0) vs API targets
    for patient_tuple in patients:
        if len(patient_tuple) >= 5:
            (patid, dob_iso, member_id, payer_id, service_date) = patient_tuple
        else:
            (patid, dob_iso, member_id, payer_id) = patient_tuple
            service_date = None
        try:
            cached = None
            if cache_lookup:
                service_date_str = _parse_service_date_to_iso(service_date)
                cached = cache_lookup(patient_id=patid, csv_dir=csv_dir, return_full=True, service_date=service_date_str)
            
            # Validate cached code before using cache (invalid codes should trigger API refresh)
            if cached:
                cached_code = cached.get('code', '')
                if not _is_valid_insurance_code(cached_code):
                    # Invalid code (description, "Not Available", etc.) - skip cache and call API
                    _log("Cache code invalid for patient {}: '{}' - will call API".format(
                        patid, cached_code[:50] if cached_code else '(empty)'), level="DEBUG")
                    cached = None  # Clear cached so we proceed to API call
            
            # Check cache freshness and remaining amount only if code is valid
            if cached:
                recent_cache = _is_recent_cache_payload(cached)
                if _is_ready_from_cache_payload(cached):
                    # Zero remaining amount - skip API call
                    cache_hits_zero += 1
                    continue
                elif recent_cache:
                    # Recent cache (<24h) - skip API call
                    cache_hits_recent += 1
                    continue
        except Exception:
            pass

        if not payer_id:
            _log("Skipped patient with missing payer_id (PATID={})".format(patid), level="DEBUG")
            continue

        # Validate payer_id against valid list (filter out invalid payer IDs before API calls)
        if valid_payer_ids and payer_id not in valid_payer_ids:
            invalid_payer_count += 1
            _log("Skipped patient with invalid payer_id '{}' (PATID={}) - not in valid OPTUMAI payer list".format(
                payer_id, patid), level="DEBUG")
            continue

        # Patient has valid payer_id - count as API-eligible
        api_eligible_count += 1
        patients_to_process.append((patid, dob_iso, member_id, payer_id, service_date))

    if cache_hits_zero > 0:
        _log("Skipped {} patients with zero remaining_amount (cached)".format(cache_hits_zero), level="INFO")
    if cache_hits_recent > 0:
        _log("Skipped {} patients with recent cache (<24h)".format(cache_hits_recent), level="INFO")
    
    total_api_targets = len(patients_to_process)
    # Always show progress bar initialization message
    print("Building deductible cache...")
    if total_api_targets > 0:
        _log("Fetching eligibility for {} patients via API".format(total_api_targets), level="INFO")
        _print_progress(0, total_api_targets)
    else:
        print("No patients require API fetch (all cached or zero remaining)")
        _log("No patients require API fetch (all cached or zero remaining)", level="INFO")
    
    processed_count = 0
    # Collect errors for error report context
    patient_errors = []

    for patid, dob_iso, member_id, payer_id, service_date in patients_to_process:
        try:
            result = _optumai_first_with_legacy_fallback(
                client, payer_id, provider_last_name, dob_iso, member_id, npi, service_date=service_date
            )
            if result is None:
                # Pre-API validation failed (returned None from validation function)
                validation_failures += 1
            elif isinstance(result, dict):
                fetched += 1
                try:
                    if put_entry_from_enhanced_result:
                        # Ensure patient_id is in the result dict for cache storage
                        # merge_responses doesn't include patient_id, so we need to add it
                        if 'patient_id' not in result or not result.get('patient_id'):
                            result['patient_id'] = patid
                        
                        service_date_for_api = service_date
                        if service_date and isinstance(service_date, datetime):
                            service_date_for_api = service_date
                        elif service_date:
                            service_date_for_api = _parse_service_date_to_iso(service_date)
                        put_entry_from_enhanced_result(
                            csv_dir, result, dob_iso, member_id, payer_id,
                            csv_row=None,
                            service_date_for_api=service_date_for_api,
                            context="batch"
                        )
                except Exception:
                    pass
                processed.append(result)
            else:
                # Unexpected return type - count as API failure
                api_call_failures += 1
        except Exception as e:
            # Catch all exceptions to prevent one patient from stopping entire batch
            error_str = str(e)
            # Check for GraphQL validation errors
            validation_terms = ["BACKEND_VALIDATION_FAILED", "ED270BR", "mandatory attributes", "Bad request"]
            is_validation_error = False
            for term in validation_terms:
                if term in error_str:
                    is_validation_error = True
                    break
            
            # Exclude payer-specific unsupported feature errors from validation error category
            # These should trigger fallback but are not validation errors (e.g., "PSPFNS : Currently not Supported for UMR")
            unsupported_feature_terms = ["not supported", "pspfns", "currently not supported"]
            is_unsupported_feature = False
            for term in unsupported_feature_terms:
                if term.lower() in error_str.lower():
                    is_unsupported_feature = True
                    break
            
            # If it's an unsupported feature error, don't treat it as a validation error
            if is_unsupported_feature:
                is_validation_error = False
            
            # Enhanced error logging for payer-specific unsupported feature errors
            if is_unsupported_feature:
                _log("OptumAI payer-specific feature not supported for patient {}: {}. Skipping.".format(
                    patid, error_str[:200]  # Limit error message length
                ), level="WARNING")
            
            # Track failures
            if is_validation_error:
                validation_failures += 1
            else:
                api_call_failures += 1
            
            # Collect error for error report context
            patient_errors.append({
                "patient": patid,
                "error": error_str,
                "is_validation": is_validation_error
            })
            
            if is_validation_error:
                _log("GraphQL validation error for patient {}: {}. Skipping.".format(patid, error_str), level="WARNING")
            else:
                _log("API error for patient {}: {}. Skipping.".format(patid, error_str), level="ERROR")
        
        # Always increment processed_count and update progress, even on errors
        processed_count += 1
        if total_api_targets > 0:
            _print_progress(processed_count, total_api_targets)
    
    # Log summary of errors for error report context
    if patient_errors:
        validation_count = 0
        for e in patient_errors:
            if e.get("is_validation"):
                validation_count += 1
        other_count = len(patient_errors) - validation_count
        _log("Encountered {} GraphQL validation errors and {} other errors during batch processing".format(
            validation_count, other_count), level="WARNING")

    # Always complete progress bar with newline, even if no patients processed
    sys.stdout.write("\n")
    sys.stdout.flush()

    # Check cache status after batch to verify it was written
    cache_patient_count = 0
    cache_file_exists = False
    try:
        if csv_dir and load_cache:
            cache_dict = load_cache(csv_dir)
            cache_patient_count = len(cache_dict.get('by_patient_id', {}))
            # Check if cache file exists
            try:
                from MediLink.insurance_type_cache import get_cache_path
                cache_path = get_cache_path(csv_dir)
                cache_file_exists = os.path.exists(cache_path) if cache_path else False
            except Exception:
                pass
    except Exception:
        pass
    
    print("Deductible_v1.5: Batch complete. Skipped (cached zero): {} | Recent cache (<24h): {} | Invalid payer IDs: {} | API-eligible: {} | Validation failures: {} | API failures: {} | Fetched: {} | Processed via API: {} | Total from CSV: {} | Cache file: {} | Patients in cache: {}".format(
        cache_hits_zero, cache_hits_recent, invalid_payer_count, api_eligible_count, validation_failures, api_call_failures, fetched, total_api_targets, len(patients), "exists" if cache_file_exists else "missing", cache_patient_count
    ))
    _log("Cache build complete: skipped (zero)={}, skipped (recent)={}, invalid_payer_ids={}, api_eligible={}, validation_failures={}, api_failures={}, fetched={}, processed_via_api={}, total_from_csv={}, cache_file_exists={}, cache_patient_count={}".format(
        cache_hits_zero, cache_hits_recent, invalid_payer_count, api_eligible_count, validation_failures, api_call_failures, fetched, total_api_targets, len(patients), cache_file_exists, cache_patient_count
    ), level="INFO")
    return processed

def run_headless_batch(config=None):
    """
    Headless helper that installs error hooks and runs the batch processor.
    """
    _install_exception_hook()
    effective_config = config if isinstance(config, dict) else {}
    try:
        return run_batch_from_csv(effective_config)
    except Exception as exc:
        _report_batch_failure(exc)
        raise


