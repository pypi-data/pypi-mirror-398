#!/usr/bin/env python3
"""
build_deductible_cache.py

Silent helper that runs MediLink_Deductible_v1_5 during CSV intake so that the
insurance_type_cache.json gets populated without requiring any additional user
interaction. Designed to be invoked from process_csvs.py immediately after a
fresh CSV is moved into place (Email de Carol flow).
"""

from __future__ import print_function

import argparse
import io
import os
import sys
import traceback

# Ensure workspace root is on sys.path (only add once to prevent duplicates)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(CURRENT_DIR)
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


def _safe_print(message):
    """Print message safely, handling encoding errors on Windows."""
    try:
        # Convert message to string
        msg_str = str(message) if message else ""
        
        # Sanitize message to ASCII-safe characters to avoid charmap errors
        try:
            msg_ascii = msg_str.encode('ascii', errors='replace').decode('ascii')
        except Exception:
            # If encoding fails, use empty string
            msg_ascii = ""
        
        # Try writing to stdout buffer directly (most reliable on Windows)
        try:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout.buffer.write(msg_ascii.encode('ascii', errors='replace'))
                sys.stdout.buffer.write(b'\n')
                sys.stdout.flush()
                return
        except Exception:
            pass
        
        # Fallback to regular print with ASCII-safe string
        try:
            print(msg_ascii)
        except Exception:
            # If print fails, silently skip to avoid cascading errors
            pass
    except Exception:
        # If anything goes wrong, silently skip to avoid cascading errors
        pass


from MediCafe.core_utils import get_shared_config_loader  # noqa: E402

# Import error reporting functions (with graceful fallback)
try:
    from MediCafe.error_reporter import capture_unhandled_traceback, collect_support_bundle, submit_support_bundle_email  # noqa: E402
except Exception:
    capture_unhandled_traceback = None
    collect_support_bundle = None
    submit_support_bundle_email = None

try:
    from MediLink.MediLink_Deductible_v1_5 import run_batch_from_csv  # noqa: E402
except Exception as import_err:  # pragma: no cover - guard rails for XP envs
    _safe_print("Deductible cache builder: cannot import v1.5 module: {}".format(import_err))
    # Note: Error reporting not available at import time, so we can't submit error report
    # This is acceptable since import failures are usually configuration/environment issues
    sys.exit(1)

# Import check_internet_connection with graceful fallback (consistent with other imports)
try:
    from MediCafe.core_utils import check_internet_connection  # noqa: E402
except ImportError as e:
    # Log warning but don't fail - connectivity check will be skipped if function unavailable
    _safe_print("Warning: Cannot import check_internet_connection from MediCafe.core_utils. Connectivity checks will be skipped. Original error: {}".format(e))
    # Define a fallback function that always returns True (assume online)
    def check_internet_connection():
        return True


# Initialize logger with error handling (don't fail if unavailable)
try:
    LOGGER = get_shared_config_loader()
except Exception:
    LOGGER = None  # Will fall back to safe_print in _log()


def _safe_print_traceback():
    """Print traceback safely, handling encoding errors on Windows."""
    try:
        # Capture traceback to string with safe encoding
        # Use try/finally for Python 3.4 compatibility (context manager not always available)
        tb_str = None
        try:
            tb_str = io.StringIO()
            traceback.print_exc(file=tb_str)
            tb_content = tb_str.getvalue()
            _safe_print(tb_content)
        except Exception:
            # If StringIO fails, try direct print with error handling
            try:
                traceback.print_exc()
            except (UnicodeEncodeError, UnicodeDecodeError):
                # Encoding error in traceback - print a safe message instead
                _safe_print("Traceback (encoding error - details unavailable)")
            except Exception:
                pass
        finally:
            # Ensure StringIO is closed even if getvalue() or _safe_print fails
            if tb_str is not None:
                try:
                    tb_str.close()
                except Exception:
                    pass
    except Exception:
        # If all else fails, print a safe error message
        try:
            _safe_print("Error occurred (traceback unavailable)")
        except Exception:
            pass


def _log(message, level="INFO"):
    """Best-effort logging via shared config loader, falling back to safe print."""
    try:
        if LOGGER and hasattr(LOGGER, "log"):
            LOGGER.log(message, level=level)
            return
    except (OSError, IOError):
        # Windows logging stream flush can fail with OSError [Errno 22] - ignore silently
        pass
    except Exception:
        pass
    try:
        _safe_print(message)
    except Exception:
        pass


def _clear_cached_configuration():
    """Ensure subsequent loads read the freshly updated config file."""
    try:
        from MediCafe import MediLink_ConfigLoader
        clear_func = getattr(MediLink_ConfigLoader, "clear_config_cache", None)
        if callable(clear_func):
            clear_func()
    except Exception:
        pass


