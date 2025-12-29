# insurance_type_cache.py
# XP/Python 3.4.4 compatible helper for persisting insurance type codes
# Stored alongside the CSV file referenced by config['CSV_FILE_PATH']
#
# Schema v2 (kept lean; avoid names/PHI where possible):
# {
#   "version": 2,
#   "lastUpdated": "YYYY-MM-DDTHH:MM:SSZ",
#   "by_patient_id": {
#       "<patient_id>": {
#           "policies": [
#               {
#                   "code": "12",
#                   "payer_id": "87726",
#                   "member_id": "...",
#                   "dob": "YYYY-MM-DD",
#                   "remaining_amount": "500.00",
#                   "plan_start_date": "2025-01-01",
#                   "plan_end_date": "2025-12-31",
#                   "service_date": "2025-06-15",
#                   "cached_at": "2025-11-16T22:00:44Z"
#               }
#           ]
#       }
#   }
# }
# All lookups use by_patient_id with PATID (5-digit patient ID from CSV "Patient ID #2").
# Supports multiple policies per patient with service date matching.

from __future__ import print_function

import os
import io
import json
import time
from datetime import datetime, timedelta

# Safe logger import with fallback
try:
    from MediCafe.core_utils import get_shared_config_loader
    _logger = get_shared_config_loader()
except Exception:
    _logger = None

def _log(message, level="DEBUG"):
    """Helper to log messages if logger is available."""
    if _logger and hasattr(_logger, 'log'):
        try:
            _logger.log(message, level=level)
        except (OSError, IOError):
            # Windows logging stream flush can fail with OSError [Errno 22] - ignore silently
            pass
        except Exception:
            pass

# Module-level cache to avoid reloading cache file repeatedly
# Keyed by csv_dir (normalized path), stores (cache_dict, mtime) tuples
_cache_memory = {}


def _now_iso_utc():
    # Minimal ISO-like timestamp to avoid pulling in datetime/tz complexities on XP
    try:
        # time.gmtime returns UTC; format YYYY-MM-DDTHH:MM:SSZ
        t = time.gmtime()
        return "%04d-%02d-%02dT%02d:%02d:%02dZ" % (
            t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec
        )
    except Exception:
        return ""


def get_csv_dir_from_config(config):
    """
    Resolve the CSV directory from the provided config without hardcoding paths.
    Falls back to empty string if not available.
    """
    try:
        csv_path = config.get('CSV_FILE_PATH', '')
        if csv_path:
            return os.path.dirname(csv_path)
    except Exception:
        pass
    return ''


def get_cache_path(csv_dir):
    """Return the full path to the cache file in the given directory."""
    return os.path.join(csv_dir or '', 'insurance_type_cache.json')


def _empty_cache():
    return {"version": 2, "lastUpdated": _now_iso_utc(), "by_patient_id": {}}


def save_cache(csv_dir, cache_dict):
    """
    Save the cache JSON with a best-effort atomic write (temp file + rename).
    Avoid verbose logging to keep PHI out of logs.
    """
    if not csv_dir:
        _log("Cache save_cache SKIP: empty csv_dir", level="WARNING")
        return
    try:
        if not os.path.isdir(csv_dir):
            # Best effort: attempt to create directory if missing
            try:
                os.makedirs(csv_dir)
                _log("Cache save_cache: created directory '{}'".format(csv_dir), level="DEBUG")
            except Exception as e:
                _log("Cache save_cache ERROR: failed to create directory '{}': {}".format(csv_dir, str(e)), level="WARNING")
                return

        cache_dict = cache_dict or _empty_cache()
        cache_dict['lastUpdated'] = _now_iso_utc()

        path = get_cache_path(csv_dir)
        tmp_path = path + '.tmp'
        
        # Log the path being used for debugging
        _log("Cache save_cache: saving to '{}'".format(path), level="DEBUG")
        
        # Write to temp file first
        try:
            with io.open(tmp_path, 'w', encoding='utf-8') as f:
                json_str = json.dumps(cache_dict, indent=2, sort_keys=True)
                f.write(json_str)
            _log("Cache save_cache: temp file written to '{}' ({} bytes)".format(tmp_path, len(json_str)), level="DEBUG")
        except Exception as e:
            _log("Cache save_cache ERROR: failed to write temp file '{}': {}".format(tmp_path, str(e)), level="WARNING")
            return

        # Invalidate in-memory cache for this csv_dir so it reloads on next lookup
        cache_key = csv_dir or ''
        
        # On Windows/XP, os.rename will overwrite if target exists when on same volume
        try:
            os.rename(tmp_path, path)
            _log("Cache save_cache: successfully saved to '{}'".format(path), level="DEBUG")
            if cache_key in _cache_memory:
                del _cache_memory[cache_key]
        except Exception as e:
            # Best effort fallback: try remove then rename
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
            try:
                os.rename(tmp_path, path)
                _log("Cache save_cache: successfully saved to '{}' (after retry)".format(path), level="DEBUG")
                if cache_key in _cache_memory:
                    del _cache_memory[cache_key]
            except Exception as e2:
                # Give up silently; the temp file remains
                _log("Cache save_cache ERROR: failed to save to '{}': {}".format(path, str(e2)), level="WARNING")
                pass
    except Exception as e:
        _log("Cache save_cache ERROR: exception saving cache: {}".format(str(e)), level="WARNING")