def _load_config():
    """Load the latest configuration dictionary (after clearing cache)."""
    config = {}
    try:
        if LOGGER and hasattr(LOGGER, "load_configuration"):
            _clear_cached_configuration()
            config_result = LOGGER.load_configuration()
            # Defensively handle different return types
            if isinstance(config_result, tuple) and len(config_result) >= 1:
                loaded_config = config_result[0]  # First element is config dict
                # Second element (crosswalk) is ignored, which is expected
            elif isinstance(config_result, dict):
                # Some implementations might return just the config dict
                loaded_config = config_result
            else:
                _log("Deductible cache builder: config loader returned unexpected type ({})".format(type(config_result).__name__), level="WARNING")
                loaded_config = None
            
            # Ensure we return a dict (handle case where load_configuration returns None or non-dict)
            if isinstance(loaded_config, dict):
                config = loaded_config
            elif loaded_config is not None:
                _log("Deductible cache builder: config loader returned non-dict type ({})".format(type(loaded_config).__name__), level="WARNING")
    except (KeyboardInterrupt, SystemExit):
        # Allow system exceptions to propagate
        raise
    except (ValueError, TypeError) as unpack_err:
        # Handle tuple unpacking errors or type errors
        _log("Deductible cache builder: failed to unpack config result ({})".format(unpack_err), level="WARNING")
        config = {}
    except Exception as exc:
        _log("Deductible cache builder: failed to load config ({})".format(exc), level="WARNING")
        config = {}
    # Return empty dict if config is falsy or not a dict
    if not isinstance(config, dict):
        return {}
    return config


def _has_internet():
    """Return True when internet connectivity is available (best effort)."""
    try:
        return bool(check_internet_connection())
    except Exception as exc:
        _log("Deductible cache builder: connectivity check failed ({}) - continuing as online.".format(exc), level="WARNING")
        return True


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Silent helper that builds the insurance type cache using MediLink_Deductible_v1_5."
    )
    parser.add_argument(
        "--skip-internet-check",
        action="store_true",
        help="Run even when connectivity check fails."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print a short summary to stdout even when logger is available."
    )
    return parser.parse_args()


def _submit_error_report(error_message=None):
    """Collect and submit error report for failures in build_deductible_cache.
    
    Args:
        error_message: Optional error message string for logging context.
                      Currently not included in bundle (bundle uses traceback.txt).
    
    Returns:
        bool: True if report submitted successfully, False otherwise
    """
    try:
        if collect_support_bundle is None or submit_support_bundle_email is None:
            _log("Error reporting not available - check MediCafe installation.", level="WARNING")
            return False
        
        # Log the error message if provided (for context, though bundle uses traceback.txt)
        if error_message:
            _log("Error context: {}".format(error_message), level="ERROR")
        
        _log("Collecting error report for deductible cache builder failure", level="INFO")
        zip_path = collect_support_bundle(include_traceback=True)
        if not zip_path:
            _log("Failed to create error report bundle", level="WARNING")
            return False
        
        # Validate zip_path is a valid string before using it
        if not isinstance(zip_path, str) or not zip_path:
            _log("Error report bundle path is invalid", level="WARNING")
            return False
        
        # Check internet connectivity
        try:
            online = bool(check_internet_connection())
        except Exception:
            online = True  # Assume online if check fails
        
        if online:
            success = submit_support_bundle_email(zip_path)
            if success:
                try:
                    os.remove(zip_path)
                    _log("Error report submitted successfully", level="INFO")
                except Exception:
                    pass  # Non-critical - bundle was sent
                return True
            else:
                _log("Error report send failed - bundle preserved at {} for retry".format(zip_path), level="WARNING")
                return False
        else:
            _log("Offline - error bundle queued at {} for retry when online".format(zip_path), level="INFO")
            return False
    except (KeyboardInterrupt, SystemExit):
        # Allow system exceptions to propagate
        raise
    except Exception as report_exc:
        _log("Error report collection failed: {}".format(str(report_exc)), level="WARNING")
        return False