def load_cache(csv_dir):
    """
    Load the cache JSON. Returns a dict. If file does not exist or is invalid, returns empty cache structure.
    Automatically migrates v1 to v2 format if needed.
    """
    path = get_cache_path(csv_dir)
    try:
        if not path:
            _log("Cache load: path is empty (csv_dir='{}')".format(csv_dir), level="DEBUG")
            return _empty_cache()
        if not os.path.exists(path):
            _log("Cache file not found at '{}'. Using empty cache.".format(path), level="INFO")
            return _empty_cache()
        _log("Loading cache from '{}'".format(path), level="DEBUG")
        # Use io.open for XP compatibility and explicit encoding
        with io.open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Basic shape validation
            if not isinstance(data, dict):
                _log("Cache load: invalid data type (not dict) at '{}'".format(path), level="WARNING")
                return _empty_cache()
            
            # Check version and migrate if needed
            version = data.get('version', 1)
            if version == 1:
                _log("Cache load: migrating v1 to v2 format", level="INFO")
                data = _migrate_v1_to_v2(data)
                # Save migrated cache
                try:
                    save_cache(csv_dir, data)
                except Exception:
                    pass  # Best effort
            
            # Ensure v2 structure
            if 'by_patient_id' not in data:
                data['by_patient_id'] = {}
            
            # Run cleanup to remove stale patients (1+ year old)
            try:
                removed_count = _cleanup_stale_patients(data, max_age_days=730)
                if removed_count > 0:
                    _log("Cache load: removed {} stale patient entries (1+ year old)".format(removed_count), level="INFO")
                    # Save cleaned cache
                    try:
                        save_cache(csv_dir, data)
                    except Exception:
                        pass  # Best effort
            except Exception as e:
                _log("Cache cleanup error: {}".format(str(e)), level="WARNING")
            
            _log("Cache load: SUCCESS from '{}'".format(path), level="DEBUG")
            patient_count = len(data.get('by_patient_id', {}))
            _log("Cache loaded: {} patients in cache".format(patient_count), level="DEBUG")
            if patient_count == 0:
                _log("WARNING: Cache file exists but contains no patient data", level="INFO")
            return data
    except Exception as e:
        _log("Cache load: exception '{}' at '{}'".format(str(e), path), level="WARNING")
        # Never raise; return empty to avoid breaking flows
        return _empty_cache()


def _normalize_str(value):
    try:
        if value is None:
            return ''
        s = str(value).strip()
        return s
    except Exception:
        return ''


def _parse_date(date_str):
    """Parse date string in YYYY-MM-DD format to datetime object. Returns None if invalid."""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def _service_date_in_range(service_date, plan_start, plan_end):
    """
    Check if service_date falls within plan_start and plan_end range.
    Returns True if service_date is within range, False otherwise.
    If plan_start/plan_end are missing, uses service_date as single-day range.
    """
    if not service_date:
        return False
    
    service_dt = _parse_date(service_date)
    if not service_dt:
        return False
    
    plan_start_dt = _parse_date(plan_start) if plan_start else None
    plan_end_dt = _parse_date(plan_end) if plan_end else None
    
    # If both dates missing, use service_date as single-day range
    if not plan_start_dt and not plan_end_dt:
        return True
    
    # If only one date missing, use service_date as boundary
    if not plan_start_dt:
        plan_start_dt = service_dt
    if not plan_end_dt:
        plan_end_dt = service_dt
    
    return plan_start_dt <= service_dt <= plan_end_dt


def _find_policy_by_service_date(policies, service_date):
    """
    Find policy where service_date falls within plan_start_date and plan_end_date range.
    Returns policy dict or None if not found.
    """
    if not policies or not service_date:
        return None
    
    for policy in policies:
        plan_start = policy.get('plan_start_date', '')
        plan_end = policy.get('plan_end_date', '')
        if _service_date_in_range(service_date, plan_start, plan_end):
            return policy
    
    return None


def _find_most_recent_policy(policies):
    """
    Get most recent policy by cached_at timestamp, or by plan_end_date if cached_at not available.
    Returns policy dict or None if policies empty.
    """
    if not policies:
        return None
    
    # Try to find by cached_at first
    most_recent = None
    most_recent_time = None
    
    for policy in policies:
        cached_at = policy.get('cached_at', '')
        if cached_at:
            try:
                # Parse ISO timestamp (YYYY-MM-DDTHH:MM:SSZ)
                cached_dt = datetime.strptime(cached_at, '%Y-%m-%dT%H:%M:%SZ')
                if most_recent_time is None or cached_dt > most_recent_time:
                    most_recent_time = cached_dt
                    most_recent = policy
            except (ValueError, TypeError):
                pass
    
    if most_recent:
        return most_recent
    
    # Fallback to plan_end_date
    most_recent = None
    most_recent_date = None
    
    for policy in policies:
        plan_end = policy.get('plan_end_date', '')
        if plan_end:
            plan_end_dt = _parse_date(plan_end)
            if plan_end_dt:
                if most_recent_date is None or plan_end_dt > most_recent_date:
                    most_recent_date = plan_end_dt
                    most_recent = policy
    
    # Last resort: return first policy
    return most_recent or (policies[0] if policies else None)


def _cleanup_stale_patients(cache_dict, max_age_days=730):
    """
    Remove patient entries where the latest service_date across all policies is older than max_age_days.
    Returns count of removed patients.
    """
    if not isinstance(cache_dict, dict):
        return 0
    
    by_pid = cache_dict.get('by_patient_id', {})
    if not isinstance(by_pid, dict):
        return 0
    
    removed_count = 0
    today = datetime.now()
    cutoff_date = today - timedelta(days=max_age_days)
    
    patient_ids_to_remove = []
    
    for patient_id, patient_data in by_pid.items():
        if not isinstance(patient_data, dict):
            continue
        
        policies = patient_data.get('policies', [])
        if not isinstance(policies, list):
            continue
        
        # Find latest service_date across all policies
        latest_service_date = None
        latest_service_dt = None
        
        for policy in policies:
            if not isinstance(policy, dict):
                continue
            service_date = policy.get('service_date', '')
            if service_date:
                service_dt = _parse_date(service_date)
                if service_dt:
                    if latest_service_dt is None or service_dt > latest_service_dt:
                        latest_service_dt = service_dt
                        latest_service_date = service_date
        
        # If patient has no service_date at all, keep them (they're likely newly added or don't have dates)
        if latest_service_dt is None:
            # No service_date found - keep this patient
            continue
        
        # If latest service_date is older than cutoff, mark for removal
        if latest_service_dt < cutoff_date:
            patient_ids_to_remove.append(patient_id)
    
    # Remove stale patients
    for patient_id in patient_ids_to_remove:
        try:
            del by_pid[patient_id]
            removed_count += 1
        except Exception:
            pass
    
    return removed_count


def _migrate_v1_to_v2(v1_cache):
    """
    Migrate v1 cache structure to v2 format.
    Converts single entry per patient to policies array.
    Discards by_dob_member data (never used for lookups).
    """
    try:
        v2_cache = {
            "version": 2,
            "lastUpdated": v1_cache.get('lastUpdated', _now_iso_utc()),
            "by_patient_id": {}
        }
        
        by_pid_v1 = v1_cache.get('by_patient_id', {})
        if not isinstance(by_pid_v1, dict):
            return v2_cache
        
        for patient_id, entry in by_pid_v1.items():
            if not isinstance(entry, dict):
                continue
            
            # Convert single entry to policies array
            policy = {
                'code': _normalize_str(entry.get('code', '')),
                'payer_id': _normalize_str(entry.get('payer_id', '')),
                'member_id': _normalize_str(entry.get('member_id', '')),
                'dob': _normalize_str(entry.get('dob', '')),
                'remaining_amount': _normalize_str(entry.get('remaining_amount', '')),
                'plan_start_date': '',  # Unknown from v1
                'plan_end_date': '',    # Unknown from v1
                'service_date': '',     # Unknown from v1
                'cached_at': v1_cache.get('lastUpdated', _now_iso_utc())
            }
            
            # Only add if code is present and valid (filter out descriptions during migration)
            if policy['code'] and _is_valid_insurance_code(policy['code']):
                v2_cache['by_patient_id'][patient_id] = {
                    'policies': [policy]
                }
            else:
                # Log invalid codes being filtered out during migration
                if policy['code']:
                    _log("Migration: filtering out invalid code '{}' for patient_id='{}'".format(
                        policy['code'][:50], patient_id), level="INFO")
        
        return v2_cache
    except Exception as e:
        _log("Migration error: {}".format(str(e)), level="WARNING")
        return _empty_cache()