def build_deductible_cache(config=None, verbose=False, skip_internet_check=False, submit_error_report=True):
    """
    Build deductible cache from CSV configuration.
    
    This function can be called directly from Python code (with existing exception handling)
    or via main() when run as a standalone script.
    
    Args:
        config: Optional config dict. If None, loads from config loader. Must be dict-like if provided.
        verbose: If True, print summary to stdout.
        skip_internet_check: If True, skip internet connectivity check.
        submit_error_report: If True, submit error report on failure. Set False when caller handles reporting.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    if not skip_internet_check and not _has_internet():
        _log("Deductible cache builder: skipped (offline).", level="INFO")
        return 0

    if config is None:
        config = _load_config()
    
    # Validate config is dict-like
    if not isinstance(config, dict):
        _log("Deductible cache builder: invalid config type (expected dict, got {}); skipping cache build.".format(type(config).__name__), level="ERROR")
        return 1
    
    csv_path = ""
    try:
        csv_path = config.get("CSV_FILE_PATH", "")
        # Ensure csv_path is a string
        if csv_path is not None:
            csv_path = str(csv_path).strip()
        else:
            csv_path = ""
    except Exception as exc:
        _log("Deductible cache builder: error extracting CSV path from config ({})".format(exc), level="WARNING")
        csv_path = ""

    if not csv_path:
        _log("Deductible cache builder: no CSV_FILE_PATH configured; nothing to do.", level="INFO")
        # Return 0 (success) since this is an expected/valid state (not an error condition)
        return 0

    # Validate path is a valid string before checking existence
    if not isinstance(csv_path, str) or not csv_path:
        _log("Deductible cache builder: invalid CSV_FILE_PATH value; skipping cache build.", level="WARNING")
        # Return 0 (success) - invalid path is handled gracefully
        return 0

    try:
        if not os.path.exists(csv_path):
            _log("Deductible cache builder: CSV not found at '{}'; skipping cache build.".format(csv_path), level="INFO")
            # Return 0 (success) - missing CSV is handled gracefully (may be expected in some workflows)
            return 0
    except (TypeError, OSError) as path_err:
        _log("Deductible cache builder: error checking CSV path '{}' ({})".format(csv_path, path_err), level="WARNING")
        # Return 0 (success) - path checking error is handled gracefully
        return 0

    _log("Deductible cache builder: starting silent batch against '{}'.".format(csv_path), level="INFO")

    try:
        results = run_batch_from_csv(config)
        # Defensively handle return value - should be list, but handle None and other types
        if results is None:
            _log("Deductible cache builder: batch function returned None (no results)", level="WARNING")
            processed_count = 0
        elif isinstance(results, (list, tuple)):
            processed_count = len(results)
        else:
            # Unexpected return type - log warning but treat as 0 processed
            _log("Deductible cache builder: batch function returned unexpected type ({})".format(type(results).__name__), level="WARNING")
            processed_count = 0
        
        summary = "Deductible cache builder: completed - {} patient(s) refreshed.".format(processed_count)
        _log(summary, level="INFO")
        if verbose:
            _safe_print(summary)
        return 0
    except (KeyboardInterrupt, SystemExit):
        # Allow system exceptions to propagate (don't mask user cancellation or system exits)
        raise
    except Exception as exc:  # pragma: no cover - protective logging for runtime failures
        # Sanitize exception message to prevent charmap errors when logging
        exc_str = str(exc)
        try:
            # Convert to ASCII-safe string
            exc_str_safe = exc_str.encode('ascii', errors='replace').decode('ascii')
        except Exception:
            exc_str_safe = "Error message encoding failed"
        _log("Deductible cache builder: failed with error: {}".format(exc_str_safe), level="ERROR")
        _safe_print_traceback()
        
        # Submit error report (non-blocking - don't fail if reporting fails)
        # Only submit if flag is True (default for standalone usage)
        # When called from Python code with existing exception handling, caller can set submit_error_report=False
        if submit_error_report:
            try:
                # Sanitize error message for error reporting (consistent with logging)
                _submit_error_report(error_message=exc_str_safe)
            except Exception:
                pass  # Don't let error reporting failure mask the original error
        
        return 1


def main():
    """Entry point when run as standalone script - parses args and calls build_deductible_cache()."""
    try:
        args = _parse_args()
        # Load config here to avoid double-loading in build_deductible_cache()
        config = _load_config()
        return build_deductible_cache(config=config, verbose=args.verbose, skip_internet_check=args.skip_internet_check, submit_error_report=True)
    except (KeyboardInterrupt, SystemExit):
        # Allow system exceptions to propagate
        raise
    except Exception as exc:
        # Catch-all for unexpected errors in main() itself
        _safe_print("Deductible cache builder: fatal error in main(): {}".format(exc))
        _safe_print_traceback()
        return 1


if __name__ == "__main__":
    # Install unhandled exception hook to capture tracebacks for uncaught exceptions
    try:
        if capture_unhandled_traceback is not None:
            sys.excepthook = capture_unhandled_traceback
    except Exception:
        pass
    
    sys.exit(main())