# Import shared validation utility
try:
    from MediCafe.deductible_utils import is_valid_insurance_code as _is_valid_insurance_code
except ImportError:
    # Fallback if import fails
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


def put_entry(csv_dir, patient_id, dob, member_id, payer_id, code, 
              remaining_amount=None, service_date=None, 
              plan_start_date=None, plan_end_date=None):
    """
    Low-level function to insert or update an entry in the cache. Supports multiple policies per patient with service date matching.
    - patient_id: PATID (5-digit patient ID from CSV "Patient ID #2") - used for lookups
    - dob/member_id: stored for reference
    - payer_id: retained to aid debugging and potential future logic; avoid logging
    - code: insurance type code as provided by API (must be valid short code, 1-3 alphanumeric)
    - remaining_amount: deductible remaining amount to persist (optional)
    - service_date: Service date in YYYY-MM-DD format (optional, but recommended for correct policy matching)
    - plan_start_date: Plan start date in YYYY-MM-DD format (optional, from API response)
    - plan_end_date: Plan end date in YYYY-MM-DD format (optional, from API response)
    """
    try:
        code_norm = _normalize_str(code)
        if not code_norm:
            _log("Cache put_entry SKIP: empty code for patient_id='{}'".format(_normalize_str(patient_id)), level="WARNING")
            return
        
        # Validate code is a valid short code (not a description)
        if not _is_valid_insurance_code(code_norm):
            _log("Cache put_entry REJECTED: invalid code '{}' for patient_id='{}' (length={}, is_alnum={}). Not caching.".format(
                code_norm[:50], _normalize_str(patient_id), len(code_norm), code_norm.isalnum()), level="WARNING")
            return
        
        # Log validation passed
        _log("Cache put_entry: code '{}' passed validation for patient_id='{}'".format(
            code_norm, _normalize_str(patient_id)), level="DEBUG")
        
        cache_dict = load_cache(csv_dir)
        pid_norm = _normalize_str(patient_id)
        
        if not pid_norm:
            _log("Cache put_entry SKIP: empty patient_id", level="DEBUG")
            return
        
        # Ensure patient entry exists with policies array
        by_pid = cache_dict.setdefault('by_patient_id', {})
        patient_entry = by_pid.setdefault(pid_norm, {'policies': []})
        if 'policies' not in patient_entry or not isinstance(patient_entry['policies'], list):
            patient_entry['policies'] = []
        
        # Log before adding policy
        _log("Cache put_entry: before adding policy, cache has {} patients, patient '{}' has {} policies".format(
            len(by_pid), pid_norm, len(patient_entry.get('policies', []))), level="DEBUG")
        
        policies = patient_entry['policies']
        
        # Create new policy entry
        new_policy = {
            'code': code_norm,
            'payer_id': _normalize_str(payer_id),
            'member_id': _normalize_str(member_id),
            'dob': _normalize_str(dob),
            'remaining_amount': _normalize_str(remaining_amount) if remaining_amount else '',
            'plan_start_date': _normalize_str(plan_start_date) if plan_start_date else '',
            'plan_end_date': _normalize_str(plan_end_date) if plan_end_date else '',
            'service_date': _normalize_str(service_date) if service_date else '',
            'cached_at': _now_iso_utc()
        }
        
        # If service_date provided, check if policy with matching date range exists
        if service_date:
            existing_policy = _find_policy_by_service_date(policies, service_date)
            if existing_policy:
                # Update existing policy
                existing_policy.update(new_policy)
                _log("Cache put_entry UPDATED: patient_id='{}', code='{}', service_date='{}'".format(
                    pid_norm, code_norm, service_date), level="DEBUG")
            else:
                # Append new policy
                policies.append(new_policy)
                _log("Cache put_entry ADDED: patient_id='{}', code='{}', service_date='{}'".format(
                    pid_norm, code_norm, service_date), level="DEBUG")
        else:
            # No service_date provided, append new policy
            policies.append(new_policy)
            _log("Cache put_entry ADDED: patient_id='{}', code='{}' (no service_date), now has {} policies".format(
                pid_norm, code_norm, len(policies)), level="DEBUG")
        
        # Limit policies array size (max 10 per patient, remove oldest by cached_at)
        if len(policies) > 10:
            # Sort by cached_at (oldest first) and keep only last 10
            # Policies without cached_at go to the front (oldest)
            try:
                policies.sort(key=lambda p: p.get('cached_at', '') or '0000-00-00T00:00:00Z')
                patient_entry['policies'] = policies[-10:]
            except Exception:
                # If sorting fails, just keep last 10
                patient_entry['policies'] = policies[-10:]
        
        # Log after adding policy but before cleanup
        _log("Cache put_entry: after adding policy, cache has {} patients, patient '{}' has {} policies".format(
            len(by_pid), pid_norm, len(patient_entry.get('policies', []))), level="DEBUG")
        
        # Verify the patient is actually in cache_dict
        verify_by_pid = cache_dict.get('by_patient_id', {})
        verify_patient = verify_by_pid.get(pid_norm)
        _log("Cache put_entry: verification - cache_dict has {} patients, patient '{}' exists: {}, has {} policies".format(
            len(verify_by_pid), pid_norm, verify_patient is not None, 
            len(verify_patient.get('policies', [])) if verify_patient else 0), level="DEBUG")
        
        # Run cleanup before save
        try:
            removed_count = _cleanup_stale_patients(cache_dict, max_age_days=720)
            if removed_count > 0:
                _log("Cache put_entry: cleanup removed {} stale patients".format(removed_count), level="INFO")
        except Exception as e:
            _log("Cache put_entry: cleanup error: {}".format(str(e)), level="WARNING")
        
        # Log before saving to confirm we reach this point
        final_by_pid = cache_dict.get('by_patient_id', {})
        _log("Cache put_entry: about to save cache with {} patients (patient '{}' exists: {})".format(
            len(final_by_pid), pid_norm, pid_norm in final_by_pid), level="DEBUG")
        
        save_cache(csv_dir, cache_dict)
        
        # Log after save attempt
        _log("Cache put_entry: save_cache call completed", level="DEBUG")
        
    except Exception as e:
        _log("Cache put_entry ERROR: {}".format(str(e)), level="WARNING")


def _map_api_insurance_type_code(api_code):
    """
    Temporary hardcoded mapping to convert API response insurance type codes
    to SBR segment-compatible codes.
    
    This mapping is applied upstream after receiving the code from the API endpoint
    so that everything downstream treats it as API-sourced.
    
    Args:
        api_code: Insurance type code from API response
        
    Returns:
        Mapped code for SBR segment construction, or original code if no mapping exists
    """
    if not api_code:
        return api_code
    
    # Temporary hardcoded mapping: API code -> SBR code
    # Add mappings as needed when API returns codes that don't match SBR segment requirements
    API_TO_SBR_MAPPING = {
        'C1': 'CI',  # Commercial Insurance Co.
        'HN': '16',  # Health Maintenance Organization (HMO) Medicare Risk
        'MP': '16',  # Health Maintenance Organization (HMO) Medicare Risk
        'PR': '12',  # Preferred Provider Organization (PPO)
    }
    
    mapped_code = API_TO_SBR_MAPPING.get(api_code)
    if mapped_code:
        try:
            _log("API insurance type code mapping: '{}' -> '{}'".format(api_code, mapped_code), level="INFO")
        except (OSError, IOError):
            # Windows logging stream flush can fail with OSError [Errno 22] - ignore silently
            pass
        return mapped_code
    return api_code  # Return original if no mapping exists


def put_entry_from_enhanced_result(csv_dir, enhanced_result, dob, member_id, payer_id, 
                                    csv_row=None, service_date_for_api=None, context="batch"):
    """
    High-level function to write eligibility data to cache from an enhanced result dict.
    Handles all data extraction internally.
    
    Args:
        csv_dir: Directory containing the cache file
        enhanced_result: Enhanced eligibility result dict (from merge_responses or convert_eligibility_to_enhanced_format)
        dob: Date of birth
        member_id: Member ID
        payer_id: Payer ID
        csv_row: Optional CSV row data for patient_id extraction
        service_date_for_api: Optional service date (datetime object or string in YYYY-MM-DD format)
        context: Context string for logging ("batch" or "manual")
    
    Returns:
        bool: True if cache write was attempted, False otherwise
    """
    try:
        # Extract insurance code from API response
        raw_api_code = _normalize_str(enhanced_result.get('insurance_type', ''))
        # Apply mapping to convert API code to SBR-compatible code
        code_to_persist = _map_api_insurance_type_code(raw_api_code) if raw_api_code else ''
        if not code_to_persist:
            _log("{} cache SKIP: empty code for member_id='{}'".format(context.title(), member_id), level="INFO")
            return False
        
        # Extract remaining amount
        remaining_amount_to_persist = _normalize_str(enhanced_result.get('remaining_amount', ''))
        if remaining_amount_to_persist == 'Not Found':
            remaining_amount_to_persist = ''
        
        # Extract patient_id from enhanced_result first, then CSV row if needed
        pid_for_cache = _normalize_str(enhanced_result.get('patient_id', ''))
        if not pid_for_cache and csv_row:
            try:
                # Try common patient ID field names
                pid_for_cache = _normalize_str(csv_row.get('Patient ID #2', csv_row.get('Patient ID', '')))
            except Exception:
                pid_for_cache = ''
        
        # Log cache attempt details
        _log("{} cache check: patient_id='{}', code='{}', remaining='{}', member_id='{}'".format(
            context.title(), pid_for_cache or '(empty)', code_to_persist or '(empty)', 
            remaining_amount_to_persist or '(empty)', member_id), level="DEBUG")
        
        # Only cache if we have a valid patient_id and insurance code
        if not pid_for_cache:
            try:
                _log("{} cache SKIP: empty patient_id for member_id='{}'".format(
                    context.title(), member_id), level="INFO")
            except (OSError, IOError):
                # Windows logging stream flush can fail with OSError [Errno 22] - ignore silently
                pass
            return False
        
        if not code_to_persist:
            _log("{} cache SKIP: empty code='{}' for patient_id='{}'".format(
                context.title(), code_to_persist or '(empty)', pid_for_cache or '(empty)'), level="INFO")
            return False
        
        # Extract service_date for cache
        service_date_for_cache = None
        if service_date_for_api:
            try:
                # Handle datetime objects (datetime already imported at module level)
                if isinstance(service_date_for_api, datetime):
                    service_date_for_cache = service_date_for_api.strftime('%Y-%m-%d')
                    _log("{} cache: extracted service_date from datetime: '{}'".format(
                        context.title(), service_date_for_cache), level="DEBUG")
                else:
                    # Assume string in YYYY-MM-DD format or try to parse
                    service_date_str = str(service_date_for_api).strip()
                    if service_date_str:
                        # Try to parse if not already in YYYY-MM-DD format
                        try:
                            parsed = datetime.strptime(service_date_str, '%Y-%m-%d')
                            service_date_for_cache = parsed.strftime('%Y-%m-%d')
                            _log("{} cache: extracted service_date from string (YYYY-MM-DD): '{}'".format(
                                context.title(), service_date_for_cache), level="DEBUG")
                        except ValueError:
                            # Try other common formats
                            for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y']:
                                try:
                                    parsed = datetime.strptime(service_date_str, fmt)
                                    service_date_for_cache = parsed.strftime('%Y-%m-%d')
                                    _log("{} cache: extracted service_date from string ({}): '{}'".format(
                                        context.title(), fmt, service_date_for_cache), level="DEBUG")
                                    break
                                except ValueError:
                                    continue
                            if not service_date_for_cache:
                                service_date_for_cache = service_date_str  # Use as-is if parsing fails
                                _log("{} cache: using service_date as-is (unparsed): '{}'".format(
                                    context.title(), service_date_for_cache), level="DEBUG")
            except Exception as e:
                _log("{} cache: error extracting service_date from service_date_for_api: {}".format(
                    context.title(), str(e)), level="WARNING")
        elif csv_row:
            # Try to extract from CSV row using common field names
            try:
                service_date_str = _normalize_str(csv_row.get('Service Date', ''))
                if not service_date_str:
                    service_date_str = _normalize_str(csv_row.get('Surgery Date', ''))
                if not service_date_str:
                    service_date_str = _normalize_str(csv_row.get('Date of Service', ''))
                if service_date_str:
                    # Try to parse to ensure YYYY-MM-DD format (datetime already imported at module level)
                    try:
                        parsed = datetime.strptime(service_date_str, '%Y-%m-%d')
                        service_date_for_cache = parsed.strftime('%Y-%m-%d')
                        _log("{} cache: extracted service_date from CSV row (YYYY-MM-DD): '{}'".format(
                            context.title(), service_date_for_cache), level="DEBUG")
                    except ValueError:
                        # Try other formats
                        for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%m-%d-%y', '%m/%d/%y']:
                            try:
                                parsed = datetime.strptime(service_date_str, fmt)
                                service_date_for_cache = parsed.strftime('%Y-%m-%d')
                                _log("{} cache: extracted service_date from CSV row ({}): '{}'".format(
                                    context.title(), fmt, service_date_for_cache), level="DEBUG")
                                break
                            except ValueError:
                                continue
                        if not service_date_for_cache:
                            service_date_for_cache = service_date_str  # Use as-is if parsing fails
                            _log("{} cache: using service_date from CSV as-is (unparsed): '{}'".format(
                                context.title(), service_date_for_cache), level="DEBUG")
            except Exception as e:
                _log("{} cache: error extracting service_date from CSV row: {}".format(
                    context.title(), str(e)), level="WARNING")
        
        if not service_date_for_cache:
            _log("{} cache: WARNING - no service_date extracted (service_date_for_api={}, csv_row={})".format(
                context.title(), service_date_for_api, 'present' if csv_row else 'None'), level="WARNING")
        
        # Extract plan dates from enhanced_result if available from API
        # merge_responses normalizes these to None if missing, so safe to get directly
        plan_start_date = None
        plan_end_date = None
        try:
            plan_start_date = enhanced_result.get('plan_start_date')
            plan_end_date = enhanced_result.get('plan_end_date')
            # Log plan dates for debugging
            if plan_start_date or plan_end_date:
                _log("{} cache: extracted plan dates - start='{}', end='{}'".format(
                    context.title(), plan_start_date or '(none)', plan_end_date or '(none)'), level="DEBUG")
            else:
                _log("{} cache: no plan dates found in enhanced_result".format(context.title()), level="DEBUG")
            # Keep as None if missing (don't convert to empty string yet - let put_entry handle it)
        except Exception as e:
            _log("{} cache: error extracting plan dates: {}".format(context.title(), str(e)), level="WARNING")
            plan_start_date = None
            plan_end_date = None
        
        # Log cache write attempt
        _log("{} cache WRITE: patient_id='{}', code='{}', remaining='{}', service_date='{}'".format(
            context.title(), pid_for_cache, code_to_persist, remaining_amount_to_persist or '(empty)',
            service_date_for_cache or '(none)'), level="DEBUG")
        
        # Log csv_dir being used for debugging
        _log("{} cache: using csv_dir='{}'".format(context.title(), csv_dir or '(empty)'), level="DEBUG")
        
        # Call low-level put_entry with extracted values
        put_entry(csv_dir, pid_for_cache, dob, member_id, payer_id, code_to_persist,
                 remaining_amount=remaining_amount_to_persist if remaining_amount_to_persist else None,
                 service_date=service_date_for_cache,
                 plan_start_date=plan_start_date if plan_start_date else None,
                 plan_end_date=plan_end_date if plan_end_date else None)
        return True
        
    except Exception as e:
        # Log exception for debugging
        _log("{} cache ERROR: {}".format(context.title(), str(e)), level="WARNING")
        return False


def lookup(patient_id=None, csv_dir=None, return_full=False, service_date=None):
    """
    Lookup insurance type code by PATID (patient_id).
    PATID is the 5-digit patient ID from fixed-width files that matches CSV "Patient ID #2".
    This is the reliable matching strategy.
    
    Args:
        patient_id: PATID (5-digit patient ID) to look up
        csv_dir: Directory containing the cache file
        return_full: When True, return dict with available fields (e.g., code, remaining_amount).
                     When False (default), return just the insurance type code string for backward compatibility.
        service_date: Optional service date in YYYY-MM-DD format. If provided, matches policy by date range.
                     If not provided, returns most recent policy.
    
    Returns:
        - If return_full is False: The insurance type code string or None if not found.
        - If return_full is True: A dict with keys like {'code': str, 'remaining_amount': str} or None if not found.
    """
    try:
        # Log individual lookup at DEBUG level to avoid log flooding
        _log("Cache lookup: patient_id='{}', csv_dir='{}', service_date='{}'".format(
            patient_id, csv_dir, service_date or 'none'), level="DEBUG")
        
        # Use in-memory cache to avoid reloading from disk repeatedly
        cache_key = csv_dir or ''
        cache_path = get_cache_path(csv_dir)
        
        # Check if we have a cached version and if file hasn't changed
        if cache_key in _cache_memory:
            cached_data, cached_mtime = _cache_memory[cache_key]
            # Check if file modification time has changed (optional optimization)
            try:
                if cache_path and os.path.exists(cache_path):
                    current_mtime = os.path.getmtime(cache_path)
                    if current_mtime == cached_mtime:
                        # Cache is still valid, use it
                        cache_dict = cached_data
                    else:
                        # File changed, reload
                        cache_dict = load_cache(csv_dir)
                        _cache_memory[cache_key] = (cache_dict, current_mtime)
                else:
                    # File doesn't exist, use cached empty cache
                    cache_dict = cached_data
            except Exception:
                # On error, reload from disk
                cache_dict = load_cache(csv_dir)
                try:
                    mtime = os.path.getmtime(cache_path) if cache_path and os.path.exists(cache_path) else 0
                    _cache_memory[cache_key] = (cache_dict, mtime)
                except Exception:
                    _cache_memory[cache_key] = (cache_dict, 0)
        else:
            # First time loading for this csv_dir
            cache_dict = load_cache(csv_dir)
            try:
                mtime = os.path.getmtime(cache_path) if cache_path and os.path.exists(cache_path) else 0
                _cache_memory[cache_key] = (cache_dict, mtime)
            except Exception:
                _cache_memory[cache_key] = (cache_dict, 0)
        # Only log cache patient count at DEBUG to avoid repetition
        patient_count = len(cache_dict.get('by_patient_id', {}))
        _log("Cache contains {} patients".format(patient_count), level="DEBUG")
        
        # PATID match (normalized) - this is the reliable matching strategy
        pid = _normalize_str(patient_id)
        if not pid:
            _log("Cache lookup skipped: patient_id is empty", level="INFO")
            return None
        
        # pid is guaranteed to be non-empty here
        try:
            by_pid = cache_dict.get('by_patient_id', {})
            # Log available keys for debugging (first 5 only)
            if by_pid:
                sample_keys = list(by_pid.keys())[:5]
                _log("Cache lookup by PATID: searching for '{}', sample keys in cache: {}".format(
                    pid, sample_keys), level="DEBUG")
            
            patient_entry = by_pid.get(pid)
            if not patient_entry or not isinstance(patient_entry, dict):
                _log("Cache lookup MISS: patient_id '{}' not found in cache".format(pid), level="DEBUG")
                return None
            
            policies = patient_entry.get('policies', [])
            if not isinstance(policies, list) or not policies:
                _log("Cache lookup MISS: patient_id '{}' found but no policies".format(pid), level="DEBUG")
                return None
            
            # Select policy based on service_date
            selected_policy = None
            if service_date:
                selected_policy = _find_policy_by_service_date(policies, service_date)
                if selected_policy:
                    _log("Cache lookup FOUND by PATID '{}' with service_date '{}'".format(pid, service_date), level="DEBUG")
                else:
                    _log("Cache lookup: no policy found for PATID '{}' with service_date '{}', trying most recent".format(
                        pid, service_date), level="DEBUG")
            
            # Fallback to most recent if service_date match not found or service_date not provided
            if not selected_policy:
                selected_policy = _find_most_recent_policy(policies)
                if selected_policy:
                    _log("Cache lookup FOUND by PATID '{}' (most recent policy)".format(pid), level="DEBUG")
            
            if not selected_policy:
                _log("Cache lookup MISS by PATID '{}': no valid policy found".format(pid), level="DEBUG")
                return None
            
            code = _normalize_str(selected_policy.get('code'))
            if not code:
                _log("Cache lookup MISS by PATID '{}': policy found but no code".format(pid), level="DEBUG")
                return None
            
            if return_full:
                result = {'code': code}
                ra = _normalize_str(selected_policy.get('remaining_amount'))
                if ra:
                    result['remaining_amount'] = ra
                # Include plan dates for policy status determination
                plan_start = _normalize_str(selected_policy.get('plan_start_date'))
                plan_end = _normalize_str(selected_policy.get('plan_end_date'))
                if plan_start:
                    result['plan_start_date'] = plan_start
                if plan_end:
                    result['plan_end_date'] = plan_end
                # Include other fields that might be useful
                payer_id = _normalize_str(selected_policy.get('payer_id'))
                if payer_id:
                    result['payer_id'] = payer_id
                # Include cached_at for recent cache checking (critical for cache freshness logic)
                cached_at = selected_policy.get('cached_at')
                if cached_at:
                    result['cached_at'] = cached_at
                _log("Cache lookup FOUND by PATID '{}' (full)".format(pid), level="DEBUG")
                return result
            else:
                _log("Cache lookup SUCCESS: patient_id '{}', code='{}'".format(pid, code), level="DEBUG")
                return code
                
        except Exception as e:
            _log("Cache lookup exception (PATID): {}".format(str(e)), level="WARNING")
    except Exception as e:
        _log("Cache lookup error: {}".format(str(e)), level="WARNING")
    return None


