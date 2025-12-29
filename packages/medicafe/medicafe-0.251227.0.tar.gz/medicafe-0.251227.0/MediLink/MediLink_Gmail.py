# MediLink_Gmail.py
import sys, os, subprocess, time, webbrowser, requests, json, ssl, signal, re
from collections import deque
from datetime import datetime

# Set up Python path to find MediCafe when running directly
def setup_python_path():
    """Set up Python path to find MediCafe package"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(current_dir)
    
    # Add workspace root to Python path if not already present
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)
    
    return workspace_root

# Set up paths before importing MediCafe
WORKSPACE_ROOT = setup_python_path()

from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config, check_internet_connection

# New helpers
from MediLink.gmail_oauth_utils import (
    get_authorization_url as oauth_get_authorization_url,
    exchange_code_for_token as oauth_exchange_code_for_token,
    refresh_access_token as oauth_refresh_access_token,
    is_valid_authorization_code as oauth_is_valid_authorization_code,
)
from MediLink.gmail_http_utils import (
    generate_self_signed_cert as http_generate_self_signed_cert,
    wrap_socket_for_server as http_wrap_socket_for_server,
    inspect_token as http_inspect_token,
    get_certificate_fingerprint as http_get_certificate_fingerprint,
    SSLRequestHandler,
)
try:
    from MediLink import certificate_authority
    CERTIFICATE_AUTHORITY_AVAILABLE = True
except ImportError:
    certificate_authority = None
    CERTIFICATE_AUTHORITY_AVAILABLE = False
try:
    from MediLink.firefox_cert_utils import diagnose_firefox_certificate_exceptions
    FIREFOX_CERT_DIAG_AVAILABLE = True
except ImportError:
    FIREFOX_CERT_DIAG_AVAILABLE = False
    def diagnose_firefox_certificate_exceptions(*args, **kwargs):
        return {'error': 'Firefox certificate diagnostics not available'}
from MediLink.gmail_html_utils import (
    build_cert_info_html as html_build_cert_info_html,
    build_root_status_html as html_build_root_status_html,
    build_diagnostics_html as html_build_diagnostics_html,
    build_troubleshoot_html as html_build_troubleshoot_html,
    build_simple_error_html as html_build_simple_error_html,
    build_fallback_status_html as html_build_fallback_status_html,
    build_fallback_cert_html as html_build_fallback_cert_html,
)

# Import connection diagnostics module
try:
    from MediLink.connection_diagnostics import (
        run_diagnostics as _run_diagnostics_base,
        get_firefox_xp_compatibility_notes,
        BROWSER_DIAGNOSTIC_HINTS,
        run_all_selftests as _run_all_selftests,
        detect_available_tls_versions,
        is_windows_xp as detect_is_windows_xp,
    )
    DIAGNOSTICS_AVAILABLE = True
except ImportError as diag_import_err:
    DIAGNOSTICS_AVAILABLE = False
    _run_diagnostics_base = None
    _run_all_selftests = None
    def get_firefox_xp_compatibility_notes():
        return {'notes': []}
    BROWSER_DIAGNOSTIC_HINTS = {}
    def detect_available_tls_versions():
        # Fallback: detect TLS versions without diagnostics module
        import ssl as _ssl
        _tls = []
        for _name, _attr in [('TLSv1', 'PROTOCOL_TLSv1'), ('TLSv1.1', 'PROTOCOL_TLSv1_1'), 
                             ('TLSv1.2', 'PROTOCOL_TLSv1_2'), ('TLSv1.3', 'PROTOCOL_TLSv1_3')]:
            if hasattr(_ssl, _attr):
                _tls.append(_name)
        return _tls
    def detect_is_windows_xp(os_name=None, os_version=None):
        # Fallback: detect XP without diagnostics module
        import platform as _platform
        _os = os_name if os_name is not None else _platform.system()
        _ver = os_version if os_version is not None else _platform.release()
        return _os == 'Windows' and _ver.startswith('5.')
from MediCafe.gmail_token_service import (
    get_gmail_access_token as shared_get_gmail_access_token,
    resolve_credentials_path as shared_resolve_credentials_path,
    resolve_token_path as shared_resolve_token_path,
    clear_gmail_token_cache as shared_clear_token_cache,
    save_gmail_token as shared_save_gmail_token,
)

# Get shared config loader
MediLink_ConfigLoader = get_shared_config_loader()
if MediLink_ConfigLoader:
    load_configuration = MediLink_ConfigLoader.load_configuration
    log = MediLink_ConfigLoader.log
else:
    # Fallback functions if config loader is not available
    def load_configuration():
        return {}, {}
    def log(message, level="INFO"):
        print("[{}] {}".format(level, message))

try:
    from MediCafe.error_reporter import (
        capture_unhandled_traceback as _capture_unhandled_traceback,
        submit_support_bundle_email as _submit_support_bundle_email,
    )
    sys.excepthook = _capture_unhandled_traceback  # Ensure unhandled exceptions hit MediCafe reporter
    log("MediCafe error reporter registered for Gmail flow exceptions.", level="DEBUG")
except Exception as error_reporter_exc:
    _submit_support_bundle_email = None
    # Keep server running even if error reporter is unavailable
    try:
        log("Unable to register MediCafe error reporter: {}".format(error_reporter_exc), level="DEBUG")
    except Exception:
        pass
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread, Event
import platform
import ctypes

# Default configuration values
DEFAULT_SERVER_PORT = 8000
DEFAULT_CERT_DAYS = 365
LOSS_ALERT_SECONDS = 60  # Increased for debugging
CONNECTION_WATCHDOG_INTERVAL = 5
AUTO_SHUTDOWN_SECONDS = 600  # 10 minutes for debugging

def resolve_openssl_cnf(base_dir):
    """Find openssl.cnf file, searching local dir then fallback path. Returns best-effort path."""
    # Try relative path first
    openssl_cnf = 'openssl.cnf'
    if os.path.exists(openssl_cnf):
        log("Found openssl.cnf at: {}".format(os.path.abspath(openssl_cnf)), level="DEBUG")
        return openssl_cnf

    # Try base directory
    medilink_openssl = os.path.join(base_dir, 'openssl.cnf')
    if os.path.exists(medilink_openssl):
        log("Found openssl.cnf at: {}".format(medilink_openssl), level="DEBUG")
        return medilink_openssl

    # Try fallback path (one directory up)
    parent_dir = os.path.dirname(base_dir)
    alternative_path = os.path.join(parent_dir, 'MediBot', 'openssl.cnf')
    if os.path.exists(alternative_path):
        log("Found openssl.cnf at: {}".format(alternative_path), level="DEBUG")
        return alternative_path

    # Return relative path as fallback (may not exist)
    log("Could not find openssl.cnf - using fallback path", level="DEBUG")
    return openssl_cnf


# Lazy resolution cache for openssl.cnf - only resolved when actually needed
_openssl_cnf_cache = None

def get_openssl_cnf():
    """Lazy resolution of openssl.cnf - only resolved when actually needed (e.g., HTTPS server startup).
    
    This avoids running the resolution when scripts only import add_downloaded_email
    from this module, which was causing duplicate openssl.cnf checks in logs.
    """
    global _openssl_cnf_cache
    if _openssl_cnf_cache is None:
        medilink_dir = os.path.dirname(os.path.abspath(__file__))
        _openssl_cnf_cache = resolve_openssl_cnf(medilink_dir)
    return _openssl_cnf_cache


config, _ = load_configuration()
medi = extract_medilink_config(config)

# HTTP Mode Configuration Flag
# Read use_http_mode or disable_https from config (for backward compatibility)
USE_HTTP_MODE = bool(medi.get('use_http_mode', False) or medi.get('disable_https', False))
# Hardcoded for now
# USE_HTTP_MODE = True
log("HTTP Mode: {}".format(USE_HTTP_MODE), level="INFO")

# IMPORTANT LIMITATION: HTTP Mode and Chrome Private Network Access (PNA)
# =========================================================================
# HTTP mode does NOT work when the webapp is served from HTTPS pages (e.g., Google Apps Script).
# Chrome's Private Network Access (PNA) security feature blocks HTTPS-to-HTTP localhost requests
# at the browser level, BEFORE they reach the server. This is a browser security policy that
# cannot be bypassed from JavaScript.
#
# Why this happens:
# - Chrome PNA blocks requests from HTTPS origins to HTTP localhost/private network addresses
# - The browser blocks the request before sending any network traffic (including preflight OPTIONS)
# - Server-side CORS headers are irrelevant because the request never reaches the server
#
# Workarounds:
# 1. Use HTTPS mode (recommended): Avoids PNA blocking but requires certificate trust
# 2. Serve webapp over HTTP: HTTP mode works when webapp is served from HTTP (not GAS)
# 3. Disable Chrome PNA (development only): Launch Chrome with flag:
#    --disable-features=BlockInsecurePrivateNetworkRequests
#    Example: chrome.exe --disable-features=BlockInsecurePrivateNetworkRequests
#    Note: This flag may be removed in future Chrome versions
#
# Recommendation: Use HTTPS mode for production. HTTP mode is only suitable for:
# - Development when webapp is served over HTTP (not from Google Apps Script)
# - Testing with PNA disabled via browser flag
# =========================================================================

# Configuration validation: HTTP mode should only be used with localhost
if USE_HTTP_MODE:
    # Verify SERVER_HOST is localhost (will be set later, but validate here too)
    server_host_check = medi.get('gmail_server_host', '127.0.0.1')
    if server_host_check not in ('127.0.0.1', 'localhost', '::1'):
        log("ERROR: HTTP mode can only be used with localhost hosts (127.0.0.1 or localhost). "
            "Current host: {}. Disabling HTTP mode for security.".format(server_host_check), level="ERROR")
        USE_HTTP_MODE = False
    else:
        # Prominent security warning when HTTP mode is enabled
        log("=" * 80, level="WARNING")
        log("HTTP MODE ENABLED - Data transmission is unencrypted.", level="WARNING")
        log("Only suitable for localhost development.", level="WARNING")
        log("Do not use in production or over network connections.", level="WARNING")
        log("=" * 80, level="WARNING")
        log("HTTP mode enabled. Server will run without SSL/TLS encryption.", level="INFO")
        log("NOTE: HTTP mode will NOT work from HTTPS pages (e.g., Google Apps Script) due to", level="WARNING")
        log("      Chrome Private Network Access blocking. Use HTTPS mode or disable PNA flag.", level="WARNING")

if not USE_HTTP_MODE:
    log("HTTPS mode enabled (default). Server will use SSL/TLS encryption.", level="DEBUG")


def _cert_provider_defaults():
    return {
        'mode': 'self_signed',
        'profile': 'default',
        'root_subject': '/CN=MediLink Managed Root CA',
        'server_subject': '/CN=127.0.0.1',
        'san': ['127.0.0.1', 'localhost'],
        'root_valid_days': 3650,
        'server_valid_days': DEFAULT_CERT_DAYS
    }


def _str_or_default(value, default):
    if isinstance(value, str):
        text = value.strip()
        return text or default
    return default if value in (None, '') else value


def _int_default(value, default):
    try:
        return int(value)
    except Exception:
        return default


def refresh_certificate_provider_settings(source_config=None):
    global CERT_PROVIDER_SETTINGS, CERT_MODE, MANAGED_CA_PROFILE_NAME
    global MANAGED_CA_ROOT_SUBJECT, MANAGED_CA_SERVER_SUBJECT
    global MANAGED_CA_SAN_LIST, MANAGED_CA_ROOT_VALID_DAYS, MANAGED_CA_SERVER_VALID_DAYS
    cfg = source_config or config
    provider_settings = None
    if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'get_certificate_provider_config'):
        try:
            provider_settings = MediLink_ConfigLoader.get_certificate_provider_config(cfg)
        except Exception:
            provider_settings = None
    if not provider_settings:
        provider_settings = _cert_provider_defaults()
    CERT_PROVIDER_SETTINGS = provider_settings
    CERT_MODE = 'managed_ca' # Force managed CA for modern browsers on Win 11
    MANAGED_CA_PROFILE_NAME = _str_or_default(provider_settings.get('profile'), 'default')
    MANAGED_CA_ROOT_SUBJECT = provider_settings.get('root_subject')
    if not (MANAGED_CA_ROOT_SUBJECT or '').startswith('/'):
        MANAGED_CA_ROOT_SUBJECT = '/CN=MediLink Managed Root CA'
    
    MANAGED_CA_SERVER_SUBJECT = provider_settings.get('server_subject')
    if not (MANAGED_CA_SERVER_SUBJECT or '').startswith('/'):
        MANAGED_CA_SERVER_SUBJECT = '/CN=127.0.0.1'
    if isinstance(provider_settings.get('san'), list):
        MANAGED_CA_SAN_LIST = [str(item) for item in provider_settings.get('san') if item]
        if not MANAGED_CA_SAN_LIST:
            MANAGED_CA_SAN_LIST = ['127.0.0.1', 'localhost']
    else:
        MANAGED_CA_SAN_LIST = ['127.0.0.1', 'localhost']
    MANAGED_CA_ROOT_VALID_DAYS = _int_default(provider_settings.get('root_valid_days'), 3650)
    MANAGED_CA_SERVER_VALID_DAYS = _int_default(provider_settings.get('server_valid_days'), DEFAULT_CERT_DAYS)
    global MANAGED_CA_ENABLED
    MANAGED_CA_ENABLED = bool(CERTIFICATE_AUTHORITY_AVAILABLE and CERT_MODE == 'managed_ca')


def rebuild_ca_profile():
    global CA_PROFILE, MANAGED_CA_ENABLED
    CA_PROFILE = None
    MANAGED_CA_ENABLED = bool(CERTIFICATE_AUTHORITY_AVAILABLE and CERT_MODE == 'managed_ca')
    
    # INSTRUMENTATION POINT: Log Managed CA initialization state (MANAGED_CA_ENABLED, CERT_MODE, storage paths).
    # This helps debug why Managed CA might not be initializing correctly.

    if not (MANAGED_CA_ENABLED and certificate_authority):
        return
    try:
        ca_storage_root = certificate_authority.resolve_default_ca_dir(local_storage_path=local_storage_path)
        # INSTRUMENTATION POINT: Log CA storage root path to verify it's being resolved correctly.
        profile = certificate_authority.create_profile(
            profile_name=MANAGED_CA_PROFILE_NAME,
            storage_root=ca_storage_root,
            server_cert_path=ABS_CERT_FILE,
            server_key_path=ABS_KEY_FILE,
            openssl_config=get_openssl_cnf(),
            san_list=MANAGED_CA_SAN_LIST,
            root_subject=MANAGED_CA_ROOT_SUBJECT,
            server_subject=MANAGED_CA_SERVER_SUBJECT
        )
        profile['root_valid_days'] = MANAGED_CA_ROOT_VALID_DAYS
        profile['server_valid_days'] = MANAGED_CA_SERVER_VALID_DAYS
        CA_PROFILE = profile
    except Exception as profile_exc:
        MANAGED_CA_ENABLED = False
        CA_PROFILE = None
        try:
            log("Unable to initialize managed CA profile: {}".format(profile_exc), level="WARNING")
        except Exception:
            pass


server_port = medi.get('gmail_server_port', DEFAULT_SERVER_PORT)
SERVER_HOST = '127.0.0.1' # Standard host for this project; localhost can sometimes cause trust mismatch
# Make LOCAL_SERVER_BASE_URL conditional on HTTP mode
if USE_HTTP_MODE:
    LOCAL_SERVER_BASE_URL = 'http://{}:{}'.format(SERVER_HOST, server_port)
else:
    LOCAL_SERVER_BASE_URL = 'https://{}:{}'.format(SERVER_HOST, server_port)
cert_file = 'server.cert'
key_file = 'server.key'
# Note: openssl.cnf resolution is now lazy - see get_openssl_cnf() function

ABS_CERT_FILE = os.path.abspath(cert_file)
ABS_KEY_FILE = os.path.abspath(key_file)
CA_PROFILE = None
CA_STATUS_CACHE = {}
MANAGED_CA_ENABLED = False

TOKEN_PATH = shared_resolve_token_path(medi)
local_storage_path = medi.get('local_storage_path', '.')
downloaded_emails_file = os.path.join(local_storage_path, 'downloaded_emails.txt')

refresh_certificate_provider_settings(config)
rebuild_ca_profile()


def _update_certificate_provider_mode(new_mode, extra_fields=None):
    if not MediLink_ConfigLoader or not hasattr(MediLink_ConfigLoader, 'update_certificate_provider_config'):
        return False, "Config mutation helper unavailable"
    payload = {'mode': new_mode}
    if isinstance(extra_fields, dict):
        payload.update(extra_fields)
    success, error = MediLink_ConfigLoader.update_certificate_provider_config(payload)
    if success:
        try:
            MediLink_ConfigLoader.clear_config_cache()
        except Exception:
            pass
        try:
            global config, medi
            config, _ = load_configuration()
            medi = extract_medilink_config(config)
            refresh_certificate_provider_settings(config)
            rebuild_ca_profile()
        except Exception:
            pass
    return success, error


def is_managed_ca_active():
    return bool(MANAGED_CA_ENABLED and CA_PROFILE and certificate_authority)


def get_managed_ca_status(refresh=False):
    """Return cached CA status, refreshing via helper when necessary."""
    global CA_STATUS_CACHE
    if not is_managed_ca_active():
        return {}
    if refresh or not CA_STATUS_CACHE:
        try:
            CA_STATUS_CACHE = certificate_authority.describe_status(CA_PROFILE, log=log) or {}
        except Exception as status_err:
            try:
                log("Unable to describe managed CA status: {}".format(status_err), level="DEBUG")
            except Exception:
                pass
            CA_STATUS_CACHE = {}
    return CA_STATUS_CACHE


httpd = None  # Global variable for the HTTP server
shutdown_event = Event()  # Event to signal shutdown
server_crashed = False  # Flag to track if server thread crashed
# Activity tracking: renamed from "secure activity" to work in both HTTP and HTTPS modes
LAST_ACTIVITY_TS = time.time()  # Renamed from LAST_SECURE_ACTIVITY_TS for HTTP mode compatibility
LAST_SECURE_ACTIVITY_TS = LAST_ACTIVITY_TS  # Alias for backward compatibility
CERT_WARNING_EMITTED = False
ACTIVITY_PATHS = {'/_diag', '/download', '/delete-files', '/_cert', '/status', '/ca/root.crt', '/ca/server-info.json', '/ca/enable', '/mode'}
SECURE_ACTIVITY_PATHS = ACTIVITY_PATHS  # Alias for backward compatibility

# Safe-to-close flag and lightweight server status tracking
SAFE_TO_CLOSE = False
SERVER_STATUS = {
    'phase': 'idle',  # idle|processing|downloading|cleanup_triggered|cleanup_confirmed|done|error
    'linksReceived': 0,
    'filesDownloaded': 0,
    'filesToDelete': 0,
    'filesDeleted': 0,
    'lastError': None,
}
RECENT_REQUESTS = deque(maxlen=25)
CONNECTION_LOSS_REPORTED = False
HAD_ACTIVITY = False  # Renamed from HAD_SECURE_ACTIVITY for HTTP mode compatibility
HAD_SECURE_ACTIVITY = False  # Alias for backward compatibility
WATCHDOG_THREAD = None

def set_safe_to_close(value):
    global SAFE_TO_CLOSE
    SAFE_TO_CLOSE = bool(value)

def set_phase(phase):
    try:
        SERVER_STATUS['phase'] = str(phase or '')
    except Exception:
        SERVER_STATUS['phase'] = 'error'

def set_counts(links_received=None, files_downloaded=None, files_to_delete=None, files_deleted=None):
    try:
        if links_received is not None:
            SERVER_STATUS['linksReceived'] = int(links_received)
        if files_downloaded is not None:
            SERVER_STATUS['filesDownloaded'] = int(files_downloaded)
        if files_to_delete is not None:
            SERVER_STATUS['filesToDelete'] = int(files_to_delete)
        if files_deleted is not None:
            SERVER_STATUS['filesDeleted'] = int(files_deleted)
    except Exception:
        pass

def set_error(msg):
    try:
        SERVER_STATUS['lastError'] = str(msg or '')
    except Exception:
        SERVER_STATUS['lastError'] = 'Unknown error'

def get_safe_status():
    try:
        elapsed = max(0, int(time.time() - LAST_ACTIVITY_TS))
        connectivity_info = {
            'secondsSinceSecureActivity': elapsed,  # Keep name for backward compatibility
            'secondsSinceActivity': elapsed,  # New name for HTTP mode compatibility
        }
        # Only include certificate warning in HTTPS mode
        if not USE_HTTP_MODE:
            connectivity_info['certificateWarningActive'] = bool(CERT_WARNING_EMITTED)
        else:
            connectivity_info['certificateWarningActive'] = False
            connectivity_info['connectionWarningActive'] = False  # HTTP mode doesn't have certificate warnings
        return {
            'safeToClose': bool(SAFE_TO_CLOSE),
            'phase': SERVER_STATUS.get('phase', 'idle'),
            'counts': {
                'linksReceived': SERVER_STATUS.get('linksReceived', 0),
                'filesDownloaded': SERVER_STATUS.get('filesDownloaded', 0),
                'filesToDelete': SERVER_STATUS.get('filesToDelete', 0),
                'filesDeleted': SERVER_STATUS.get('filesDeleted', 0),
            },
            'lastError': SERVER_STATUS.get('lastError'),
            'connectivity': connectivity_info,
            'use_http_mode': USE_HTTP_MODE  # Include mode in status
        }
    except Exception:
        return {'safeToClose': False, 'phase': 'error'}


def record_request_event(method, path, status, note=None, client=None):
    try:
        RECENT_REQUESTS.appendleft({
            'time': datetime.utcnow().isoformat() + 'Z',
            'method': method,
            'path': path,
            'status': status,
            'note': note,
            'client': client
        })
        if path in ACTIVITY_PATHS:
            mark_secure_activity()  # Function name kept for backward compatibility, works in both modes
    except Exception:
        pass


def _get_client_ip(handler):
    try:
        return handler.client_address[0]
    except Exception:
        return None


def mark_secure_activity():
    """Mark activity (works in both HTTP and HTTPS modes). Function name kept for backward compatibility."""
    global LAST_ACTIVITY_TS, LAST_SECURE_ACTIVITY_TS, CERT_WARNING_EMITTED, HAD_ACTIVITY, HAD_SECURE_ACTIVITY
    LAST_ACTIVITY_TS = time.time()
    LAST_SECURE_ACTIVITY_TS = LAST_ACTIVITY_TS  # Keep alias updated
    CERT_WARNING_EMITTED = False
    HAD_ACTIVITY = True
    HAD_SECURE_ACTIVITY = True  # Keep alias updated


def maybe_warn_secure_idle():
    """Check for idle activity and warn if needed. Works in both HTTP and HTTPS modes."""
    global CERT_WARNING_EMITTED
    elapsed = time.time() - LAST_ACTIVITY_TS
    if elapsed > LOSS_ALERT_SECONDS:
        _maybe_report_connection_loss(elapsed)
    # Only show certificate warnings in HTTPS mode
    if not USE_HTTP_MODE:
        if elapsed > 120 and not CERT_WARNING_EMITTED:
            log("No secure local HTTPS activity detected for {:.0f} seconds. Browser may still need to trust https://127.0.0.1:8000.".format(elapsed), level="WARNING")
            CERT_WARNING_EMITTED = True
    else:
        # In HTTP mode, just log activity status (no certificate warnings)
        if elapsed > 120:
            log("No local HTTP activity detected for {:.0f} seconds.".format(elapsed), level="DEBUG")
    # Auto-shutdown after timeout if no activity and not safe to close
    if elapsed > AUTO_SHUTDOWN_SECONDS and not SAFE_TO_CLOSE:
        mode_str = "HTTP" if USE_HTTP_MODE else "HTTPS"
        log("No {} activity for {:.0f} seconds. Auto-shutting down server.".format(mode_str, elapsed), level="INFO")
        shutdown_event.set()
    return elapsed


def _maybe_report_connection_loss(elapsed):
    """Report connection loss. Works in both HTTP and HTTPS modes."""
    global CONNECTION_LOSS_REPORTED
    if CONNECTION_LOSS_REPORTED or not HAD_ACTIVITY or SAFE_TO_CLOSE:
        return
    CONNECTION_LOSS_REPORTED = True
    mode_str = "HTTP" if USE_HTTP_MODE else "HTTPS"
    log("No {} activity for {:.0f} seconds. Triggering automated connection loss report.".format(mode_str, elapsed), level="WARNING")
    if _submit_support_bundle_email is None:
        log("Support bundle reporter unavailable; unable to auto-send connection loss bundle.", level="WARNING")
        return
    try:
        sent = _submit_support_bundle_email(zip_path=None, include_traceback=False)
        if sent:
            log("Connection loss bundle submitted via MediCafe error reporter.", level="INFO")
        else:
            log("Connection loss bundle creation/send failed; bundle queued for later.", level="WARNING")
    except Exception as report_exc:
        log("Failed to submit connection loss bundle: {}".format(report_exc), level="WARNING")


def _connection_watchdog_loop():
    while not shutdown_event.is_set():
        try:
            maybe_warn_secure_idle()
        except Exception as watchdog_err:
            try:
                log("Connection watchdog loop error: {}".format(watchdog_err), level="DEBUG")
            except Exception:
                pass
        time.sleep(CONNECTION_WATCHDOG_INTERVAL)


def ensure_connection_watchdog_running():
    global WATCHDOG_THREAD
    if WATCHDOG_THREAD and WATCHDOG_THREAD.is_alive():
        return
    WATCHDOG_THREAD = Thread(target=_connection_watchdog_loop, name="connection-watchdog", daemon=True)
    WATCHDOG_THREAD.start()


def get_certificate_summary(cert_path):
    summary = {
        'present': False
    }
    try:
        if os.path.exists(cert_path):
            summary['present'] = True
            ssl_impl = getattr(ssl, '_ssl', None)
            can_decode = ssl_impl is not None and hasattr(ssl_impl, '_test_decode_cert')
            if can_decode:
                cert_dict = ssl._ssl._test_decode_cert(cert_path)
                not_before = cert_dict.get('notBefore')
                not_after = cert_dict.get('notAfter')
                summary.update({
                    'subject': cert_dict.get('subject'),
                    'issuer': cert_dict.get('issuer'),
                    'notBefore': not_before,
                    'notAfter': not_after,
                    'serialNumber': cert_dict.get('serialNumber')
                })
            else:
                summary['warning'] = 'Certificate decoding not supported on this Python build.'
    except Exception as cert_err:
        summary['error'] = str(cert_err)
    return summary


def build_diagnostics_payload():
    try:
        recent = list(RECENT_REQUESTS)
    except Exception:
        recent = []
    
    # Get SSL/TLS information (uses shared helper to avoid duplication)
    # INSTRUMENTATION POINT: Log SSL module capabilities (OpenSSL version, TLS protocol support, SNI support).
    # This helps identify if the Python SSL module has the required features for modern TLS.
    ssl_info = {
        'version': getattr(ssl, 'OPENSSL_VERSION', 'Unknown'),
        'versionInfo': getattr(ssl, 'OPENSSL_VERSION_INFO', None),
        'availableTlsVersions': detect_available_tls_versions(),
    }
    
    # Check if running on Windows XP (uses shared helper)
    xp_detected = detect_is_windows_xp(os_name, os_version)
    
    # Build payload
    try:
        origin_report = '*'
        # Try to get origin from some global state if possible, but '*' is safer for reporting
    except:
        origin_report = '*'
        
    payload = {
        'status': 'ok',
        'time': datetime.utcnow().isoformat() + 'Z',
        'serverPort': server_port,
        'serverHost': SERVER_HOST,
        'safeStatus': get_safe_status(),
        'certificate': get_certificate_summary(cert_file),
        'certificateAuthority': {
            'mode': CERT_MODE,
            'managed': is_managed_ca_active(),
            'status': get_managed_ca_status()
        },
        'recentRequests': recent,
        'connectivity': {
            'secondsSinceSecureActivity': max(0, int(time.time() - LAST_ACTIVITY_TS)),  # Keep name for backward compatibility
            'secondsSinceActivity': max(0, int(time.time() - LAST_ACTIVITY_TS)),  # New name for HTTP mode
            'certificateWarningActive': bool(CERT_WARNING_EMITTED) if not USE_HTTP_MODE else False
        },
        'use_http_mode': USE_HTTP_MODE,
        'headers': {
            'Access-Control-Allow-Origin': origin_report,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Access-Control-Allow-Private-Network',
            'Access-Control-Allow-Private-Network': 'true',
            'Access-Control-Allow-Credentials': 'true',
            'Vary': 'Origin, Access-Control-Request-Private-Network'
        },
        'platform': {
            'os': os_name,
            'version': os_version,
            'isWindowsXP': xp_detected,
            'pythonVersion': sys.version_info[:3],
        },
        'ssl': ssl_info,
        'diagnosticsAvailable': DIAGNOSTICS_AVAILABLE,
        'endpoints': {
            'diag_html': '/_diag?html=1',
            'diag_full': '/_diag?full=1',
            'cert': '/_cert',
            'troubleshoot': '/_troubleshoot',
            'selftest': '/_selftest',
            'selftest_html': '/_selftest?html=1',
            'health': '/_health',
            'status': '/status',
        }
    }
    
    if payload['certificateAuthority']['managed']:
        payload['managedCA'] = {
            'nextSteps': [
                'If Firefox still blocks requests, download /ca/root.crt, import under Authorities, and restart Firefox.',
                'After importing, restart the MediLink helper if prompted so a managed server certificate is issued.'
            ],
            'enableEndpoint': '/ca/enable',
            'statusEndpoint': '/ca/server-info.json'
        }
    else:
        payload['managedCA'] = {
            'offerEscalation': True,
            'enableEndpoint': '/ca/enable',
            'statusEndpoint': '/ca/server-info.json'
        }

    if xp_detected:
        payload['xpNotes'] = [
            'Running on Windows XP - some features may be limited.',
            'Firefox 52 ESR is the last version supporting Windows XP.',
            'TLS 1.2 support requires Firefox 24+ or IE 11.',
            'Certificate exceptions may need to be re-added after browser restart.',
        ]
    
    return payload


# Define the scopes for the Gmail API and other required APIs
SCOPES = ' '.join([
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/script.external_request",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/script.scriptapp",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.email"
])

# Determine the operating system and version
os_name = platform.system()
os_version = platform.release()

# Set the credentials path based on the OS and version
CREDENTIALS_PATH = shared_resolve_credentials_path(medi, os_name=os_name, os_version=os_version)

# Resolve relative paths properly for both dev (repo_root) and prod (absolute) environments
# In dev, relative paths assume repo_root as working directory, but script may run from MediLink directory
if not os.path.isabs(CREDENTIALS_PATH):
    # If path doesn't exist at current location, try resolving relative to project root
    if not os.path.exists(CREDENTIALS_PATH):
        project_root_path = os.path.join(WORKSPACE_ROOT, CREDENTIALS_PATH)
        if os.path.exists(project_root_path):
            CREDENTIALS_PATH = os.path.normpath(project_root_path)
        else:
            # Fallback: try relative to current working directory (handles different working directories)
            cwd_path = os.path.join(os.getcwd(), CREDENTIALS_PATH)
            if os.path.exists(cwd_path):
                CREDENTIALS_PATH = os.path.normpath(cwd_path)

# Log the selected path for verification
log("Using CREDENTIALS_PATH: {}".format(CREDENTIALS_PATH), level="DEBUG")

# Make REDIRECT_URI conditional on HTTP mode
# HTTP mode: use localhost (Google OAuth preference for HTTP)
# HTTPS mode: use 127.0.0.1 (existing behavior)
# NOTE: HTTP mode redirect URI will only work if:
# - Webapp is served over HTTP (not from Google Apps Script HTTPS)
# - OR Chrome PNA is disabled via --disable-features=BlockInsecurePrivateNetworkRequests flag
# Chrome PNA blocks HTTPS-to-HTTP localhost requests at browser level
if USE_HTTP_MODE:
    REDIRECT_URI = 'http://localhost:{}'.format(server_port)
else:
    REDIRECT_URI = 'https://{}:{}'.format(SERVER_HOST, server_port)
log("OAuth redirect URI: {}".format(REDIRECT_URI), level="DEBUG")

# Validate OAuth redirect URI exists in credentials.json
def validate_redirect_uri(credentials_path, redirect_uri):
    """Validate that redirect_uri exists in credentials.json redirect_uris list."""
    try:
        if not os.path.exists(credentials_path):
            log("Warning: Credentials file not found, cannot validate redirect URI: {}".format(credentials_path), level="WARNING")
            return False
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        # Check both 'web' and 'installed' client types
        redirect_uris = []
        if 'web' in credentials and 'redirect_uris' in credentials['web']:
            redirect_uris.extend(credentials['web']['redirect_uris'])
        if 'installed' in credentials and 'redirect_uris' in credentials['installed']:
            redirect_uris.extend(credentials['installed']['redirect_uris'])
        if redirect_uri in redirect_uris:
            log("OAuth redirect URI validated: found in credentials.json", level="DEBUG")
            return True
        else:
            log("WARNING: OAuth redirect URI '{}' not found in credentials.json redirect_uris. "
                "Registered URIs: {}. This may cause OAuth flow to fail.".format(
                redirect_uri, redirect_uris), level="WARNING")
            return False
    except Exception as e:
        log("Error validating redirect URI: {}".format(e), level="DEBUG")
        return False

# Validate redirect URI (non-blocking, just logs warning)
validate_redirect_uri(CREDENTIALS_PATH, REDIRECT_URI)


def run_connection_diagnostics(cert_file='server.cert', key_file='server.key', 
                               server_port=8000, auto_fix=False, openssl_cnf='openssl.cnf'):
    """
    Run connection diagnostics using existing module functions.
    
    Returns early if HTTP mode is enabled (no certificate diagnostics needed).
    Wrapper that passes existing functions to avoid duplication.
    """
    # Skip diagnostics in HTTP mode (no certificates to diagnose)
    if USE_HTTP_MODE:
        return {'summary': {'can_start_server': True}, 'environment': {}, 'issues': [], 'warnings': [], 'note': 'HTTP mode: certificate diagnostics skipped'}
    
    if not DIAGNOSTICS_AVAILABLE or _run_diagnostics_base is None:
        return {'summary': {'can_start_server': True}, 'environment': {}, 'issues': [], 'warnings': []}
    
    # Pass existing functions to the diagnostics module to avoid duplication
    # Use lazy resolution if default parameter value is used, otherwise use provided value
    resolved_openssl_cnf = get_openssl_cnf() if openssl_cnf == 'openssl.cnf' else openssl_cnf
    return _run_diagnostics_base(
        cert_file=cert_file,
        key_file=key_file,
        server_port=server_port,
        os_name=os_name,  # Use existing module-level variable
        os_version=os_version,  # Use existing module-level variable
        cert_summary_fn=get_certificate_summary,  # Use existing function
        auto_fix=auto_fix,
        generate_cert_fn=http_generate_self_signed_cert if (auto_fix and CERT_MODE != 'managed_ca') else None,
        openssl_cnf=resolved_openssl_cnf
    )


def get_authorization_url():
    return oauth_get_authorization_url(CREDENTIALS_PATH, REDIRECT_URI, SCOPES, log)

def exchange_code_for_token(auth_code, retries=3):
    return oauth_exchange_code_for_token(auth_code, CREDENTIALS_PATH, REDIRECT_URI, log, retries=retries)

def _mask_token_value(value):
    """Mask a token value for safe logging. Returns first 4 and last 4 chars, or '***' if too short."""
    try:
        s = str(value or '')
        if len(s) <= 8:
            return '***'
        return s[:4] + '...' + s[-4:]
    except Exception:
        return '***'


def _mask_sensitive_dict(data):
    """Create a copy of a dict with sensitive fields masked for logging."""
    if not isinstance(data, dict):
        return data
    try:
        masked = data.copy()
        # Mask token fields
        for key in ['access_token', 'refresh_token', 'id_token']:
            if key in masked and masked[key]:
                masked[key] = _mask_token_value(masked[key])
        # Mask Authorization header if present
        if 'Authorization' in masked:
            auth_val = str(masked['Authorization'])
            if 'Bearer ' in auth_val:
                # Extract token from "Bearer <token>"
                parts = auth_val.split('Bearer ', 1)
                if len(parts) > 1:
                    token = parts[1].strip()
                    masked['Authorization'] = 'Bearer ' + _mask_token_value(token)
        return masked
    except Exception:
        return data


def get_access_token():
    return shared_get_gmail_access_token(log=log, medi_config=medi, os_name=os_name, os_version=os_version)

def refresh_access_token(refresh_token):
    return oauth_refresh_access_token(refresh_token, CREDENTIALS_PATH, log)

def bring_window_to_foreground():
    """Brings the current window to the foreground on Windows."""
    try:
        if platform.system() == 'Windows':
            pid = os.getpid()
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            current_pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(current_pid))
            if current_pid.value != pid:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                if ctypes.windll.user32.GetForegroundWindow() != hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 9)
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception as e:
        log("Error bringing window to foreground: {}".format(e))

# Shared mixin with all request handler methods (used by both HTTP and HTTPS handlers)
class _RequestHandlerMixin:
    """Shared mixin with all request handler methods for both HTTP and HTTPS modes."""
    # Overrides to mask Python/BaseHTTP version
    server_version = "MediLink/1.0"
    sys_version = ""

    # Disable DNS lookups for performance and to avoid timeouts on some networks
    def address_string(self):
        return str(self.client_address[0])

    def _set_headers(self):
        from MediLink.gmail_http_utils import set_standard_headers
        set_standard_headers(self)

    def _build_troubleshoot_html(self):
        """Build comprehensive troubleshooting HTML page.
        
        Delegates to gmail_html_utils.build_troubleshoot_html for HTML generation.
        """
        # Run diagnostics to gather environment/issue info
        diag_report = None
        if DIAGNOSTICS_AVAILABLE and not USE_HTTP_MODE:
            try:
                diag_report = run_connection_diagnostics(
                    cert_file=cert_file,
                    key_file=key_file,
                    server_port=server_port,
                    auto_fix=True,  # Enable auto-fix on troubleshoot page
                    openssl_cnf=get_openssl_cnf()
                )
                # If certificate was auto-fixed, log it
                if diag_report.get('fixes_successful'):
                    log("Auto-fixed certificate issues from troubleshoot page: {}".format(diag_report['fixes_successful']), level="INFO")
            except Exception as e:
                log("Error running diagnostics for troubleshoot page: {}".format(e), level="WARNING")
        
        # Get Firefox notes and browser hints
        firefox_notes = get_firefox_xp_compatibility_notes() if DIAGNOSTICS_AVAILABLE else {'notes': []}
        browser_hints = BROWSER_DIAGNOSTIC_HINTS if DIAGNOSTICS_AVAILABLE else {}
        
        # Get Firefox certificate diagnosis if available and certificate issues exist (skip in HTTP mode)
        firefox_diagnosis = None
        if not USE_HTTP_MODE and FIREFOX_CERT_DIAG_AVAILABLE and diag_report and diag_report.get('issues'):
            try:
                firefox_path = medi.get('firefox_path') or medi.get('browser_path')
                firefox_diagnosis = diagnose_firefox_certificate_exceptions(
                    cert_file=cert_file,
                    server_port=server_port,
                    firefox_path=firefox_path,
                    log=log
                )
            except Exception as fx_err:
                log("Firefox diagnosis unavailable for troubleshoot page: {}".format(fx_err), level="DEBUG")
        
        # Get certificate info for contextual guidance (skip in HTTP mode)
        cert_info = None
        if not USE_HTTP_MODE:
            try:
                cert_info = get_certificate_summary(cert_file)
            except Exception:
                pass
        
        # Delegate HTML generation to utility module
        provider_payload = None
        if not USE_HTTP_MODE:
            try:
                provider_payload = {
                    'mode': CERT_MODE,
                    'status': get_managed_ca_status(),
                    'san': MANAGED_CA_SAN_LIST,
                    'root_subject': MANAGED_CA_ROOT_SUBJECT,
                    'server_subject': MANAGED_CA_SERVER_SUBJECT
                }
            except Exception:
                provider_payload = None
        return html_build_troubleshoot_html(
            diag_report=diag_report,
            firefox_notes=firefox_notes,
            browser_hints=browser_hints,
            server_port=server_port,
            certificate_provider=provider_payload,
            firefox_diagnosis=firefox_diagnosis,
            cert_info=cert_info
        )

    def do_OPTIONS(self):
        # INSTRUMENTATION POINT: Log OPTIONS preflight requests (path, headers) to debug CORS issues.
        self.send_response(200)
        self._set_headers()
        # Log sent headers for debugging PNA
        try:
            with open(r'g:\My Drive\Codes\MediCafe\.cursor\debug.log', 'a') as f:
                import json as _json
                import time as _time
                f.write(_json.dumps({"sessionId":"debug-session", "runId":"run12", "hypothesisId":"A", "location":"MediLink_Gmail.py:do_OPTIONS", "message":"OPTIONS response headers sent", "timestamp":int(_time.time()*1000)}) + "\n")
        except: pass
        self.end_headers()
        record_request_event('OPTIONS', self.path, 200, note='preflight', client=_get_client_ip(self))
        try:
            origin = self.headers.get('Origin')
        except Exception:
            origin = None
        try:
            print("[CORS] Preflight {0} from {1}".format(self.path, origin))
        except Exception:
            pass

    def do_POST(self):
        """Handle POST requests with comprehensive exception handling to prevent server crashes."""
        from MediLink.gmail_http_utils import (
            parse_content_length, read_post_data, parse_json_data,
            send_error_response, safe_write_response, log_request_error
        )
        try:
            if self.path == '/download':
                set_phase('processing')
                try:
                    content_length = parse_content_length(self.headers, log_fn=log)
                except (KeyError, ValueError) as e:
                    send_error_response(self, 400, "Missing or invalid Content-Length header", log_fn=log, error_details=str(e))
                    return
                post_data = read_post_data(self, content_length, log_fn=log)
                if post_data is None:
                    return  # Client disconnected
                try:
                    data = parse_json_data(post_data, log_fn=log)
                except (ValueError, UnicodeDecodeError) as e:
                    send_error_response(self, 400, "Invalid request format", log_fn=log, error_details=str(e))
                    return
                links = data.get('links', [])
                log("Received links: {}".format(links), level="DEBUG")
                try:
                    print("[Handshake] Received {0} link(s) from webapp".format(len(links)))
                except Exception:
                    pass
                try:
                    set_counts(links_received=len(links))
                except Exception:
                    pass
                file_ids = [link.get('fileId', None) for link in links if link.get('fileId')]
                log("File IDs received from client: {}".format(file_ids), level="DEBUG")
                set_phase('downloading')
                try:
                    download_docx_files(links)
                except Exception as e:
                    set_phase('error')
                    set_error(str(e))
                # Only delete files that actually downloaded successfully
                downloaded_names = load_downloaded_emails()
                successful_ids = []
                try:
                    name_to_id = { (link.get('filename') or ''): link.get('fileId') for link in links if link.get('fileId') }
                    for name in downloaded_names:
                        fid = name_to_id.get(name)
                        if fid:
                            successful_ids.append(fid)
                except Exception as e:
                    log("Error computing successful file IDs for cleanup: {}".format(e))
                    successful_ids = file_ids  # Fallback: attempt all provided IDs
                try:
                    set_counts(files_to_delete=len(successful_ids))
                except Exception:
                    pass
                # Trigger cleanup in Apps Script with auth
                try:
                    cleanup_ok = False
                    if successful_ids:
                        ok = send_delete_request_to_gas(successful_ids)
                        if ok:
                            set_phase('cleanup_confirmed')
                            try:
                                set_counts(files_deleted=len(successful_ids))
                            except Exception:
                                pass
                            cleanup_ok = True
                        else:
                            set_phase('cleanup_triggered')
                            set_error('Cleanup request not confirmed')
                    else:
                        log("No successful file IDs to delete after download.")
                        set_phase('done')
                        cleanup_ok = True  # nothing to delete -> safe
                except Exception as e:
                    log("Cleanup trigger failed: {}".format(e))
                    set_phase('error')
                    set_error(str(e))
                    cleanup_ok = False
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                try:
                    set_safe_to_close(bool(cleanup_ok))
                except Exception:
                    pass
                response = json.dumps({"status": "success", "message": "All files downloaded", "fileIds": successful_ids, "safeToClose": bool(cleanup_ok)})
                safe_write_response(self, response)
                try:
                    print("[Handshake] Completed. Returning success for {0} fileId(s)".format(len(successful_ids)))
                except Exception:
                    pass
                shutdown_event.set()
                bring_window_to_foreground()
                record_request_event('POST', '/download', 200, note='download', client=_get_client_ip(self))
                return
            elif self.path == '/shutdown':
                log("Shutdown request received.")
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                response = json.dumps({"status": "success", "message": "Server is shutting down."})
                safe_write_response(self, response)
                shutdown_event.set()
                record_request_event('POST', '/shutdown', 200, note='shutdown', client=_get_client_ip(self))
                return
            elif self.path == '/delete-files':
                try:
                    content_length = parse_content_length(self.headers, log_fn=log)
                except (KeyError, ValueError) as e:
                    send_error_response(self, 400, "Missing or invalid Content-Length header", log_fn=log, error_details=str(e))
                    return
                post_data = read_post_data(self, content_length, log_fn=log)
                if post_data is None:
                    return  # Client disconnected
                try:
                    data = parse_json_data(post_data, log_fn=log)
                except (ValueError, UnicodeDecodeError) as e:
                    send_error_response(self, 400, "Invalid request format", log_fn=log, error_details=str(e))
                    return
                file_ids = data.get('fileIds', [])
                log("File IDs to delete received from client: {}".format(file_ids))
                if not isinstance(file_ids, list):
                    send_error_response(self, 400, "Invalid fileIds parameter.", log_fn=log)
                    return
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                response = json.dumps({"status": "success", "message": "Files deleted successfully."})
                safe_write_response(self, response)
                record_request_event('POST', '/delete-files', 200, note='cleanup', client=_get_client_ip(self))
                return
            elif self.path == '/ca/enable':
                if USE_HTTP_MODE:
                    self.send_response(503)
                    self._set_headers()
                    self.end_headers()
                    safe_write_response(self, json.dumps({"error": "Certificate authority management not available in HTTP mode"}))
                    record_request_event('POST', '/ca/enable', 503, note='ca-enable-http-mode', client=_get_client_ip(self))
                    return
                try:
                    content_length = parse_content_length(self.headers, log_fn=log)
                except (KeyError, ValueError) as e:
                    send_error_response(self, 400, "Missing or invalid Content-Length header", log_fn=log, error_details=str(e))
                    return
                post_data = read_post_data(self, content_length, log_fn=log)
                if post_data is None:
                    return
                try:
                    data = parse_json_data(post_data, log_fn=log)
                except (ValueError, UnicodeDecodeError) as e:
                    send_error_response(self, 400, "Invalid request format", log_fn=log, error_details=str(e))
                    return
                desired_mode = _str_or_default(data.get('mode'), 'managed_ca').lower()
                if desired_mode not in ('managed_ca', 'self_signed'):
                    desired_mode = 'managed_ca'
                extra_fields = {}
                if desired_mode == 'managed_ca':
                    extra_fields = {
                        'profile': MANAGED_CA_PROFILE_NAME,
                        'root_subject': MANAGED_CA_ROOT_SUBJECT,
                        'server_subject': MANAGED_CA_SERVER_SUBJECT,
                        'san': MANAGED_CA_SAN_LIST,
                        'root_valid_days': MANAGED_CA_ROOT_VALID_DAYS,
                        'server_valid_days': MANAGED_CA_SERVER_VALID_DAYS
                    }
                success, error = _update_certificate_provider_mode(desired_mode, extra_fields)
                response = {
                    'success': bool(success),
                    'mode': CERT_MODE,
                    'managed': is_managed_ca_active()
                }
                if error:
                    response['error'] = error
                status_code = 200 if success else 500
                self.send_response(status_code)
                self._set_headers()
                self.end_headers()
                safe_write_response(self, json.dumps(response))
                record_request_event('POST', '/ca/enable', status_code, note='ca-enable', client=_get_client_ip(self))
                return
            else:
                self.send_response(404)
                self._set_headers()
                self.end_headers()
        except KeyError as e:
            send_error_response(self, 400, "Missing required header: {}".format(str(e)), log_fn=log, error_details=str(e))
        except (ValueError, TypeError) as e:
            # Note: json.JSONDecodeError doesn't exist in Python 3.4.4; json.loads raises ValueError
            send_error_response(self, 400, "Invalid request format: {}".format(str(e)), log_fn=log, error_details=str(e))
        except OSError as e:
            from MediLink.gmail_http_utils import _is_expected_disconnect
            if _is_expected_disconnect(e):
                log("Client disconnected during POST request handling: {}".format(e), level="DEBUG")
                self.close_connection = True
            else:
                log("Connection error in POST request: {} - This usually indicates a network error, client disconnect, or socket issue on Windows XP".format(e), level="ERROR")
                send_error_response(self, 500, "Connection error", log_fn=log, error_details=str(e))
        except Exception as e:
            log_request_error(e, self.path, "POST", log, headers=self.headers)
            send_error_response(self, 500, "Internal server error", log_fn=log, error_details=str(e))

    def do_GET(self):
        """Handle GET requests with comprehensive exception handling to prevent server crashes."""
        # INSTRUMENTATION POINT: Log GET requests (path, headers) to track which endpoints are being accessed.
        from MediLink.gmail_http_utils import (
            _is_expected_disconnect,
            send_error_response, log_request_error
        )
        try:
            log("Full request path: {}".format(self.path), level="DEBUG")
            if self.path == '/_health':
                try:
                    print("[Health] Probe OK")
                except Exception:
                    pass
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                try:
                    self.wfile.write(json.dumps({"status": "ok"}).encode('ascii'))
                except Exception:
                    try:
                        self.wfile.write(b'{"status":"ok"}')
                    except OSError as e:
                        if _is_expected_disconnect(e):
                            self.close_connection = True
                        else:
                            raise
                record_request_event('GET', '/_health', 200, note='health-probe', client=_get_client_ip(self))
                return
            elif self.path == '/mode':
                # Server mode endpoint for webapp detection
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                mode_response = {
                    'mode': 'http' if USE_HTTP_MODE else 'https',
                    'use_http_mode': USE_HTTP_MODE
                }
                try:
                    self.wfile.write(json.dumps(mode_response).encode('utf-8'))
                except Exception as write_err:
                    log("Failed to write mode response: {}".format(write_err))
                record_request_event('GET', '/mode', 200, note='mode-endpoint', client=_get_client_ip(self))
                return
            elif self.path.startswith('/_selftest'):
                # Run self-tests to verify server connectivity and SSL configuration
                # This endpoint helps diagnose Firefox/XP connectivity issues
                self.send_response(200)
                
                # Check if HTML format is requested
                want_html = 'html=1' in self.path or 'format=html' in self.path
                
                if USE_HTTP_MODE:
                    # In HTTP mode, skip SSL/certificate tests
                    selftest_results = {
                        'note': 'HTTP mode: SSL/certificate tests skipped',
                        'tests': {},
                        'summary': {'total': 0, 'passed': 0, 'failed': 0, 'all_passed': True},
                        'mode': 'http'
                    }
                elif DIAGNOSTICS_AVAILABLE and _run_all_selftests:
                    try:
                        # Run self-tests (skip network tests since we ARE the server)
                        selftest_results = _run_all_selftests(
                            port=server_port,
                            cert_file=cert_file,
                            include_network=False  # Can't test ourselves while handling request
                        )
                        # Add note about network tests
                        selftest_results['note'] = 'Network tests skipped (cannot self-test while handling request). Run from external script for full test.'
                    except Exception as st_err:
                        log("Error running self-tests: {}".format(st_err), level="ERROR")
                        selftest_results = {
                            'error': str(st_err),
                            'tests': {},
                            'summary': {'total': 0, 'passed': 0, 'failed': 0, 'all_passed': False}
                        }
                else:
                    selftest_results = {
                        'error': 'Diagnostics module not available',
                        'tests': {},
                        'summary': {'total': 0, 'passed': 0, 'failed': 0, 'all_passed': False}
                    }
                
                if want_html:
                    # Build simple HTML response
                    html_parts = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>MediLink Self-Test</title>',
                                  '<style>body{font-family:Arial,sans-serif;padding:20px;background:#f5f3e8;}',
                                  '.container{max-width:800px;margin:0 auto;background:white;padding:24px;border:1px solid #ccc;}',
                                  'h1{color:#3B2323;}.pass{color:#1f5132;}.fail{color:#dc2626;}',
                                  'pre{background:#f0f0f0;padding:12px;overflow:auto;}</style></head><body>',
                                  '<div class="container"><h1>MediLink Self-Test Results</h1>']
                    
                    summary = selftest_results.get('summary', {})
                    if summary.get('all_passed'):
                        html_parts.append('<p class="pass"><strong>All tests passed</strong></p>')
                    else:
                        html_parts.append('<p class="fail"><strong>{} of {} tests failed</strong></p>'.format(
                            summary.get('failed', 0), summary.get('total', 0)))
                    
                    if selftest_results.get('note'):
                        html_parts.append('<p><em>{}</em></p>'.format(selftest_results['note']))
                    
                    html_parts.append('<h2>Test Results</h2><pre>{}</pre>'.format(
                        json.dumps(selftest_results, indent=2, default=str)))
                    
                    html_parts.append('<p><a href="/_diag?html=1">Full Diagnostics</a> | ')
                    html_parts.append('<a href="/_troubleshoot">Troubleshooting Guide</a> | ')
                    html_parts.append('<a href="/">Server Status</a></p>')
                    html_parts.append('</div></body></html>')
                    
                    response_body = ''.join(html_parts)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                else:
                    response_body = json.dumps(selftest_results, indent=2, default=str)
                    self.send_header('Content-type', 'application/json')
                
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                
                try:
                    self.wfile.write(response_body.encode('utf-8'))
                except Exception as write_err:
                    log("Failed to write selftest response: {}".format(write_err))
                
                record_request_event('GET', '/_selftest', 200, note='selftest', client=_get_client_ip(self))
                return
            elif self.path == '/status':
                maybe_warn_secure_idle()
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                try:
                    payload = json.dumps(get_safe_status())
                except Exception:
                    payload = '{}'
                try:
                    self.wfile.write(payload.encode('ascii'))
                except Exception:
                    try:
                        self.wfile.write(payload.encode('utf-8'))
                    except Exception:
                        try:
                            self.wfile.write(payload.encode('utf-8', errors='ignore'))
                        except OSError as e:
                            if _is_expected_disconnect(e):
                                self.close_connection = True
                            else:
                                raise
                record_request_event('GET', '/status', 200, note='status', client=_get_client_ip(self))
                return
            elif self.path.startswith('/_diag'):
                # Check if HTML format is requested (browser access)
                want_html = 'html=1' in self.path or 'format=html' in self.path
                include_full = 'full=1' in self.path or 'refresh=1' in self.path
                
                # Build basic diagnostics payload
                diag_payload = build_diagnostics_payload()
                
                # Run comprehensive diagnostics if available and requested (skip in HTTP mode)
                if not USE_HTTP_MODE and DIAGNOSTICS_AVAILABLE and include_full:
                    try:
                        # Enable auto_fix for runtime diagnostics
                        # User will be notified if server restart is needed
                        full_diag = run_connection_diagnostics(
                            cert_file=cert_file,
                            key_file=key_file,
                            server_port=server_port,
                            auto_fix=True,  # Enable auto-fix during runtime
                            openssl_cnf=get_openssl_cnf()
                        )
                        diag_payload['fullDiagnostics'] = full_diag
                        
                        # If certificate was auto-fixed, add prominent notification
                        if full_diag.get('user_action_required') and full_diag['user_action_required'].get('requires_restart'):
                            diag_payload['certificateAutoFixed'] = True
                            diag_payload['restartRequired'] = True
                        
                        diag_payload['firefoxNotes'] = get_firefox_xp_compatibility_notes()
                        diag_payload['browserHints'] = BROWSER_DIAGNOSTIC_HINTS
                    except Exception as full_diag_err:
                        log("Error running full diagnostics: {}".format(full_diag_err), level="WARNING")
                        diag_payload['fullDiagnosticsError'] = str(full_diag_err)
                
                self.send_response(200)
                
                if want_html and DIAGNOSTICS_AVAILABLE and not USE_HTTP_MODE:
                    # Return HTML diagnostics page
                    try:
                        if 'fullDiagnostics' not in diag_payload:
                            # Enable auto_fix for HTML diagnostics view
                            full_diag = run_connection_diagnostics(
                                cert_file=cert_file,
                                key_file=key_file,
                                server_port=server_port,
                                auto_fix=True,  # Enable auto-fix during runtime
                                openssl_cnf=get_openssl_cnf()
                            )
                            # Check if certificate was auto-fixed
                            if full_diag.get('user_action_required') and full_diag['user_action_required'].get('requires_restart'):
                                diag_payload['certificateAutoFixed'] = True
                                diag_payload['restartRequired'] = True
                        else:
                            full_diag = diag_payload['fullDiagnostics']
                        # Pass auto-fix flags to HTML builder
                        diag_html = html_build_diagnostics_html(full_diag, server_port, certificate_auto_fixed=diag_payload.get('certificateAutoFixed', False), restart_required=diag_payload.get('restartRequired', False))
                    except Exception as html_err:
                        log("Error building diagnostics HTML: {}".format(html_err), level="WARNING")
                        diag_html = "<html><body><h1>Diagnostics</h1><pre>{}</pre></body></html>".format(
                            json.dumps(diag_payload, indent=2)
                        )
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.send_header('Access-Control-Allow-Private-Network', 'true')
                    self.end_headers()
                    try:
                        self.wfile.write(diag_html.encode('utf-8'))
                    except Exception as write_err:
                        log("Failed to write diagnostics HTML: {}".format(write_err))
                else:
                    # Return JSON diagnostics
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps(diag_payload).encode('utf-8'))
                    except Exception as write_err:
                        log("Failed to write diagnostics payload: {}".format(write_err))
                record_request_event('GET', '/_diag', 200, note='diagnostics', client=_get_client_ip(self))
                return
            elif self.path.startswith('/_troubleshoot'):
                # Comprehensive troubleshooting page
                try:
                    troubleshoot_html = self._build_troubleshoot_html()
                except Exception as ts_err:
                    log("Error building troubleshoot page: {}".format(ts_err), level="ERROR")
                    troubleshoot_html = html_build_simple_error_html("Troubleshooting Error", str(ts_err), server_port)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(troubleshoot_html.encode('utf-8'))
                except Exception as write_err:
                    log("Failed to write troubleshoot page: {}".format(write_err))
                record_request_event('GET', '/_troubleshoot', 200, note='troubleshoot', client=_get_client_ip(self))
                return
            elif self.path == '/_cert_download' or self.path.startswith('/_cert_download'):
                # Certificate download endpoint - not available in HTTP mode
                if USE_HTTP_MODE:
                    self.send_response(404)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(b'Certificate download not available in HTTP mode')
                    record_request_event('GET', '/_cert_download', 404, note='cert-download-http-mode', client=_get_client_ip(self))
                    return
                # Serve certificate file for download (check before /_cert to avoid path matching conflict)
                try:
                    if os.path.exists(cert_file):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/x-x509-ca-cert')
                        self.send_header('Content-Disposition', 'attachment; filename="medilink-local.crt"')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        with open(cert_file, 'rb') as f:
                            self.wfile.write(f.read())
                        record_request_event('GET', '/_cert_download', 200, note='cert-download', client=_get_client_ip(self))
                    else:
                        self.send_response(404)
                        self._set_headers()
                        self.end_headers()
                        self.wfile.write(b'Certificate file not found')
                        record_request_event('GET', '/_cert_download', 404, note='cert-not-found', client=_get_client_ip(self))
                except Exception as e:
                    log("Error serving certificate download: {}".format(e), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(b'Error serving certificate file')
                    except Exception:
                        pass
                return
            elif self.path == '/_cert_fingerprint':
                # Certificate fingerprint endpoint - not available in HTTP mode
                if USE_HTTP_MODE:
                    self.send_response(503)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Certificate fingerprint not available in HTTP mode"}).encode('utf-8'))
                    record_request_event('GET', '/_cert_fingerprint', 503, note='cert-fingerprint-http-mode', client=_get_client_ip(self))
                    return
                # Return certificate fingerprint as JSON (for diagnostics) - check before /_cert to avoid path matching conflict
                try:
                    fingerprint = http_get_certificate_fingerprint(cert_file, log=log)
                    cert_info = get_certificate_summary(cert_file)
                    response_data = {
                        'fingerprint': fingerprint,
                        'certificate': cert_info,
                        'download_url': '/_cert_download'
                    }
                    self.send_response(200)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                    record_request_event('GET', '/_cert_fingerprint', 200, note='cert-fingerprint', client=_get_client_ip(self))
                except Exception as e:
                    log("Error serving certificate fingerprint: {}".format(e), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                    except Exception:
                        pass
                return
            elif self.path == '/_cert_diagnose_firefox':
                # Firefox certificate diagnosis endpoint - not available in HTTP mode
                if USE_HTTP_MODE:
                    self.send_response(503)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Firefox certificate diagnosis not available in HTTP mode"}).encode('utf-8'))
                    record_request_event('GET', '/_cert_diagnose_firefox', 503, note='cert-diagnose-firefox-http-mode', client=_get_client_ip(self))
                    return
                # Diagnose Firefox certificate exceptions - check before /_cert to avoid path matching conflict
                try:
                    if not FIREFOX_CERT_DIAG_AVAILABLE:
                        response_data = {'error': 'Firefox certificate diagnostics not available'}
                    else:
                        # Try to get Firefox path from config
                        firefox_path = medi.get('firefox_path') or medi.get('browser_path')
                        diagnosis = diagnose_firefox_certificate_exceptions(
                            cert_file=cert_file,
                            server_port=server_port,
                            firefox_path=firefox_path,
                            log=log
                        )
                        response_data = diagnosis
                    
                    self.send_response(200)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                    record_request_event('GET', '/_cert_diagnose_firefox', 200, note='cert-diagnose-firefox', client=_get_client_ip(self))
                except Exception as e:
                    log("Error serving Firefox certificate diagnosis: {}".format(e), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                    except Exception:
                        pass
                return
            elif self.path == '/_cert' or self.path.startswith('/_cert'):
                # Certificate info endpoint - not available in HTTP mode
                if USE_HTTP_MODE:
                    self.send_response(503)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.send_header('Access-Control-Allow-Private-Network', 'true')
                    self.end_headers()
                    error_html = "<html><body><h1>Certificate Information</h1><p>Certificate information not available in HTTP mode.</p><p><a href='/'>Return to server status</a></p></body></html>"
                    try:
                        self.wfile.write(error_html.encode('utf-8'))
                    except Exception as write_err:
                        log("Failed to write cert error response: {}".format(write_err))
                    record_request_event('GET', '/_cert', 503, note='cert-info-http-mode', client=_get_client_ip(self))
                    return
                try:
                    cert_info = get_certificate_summary(cert_file)
                    fingerprint = http_get_certificate_fingerprint(cert_file, log=log)
                    
                    # Detect browser from User-Agent header for tailored instructions
                    browser_info = None
                    try:
                        user_agent = self.headers.get('User-Agent', '')
                        if 'Firefox/52' in user_agent and 'Windows NT 5' in user_agent:
                            browser_info = {'name': 'Firefox', 'version': '52', 'isWindowsXP': True}
                        elif 'Firefox/' in user_agent:
                            # Try to extract Firefox version
                            match = re.search(r'Firefox/(\d+)', user_agent)
                            if match:
                                version = match.group(1)
                                is_xp = 'Windows NT 5' in user_agent
                                browser_info = {'name': 'Firefox', 'version': version, 'isWindowsXP': is_xp}
                    except Exception as ua_err:
                        log("Error detecting browser from User-Agent: {}".format(ua_err), level="DEBUG")
                    
                    cert_html = html_build_cert_info_html(cert_info, fingerprint=fingerprint, browser_info=browser_info, server_port=server_port)
                except Exception as cert_err:
                    log("Error generating certificate info page: {}".format(cert_err), level="ERROR")
                    # Provide a fallback HTML page on error
                    cert_html = html_build_fallback_cert_html(str(cert_err), server_port)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(cert_html.encode('utf-8'))
                except Exception as write_err:
                    log("Failed to write cert info payload: {}".format(write_err))
                record_request_event('GET', '/_cert', 200, note='cert-info', client=_get_client_ip(self))
                return
            elif self.path.startswith('/ca/root.crt'):
                if USE_HTTP_MODE:
                    self.send_response(404)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Managed CA not available in HTTP mode'}).encode('utf-8'))
                    record_request_event('GET', '/ca/root.crt', 404, note='ca-root-http-mode', client=_get_client_ip(self))
                    return
                if not is_managed_ca_active():
                    self.send_response(404)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': 'Managed CA mode disabled'}).encode('utf-8'))
                    except Exception:
                        pass
                    record_request_event('GET', '/ca/root.crt', 404, note='ca-root-missing', client=_get_client_ip(self))
                    return
                root_path = CA_PROFILE.get('root_cert_path')
                if not root_path or not os.path.exists(root_path):
                    try:
                        certificate_authority.ensure_root(CA_PROFILE, log=log, subprocess_module=subprocess)
                        root_path = CA_PROFILE.get('root_cert_path')
                    except Exception as root_err:
                        log("Unable to ensure managed CA root before download: {}".format(root_err), level="ERROR")
                if not root_path or not os.path.exists(root_path):
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': 'Managed CA root not available'}).encode('utf-8'))
                    except Exception:
                        pass
                    record_request_event('GET', '/ca/root.crt', 500, note='ca-root-error', client=_get_client_ip(self))
                    return
                try:
                    with open(root_path, 'rb') as root_file:
                        root_bytes = root_file.read()
                except Exception as read_err:
                    log("Failed to read managed CA root for download: {}".format(read_err), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': 'Unable to read managed root'}).encode('utf-8'))
                    except Exception:
                        pass
                    record_request_event('GET', '/ca/root.crt', 500, note='ca-root-read-failed', client=_get_client_ip(self))
                    return
                self.send_response(200)
                self.send_header('Content-type', 'application/x-x509-ca-cert')
                self.send_header('Content-Disposition', 'attachment; filename="medilink-managed-root.crt"')
                self.send_header('Cache-Control', 'no-store, max-age=0')
                self.send_header('Content-Length', str(len(root_bytes)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(root_bytes)
                except Exception as write_err:
                    log("Failed to stream managed CA root: {}".format(write_err), level="ERROR")
                record_request_event('GET', '/ca/root.crt', 200, note='ca-root-download', client=_get_client_ip(self))
                return
            elif self.path.startswith('/ca/server-info'):
                refresh = 'refresh=1' in self.path or 'full=1' in self.path
                status = get_managed_ca_status(refresh=refresh) if not USE_HTTP_MODE else {}
                payload = {
                    'mode': CERT_MODE,
                    'managed': is_managed_ca_active() if not USE_HTTP_MODE else False,
                    'status': status,
                    'download': '/ca/root.crt' if not USE_HTTP_MODE else None
                }
                if USE_HTTP_MODE:
                    payload['error'] = 'Managed CA not available in HTTP mode'
                response_code = 200 if (payload['managed'] or USE_HTTP_MODE) else 503
                self.send_response(response_code)
                self._set_headers()
                self.end_headers()
                try:
                    self.wfile.write(json.dumps(payload).encode('utf-8'))
                except Exception as info_err:
                    log("Failed to write CA status payload: {}".format(info_err), level="ERROR")
                record_request_event('GET', '/ca/server-info.json', response_code, note='ca-info', client=_get_client_ip(self))
                return
            if self.path.startswith("/?code="):
                try:
                    auth_code = self.path.split('=')[1].split('&')[0]
                except IndexError as e:
                    log("Invalid authorization code path format: {}".format(self.path), level="ERROR")
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    try:
                        self.wfile.write("Invalid authorization code format. Please try again.".encode())
                    except Exception:
                        pass
                    return
                try:
                    auth_code = requests.utils.unquote(auth_code)
                except Exception as e:
                    log("Error unquoting authorization code: {}".format(e), level="ERROR")
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    try:
                        self.wfile.write("Invalid authorization code format. Please try again.".encode())
                    except Exception:
                        pass
                    return
                log("Received authorization code: {}".format(_mask_token_value(auth_code)), level="DEBUG")
                if oauth_is_valid_authorization_code(auth_code, log):
                    try:
                        token_response = exchange_code_for_token(auth_code)
                        if 'access_token' not in token_response:
                            if token_response.get("status") == "error":
                                self.send_response(400)
                                self.send_header('Content-type', 'text/html')
                                self.end_headers()
                                self.wfile.write(token_response["message"].encode())
                                return
                            raise ValueError("Access token not found in response.")
                    except Exception as e:
                        log("Error during token exchange: {}".format(e))
                        self.send_response(500)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write("An error occurred during authentication. Please try again.".encode())
                    else:
                        log("Token response: {}".format(_mask_sensitive_dict(token_response)), level="DEBUG")
                    if 'access_token' in token_response:
                        if shared_save_gmail_token(token_response, log=log, medi_config=medi):
                            # Success - continue with response
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write("Authentication successful. You can close this window now.".encode())

                        # Only launch webapp if not in Gmail send-only mode
                        global httpd
                        if httpd is not None and not getattr(httpd, 'gmail_send_only_mode', False):
                            initiate_link_retrieval(config)
                        else:
                            # For Gmail send-only: just signal completion
                            log("Gmail send-only authentication complete. Server will shutdown after token poll.")
                            shutdown_event.set()
                    else:
                        log("Authentication failed with response: {}".format(_mask_sensitive_dict(token_response)))
                        if 'error' in token_response:
                            error_description = token_response.get('error_description', 'No description provided.')
                            log("Error details: {}".format(error_description))
                        if token_response.get('error') == 'invalid_grant':
                            log("Invalid grant error encountered. Authorization code: {}, Response: {}".format(_mask_token_value(auth_code), _mask_sensitive_dict(token_response)), level="DEBUG")
                            check_invalid_grant_causes(auth_code)
                            shared_clear_token_cache(log=log, medi_config=medi)
                            user_message = "Authentication failed: Invalid or expired authorization code. Please try again."
                        else:
                            user_message = "Authentication failed. Please check the logs for more details."
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(user_message.encode())
                        shutdown_event.set()
                else:
                    log("Invalid authorization code format: {}".format(_mask_token_value(auth_code)), level="DEBUG")
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    try:
                        self.wfile.write("Invalid authorization code format. Please try again.".encode())
                    except Exception:
                        pass
                    shutdown_event.set()
            elif self.path == '/downloaded-emails':
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                downloaded_emails = load_downloaded_emails()
                response = json.dumps({"downloadedEmails": list(downloaded_emails)})
                try:
                    self.wfile.write(response.encode('utf-8'))
                except OSError as e:
                    if _is_expected_disconnect(e):
                        self.close_connection = True
                    else:
                        raise
            elif self.path == '/':
                # Serve friendly root status page
                # Detect Firefox from User-Agent
                user_agent = self.headers.get('User-Agent', '')
                is_firefox = 'Firefox/' in user_agent
                
                # Run Firefox certificate diagnostic if Firefox detected (skip in HTTP mode)
                firefox_diagnosis = None
                if not USE_HTTP_MODE and is_firefox and FIREFOX_CERT_DIAG_AVAILABLE:
                    try:
                        firefox_path = medi.get('firefox_path') or medi.get('browser_path')
                        firefox_diagnosis = diagnose_firefox_certificate_exceptions(
                            cert_file=cert_file,
                            server_port=server_port,
                            firefox_path=firefox_path,
                            log=log
                        )
                    except Exception as diag_err:
                        log("Error running Firefox diagnostic for root page: {}".format(diag_err), level="DEBUG")
                        # Continue without diagnosis - page will still render
                
                try:
                    safe_status = get_safe_status()
                    cert_info = get_certificate_summary(cert_file) if not USE_HTTP_MODE else None
                    ca_payload = {
                        'mode': CERT_MODE,
                        'managed': is_managed_ca_active() if not USE_HTTP_MODE else False,
                        'status': get_managed_ca_status() if not USE_HTTP_MODE else {}
                    }
                    root_html = html_build_root_status_html(
                        safe_status,
                        cert_info,
                        RECENT_REQUESTS,
                        server_port,
                        firefox_diagnosis=firefox_diagnosis,
                        ca_details=ca_payload,
                        use_http_mode=USE_HTTP_MODE
                    )
                except Exception as e:
                    log("Error building root status HTML: {}".format(e))
                    root_html = html_build_fallback_status_html(server_port)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(root_html.encode('utf-8'))
                except OSError as e:
                    if _is_expected_disconnect(e):
                        self.close_connection = True
                    else:
                        raise
                record_request_event('GET', '/', 200, note='root-page', client=_get_client_ip(self))
                return
            else:
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                try:
                    server_msg = b'HTTP server is running.' if USE_HTTP_MODE else b'HTTPS server is running.'
                    self.wfile.write(server_msg)
                except OSError as e:
                    if _is_expected_disconnect(e):
                        self.close_connection = True
                    else:
                        raise
        except IndexError as e:
            log("IndexError in do_GET for path {}: {}".format(self.path, e), level="ERROR")
            try:
                self.send_response(400)
                self._set_headers()
                self.end_headers()
                error_response = json.dumps({"status": "error", "message": "Invalid request path format"})
                self.wfile.write(error_response.encode('utf-8'))
            except Exception:
                pass
        except OSError as e:
            from MediLink.gmail_http_utils import _is_expected_disconnect
            if _is_expected_disconnect(e):
                log("Client disconnected during GET request: {}".format(e), level="DEBUG")
                self.close_connection = True
            else:
                log("Connection error in GET request: {} - This usually indicates a network error, client disconnect, or socket issue on Windows XP".format(e), level="ERROR")
                send_error_response(self, 500, "Connection error", log_fn=log, error_details=str(e))
        except Exception as e:
            log_request_error(e, self.path, "GET", log, headers=self.headers)
            send_error_response(self, 500, "Internal server error", log_fn=log, error_details=str(e))

# Plain HTTP Request Handler (no SSL) for HTTP mode
class PlainHTTPRequestHandler(BaseHTTPRequestHandler, _RequestHandlerMixin):
    """Plain HTTP request handler for use_http_mode. Inherits all handler methods from mixin."""
    # Overrides to mask Python/BaseHTTP version
    server_version = "MediLink/1.0"
    sys_version = ""

    # Disable DNS lookups for performance and to avoid timeouts on some networks
    def address_string(self):
        return str(self.client_address[0])

    def handle_one_request(self):
        try:
            return BaseHTTPRequestHandler.handle_one_request(self)
        except Exception as e:
            # Check if this is a TLS handshake attempt on HTTP server
            error_str = str(e).lower()
            if 'bad request syntax' in error_str or 'bad request version' in error_str:
                # Likely a TLS handshake attempt on HTTP server - log as warning
                log("TLS handshake attempt detected on HTTP server (client trying HTTPS). "
                    "This is expected if webapp hasn't been updated in Google Apps Script yet.", level="WARNING")
            # INSTRUMENTATION POINT: Log exceptions with full traceback to diagnose server crashes.
            raise

# Conditional RequestHandler: use PlainHTTPRequestHandler in HTTP mode, SSLRequestHandler in HTTPS mode
if USE_HTTP_MODE:
    class RequestHandler(PlainHTTPRequestHandler):
        pass
else:
    class RequestHandler(SSLRequestHandler, _RequestHandlerMixin):
        # INSTRUMENTATION POINT: Log incoming connections (client address) to track connection attempts.
        # Also log exceptions caught during request handling to identify server-side errors.
        def handle_one_request(self):
            try:
                return SSLRequestHandler.handle_one_request(self)
            except Exception as e:
                # INSTRUMENTATION POINT: Log exceptions with full traceback to diagnose server crashes.
                raise

    def do_POST(self):
        """Handle POST requests with comprehensive exception handling to prevent server crashes."""
        from MediLink.gmail_http_utils import (
            parse_content_length, read_post_data, parse_json_data,
            send_error_response, safe_write_response, log_request_error
        )
        try:
            if self.path == '/download':
                set_phase('processing')
                try:
                    content_length = parse_content_length(self.headers, log_fn=log)
                except (KeyError, ValueError) as e:
                    send_error_response(self, 400, "Missing or invalid Content-Length header", log_fn=log, error_details=str(e))
                    return
                post_data = read_post_data(self, content_length, log_fn=log)
                if post_data is None:
                    return  # Client disconnected
                try:
                    data = parse_json_data(post_data, log_fn=log)
                except (ValueError, UnicodeDecodeError) as e:
                    send_error_response(self, 400, "Invalid request format", log_fn=log, error_details=str(e))
                    return
                links = data.get('links', [])
                log("Received links: {}".format(links), level="DEBUG")
                try:
                    print("[Handshake] Received {0} link(s) from webapp".format(len(links)))
                except Exception:
                    pass
                try:
                    set_counts(links_received=len(links))
                except Exception:
                    pass
                file_ids = [link.get('fileId', None) for link in links if link.get('fileId')]
                log("File IDs received from client: {}".format(file_ids), level="DEBUG")
                set_phase('downloading')
                try:
                    download_docx_files(links)
                except Exception as e:
                    set_phase('error')
                    set_error(str(e))
                # Only delete files that actually downloaded successfully
                downloaded_names = load_downloaded_emails()
                successful_ids = []
                try:
                    name_to_id = { (link.get('filename') or ''): link.get('fileId') for link in links if link.get('fileId') }
                    for name in downloaded_names:
                        fid = name_to_id.get(name)
                        if fid:
                            successful_ids.append(fid)
                except Exception as e:
                    log("Error computing successful file IDs for cleanup: {}".format(e))
                    successful_ids = file_ids  # Fallback: attempt all provided IDs
                try:
                    set_counts(files_to_delete=len(successful_ids))
                except Exception:
                    pass
                # Trigger cleanup in Apps Script with auth
                try:
                    cleanup_ok = False
                    if successful_ids:
                        ok = send_delete_request_to_gas(successful_ids)
                        if ok:
                            set_phase('cleanup_confirmed')
                            try:
                                set_counts(files_deleted=len(successful_ids))
                            except Exception:
                                pass
                            cleanup_ok = True
                        else:
                            set_phase('cleanup_triggered')
                            set_error('Cleanup request not confirmed')
                    else:
                        log("No successful file IDs to delete after download.")
                        set_phase('done')
                        cleanup_ok = True  # nothing to delete -> safe
                except Exception as e:
                    log("Cleanup trigger failed: {}".format(e))
                    set_phase('error')
                    set_error(str(e))
                    cleanup_ok = False
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                try:
                    set_safe_to_close(bool(cleanup_ok))
                except Exception:
                    pass
                response = json.dumps({"status": "success", "message": "All files downloaded", "fileIds": successful_ids, "safeToClose": bool(cleanup_ok)})
                safe_write_response(self, response)
                try:
                    print("[Handshake] Completed. Returning success for {0} fileId(s)".format(len(successful_ids)))
                except Exception:
                    pass
                shutdown_event.set()
                bring_window_to_foreground()
                record_request_event('POST', '/download', 200, note='download', client=_get_client_ip(self))
                return
            elif self.path == '/shutdown':
                log("Shutdown request received.")
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                response = json.dumps({"status": "success", "message": "Server is shutting down."})
                safe_write_response(self, response)
                shutdown_event.set()
                record_request_event('POST', '/shutdown', 200, note='shutdown', client=_get_client_ip(self))
                return
            elif self.path == '/delete-files':
                try:
                    content_length = parse_content_length(self.headers, log_fn=log)
                except (KeyError, ValueError) as e:
                    send_error_response(self, 400, "Missing or invalid Content-Length header", log_fn=log, error_details=str(e))
                    return
                post_data = read_post_data(self, content_length, log_fn=log)
                if post_data is None:
                    return  # Client disconnected
                try:
                    data = parse_json_data(post_data, log_fn=log)
                except (ValueError, UnicodeDecodeError) as e:
                    send_error_response(self, 400, "Invalid request format", log_fn=log, error_details=str(e))
                    return
                file_ids = data.get('fileIds', [])
                log("File IDs to delete received from client: {}".format(file_ids))
                if not isinstance(file_ids, list):
                    send_error_response(self, 400, "Invalid fileIds parameter.", log_fn=log)
                    return
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                response = json.dumps({"status": "success", "message": "Files deleted successfully."})
                safe_write_response(self, response)
                record_request_event('POST', '/delete-files', 200, note='cleanup', client=_get_client_ip(self))
                return
            elif self.path == '/ca/enable':
                try:
                    content_length = parse_content_length(self.headers, log_fn=log)
                except (KeyError, ValueError) as e:
                    send_error_response(self, 400, "Missing or invalid Content-Length header", log_fn=log, error_details=str(e))
                    return
                post_data = read_post_data(self, content_length, log_fn=log)
                if post_data is None:
                    return
                try:
                    data = parse_json_data(post_data, log_fn=log)
                except (ValueError, UnicodeDecodeError) as e:
                    send_error_response(self, 400, "Invalid request format", log_fn=log, error_details=str(e))
                    return
                desired_mode = _str_or_default(data.get('mode'), 'managed_ca').lower()
                if desired_mode not in ('managed_ca', 'self_signed'):
                    desired_mode = 'managed_ca'
                extra_fields = {}
                if desired_mode == 'managed_ca':
                    extra_fields = {
                        'profile': MANAGED_CA_PROFILE_NAME,
                        'root_subject': MANAGED_CA_ROOT_SUBJECT,
                        'server_subject': MANAGED_CA_SERVER_SUBJECT,
                        'san': MANAGED_CA_SAN_LIST,
                        'root_valid_days': MANAGED_CA_ROOT_VALID_DAYS,
                        'server_valid_days': MANAGED_CA_SERVER_VALID_DAYS
                    }
                success, error = _update_certificate_provider_mode(desired_mode, extra_fields)
                response = {
                    'success': bool(success),
                    'mode': CERT_MODE,
                    'managed': is_managed_ca_active()
                }
                if error:
                    response['error'] = error
                status_code = 200 if success else 500
                self.send_response(status_code)
                self._set_headers()
                self.end_headers()
                safe_write_response(self, json.dumps(response))
                record_request_event('POST', '/ca/enable', status_code, note='ca-enable', client=_get_client_ip(self))
                return
            else:
                self.send_response(404)
                self._set_headers()
                self.end_headers()
        except KeyError as e:
            send_error_response(self, 400, "Missing required header: {}".format(str(e)), log_fn=log, error_details=str(e))
        except (ValueError, TypeError) as e:
            # Note: json.JSONDecodeError doesn't exist in Python 3.4.4; json.loads raises ValueError
            send_error_response(self, 400, "Invalid request format: {}".format(str(e)), log_fn=log, error_details=str(e))
        except OSError as e:
            from MediLink.gmail_http_utils import _is_expected_disconnect
            if _is_expected_disconnect(e):
                log("Client disconnected during POST request handling: {}".format(e), level="DEBUG")
                self.close_connection = True
            else:
                log("Connection error in POST request: {} - This usually indicates a network error, client disconnect, or socket issue on Windows XP".format(e), level="ERROR")
                send_error_response(self, 500, "Connection error", log_fn=log, error_details=str(e))
        except Exception as e:
            log_request_error(e, self.path, "POST", log, headers=self.headers)
            send_error_response(self, 500, "Internal server error", log_fn=log, error_details=str(e))

    def do_GET(self):
        """Handle GET requests with comprehensive exception handling to prevent server crashes."""
        # INSTRUMENTATION POINT: Log GET requests (path, headers) to track which endpoints are being accessed.
        from MediLink.gmail_http_utils import (
            _is_expected_disconnect,
            send_error_response, log_request_error
        )
        try:
            log("Full request path: {}".format(self.path), level="DEBUG")
            if self.path == '/_health':
                try:
                    print("[Health] Probe OK")
                except Exception:
                    pass
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                try:
                    self.wfile.write(json.dumps({"status": "ok"}).encode('ascii'))
                except Exception:
                    try:
                        self.wfile.write(b'{"status":"ok"}')
                    except OSError as e:
                        if _is_expected_disconnect(e):
                            self.close_connection = True
                        else:
                            raise
                record_request_event('GET', '/_health', 200, note='health-probe', client=_get_client_ip(self))
                return
            elif self.path.startswith('/_selftest'):
                # Run self-tests to verify server connectivity and SSL configuration
                # This endpoint helps diagnose Firefox/XP connectivity issues
                self.send_response(200)
                
                # Check if HTML format is requested
                want_html = 'html=1' in self.path or 'format=html' in self.path
                
                if DIAGNOSTICS_AVAILABLE and _run_all_selftests:
                    try:
                        # Run self-tests (skip network tests since we ARE the server)
                        selftest_results = _run_all_selftests(
                            port=server_port,
                            cert_file=cert_file,
                            include_network=False  # Can't test ourselves while handling request
                        )
                        # Add note about network tests
                        selftest_results['note'] = 'Network tests skipped (cannot self-test while handling request). Run from external script for full test.'
                    except Exception as st_err:
                        log("Error running self-tests: {}".format(st_err), level="ERROR")
                        selftest_results = {
                            'error': str(st_err),
                            'tests': {},
                            'summary': {'total': 0, 'passed': 0, 'failed': 0, 'all_passed': False}
                        }
                else:
                    selftest_results = {
                        'error': 'Diagnostics module not available',
                        'tests': {},
                        'summary': {'total': 0, 'passed': 0, 'failed': 0, 'all_passed': False}
                    }
                
                if want_html:
                    # Build simple HTML response
                    html_parts = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>MediLink Self-Test</title>',
                                  '<style>body{font-family:Arial,sans-serif;padding:20px;background:#f5f3e8;}',
                                  '.container{max-width:800px;margin:0 auto;background:white;padding:24px;border:1px solid #ccc;}',
                                  'h1{color:#3B2323;}.pass{color:#1f5132;}.fail{color:#dc2626;}',
                                  'pre{background:#f0f0f0;padding:12px;overflow:auto;}</style></head><body>',
                                  '<div class="container"><h1>MediLink Self-Test Results</h1>']
                    
                    summary = selftest_results.get('summary', {})
                    if summary.get('all_passed'):
                        html_parts.append('<p class="pass"><strong>All tests passed</strong></p>')
                    else:
                        html_parts.append('<p class="fail"><strong>{} of {} tests failed</strong></p>'.format(
                            summary.get('failed', 0), summary.get('total', 0)))
                    
                    if selftest_results.get('note'):
                        html_parts.append('<p><em>{}</em></p>'.format(selftest_results['note']))
                    
                    html_parts.append('<h2>Test Results</h2><pre>{}</pre>'.format(
                        json.dumps(selftest_results, indent=2, default=str)))
                    
                    html_parts.append('<p><a href="/_diag?html=1">Full Diagnostics</a> | ')
                    html_parts.append('<a href="/_troubleshoot">Troubleshooting Guide</a> | ')
                    html_parts.append('<a href="/">Server Status</a></p>')
                    html_parts.append('</div></body></html>')
                    
                    response_body = ''.join(html_parts)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                else:
                    response_body = json.dumps(selftest_results, indent=2, default=str)
                    self.send_header('Content-type', 'application/json')
                
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                
                try:
                    self.wfile.write(response_body.encode('utf-8'))
                except Exception as write_err:
                    log("Failed to write selftest response: {}".format(write_err))
                
                record_request_event('GET', '/_selftest', 200, note='selftest', client=_get_client_ip(self))
                return
            elif self.path == '/status':
                maybe_warn_secure_idle()
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                try:
                    payload = json.dumps(get_safe_status())
                except Exception:
                    payload = '{}'
                try:
                    self.wfile.write(payload.encode('ascii'))
                except Exception:
                    try:
                        self.wfile.write(payload.encode('utf-8'))
                    except Exception:
                        try:
                            self.wfile.write(payload.encode('utf-8', errors='ignore'))
                        except OSError as e:
                            if _is_expected_disconnect(e):
                                self.close_connection = True
                            else:
                                raise
                record_request_event('GET', '/status', 200, note='status', client=_get_client_ip(self))
                return
            elif self.path.startswith('/_diag'):
                # Check if HTML format is requested (browser access)
                want_html = 'html=1' in self.path or 'format=html' in self.path
                include_full = 'full=1' in self.path or 'refresh=1' in self.path
                
                # Build basic diagnostics payload
                diag_payload = build_diagnostics_payload()
                
                # Run comprehensive diagnostics if available and requested
                if DIAGNOSTICS_AVAILABLE and include_full:
                    try:
                        # Enable auto_fix for runtime diagnostics
                        # User will be notified if server restart is needed
                        full_diag = run_connection_diagnostics(
                            cert_file=cert_file,
                            key_file=key_file,
                            server_port=server_port,
                            auto_fix=True,  # Enable auto-fix during runtime
                            openssl_cnf=get_openssl_cnf()
                        )
                        diag_payload['fullDiagnostics'] = full_diag
                        
                        # If certificate was auto-fixed, add prominent notification
                        if full_diag.get('user_action_required') and full_diag['user_action_required'].get('requires_restart'):
                            diag_payload['certificateAutoFixed'] = True
                            diag_payload['restartRequired'] = True
                        
                        diag_payload['firefoxNotes'] = get_firefox_xp_compatibility_notes()
                        diag_payload['browserHints'] = BROWSER_DIAGNOSTIC_HINTS
                    except Exception as full_diag_err:
                        log("Error running full diagnostics: {}".format(full_diag_err), level="WARNING")
                        diag_payload['fullDiagnosticsError'] = str(full_diag_err)
                
                self.send_response(200)
                
                if want_html and DIAGNOSTICS_AVAILABLE:
                    # Return HTML diagnostics page
                    try:
                        if 'fullDiagnostics' not in diag_payload:
                            # Enable auto_fix for HTML diagnostics view
                            full_diag = run_connection_diagnostics(
                                cert_file=cert_file,
                                key_file=key_file,
                                server_port=server_port,
                                auto_fix=True,  # Enable auto-fix during runtime
                                openssl_cnf=get_openssl_cnf()
                            )
                            # Check if certificate was auto-fixed
                            if full_diag.get('user_action_required') and full_diag['user_action_required'].get('requires_restart'):
                                diag_payload['certificateAutoFixed'] = True
                                diag_payload['restartRequired'] = True
                        else:
                            full_diag = diag_payload['fullDiagnostics']
                        # Pass auto-fix flags to HTML builder
                        diag_html = html_build_diagnostics_html(full_diag, server_port, certificate_auto_fixed=diag_payload.get('certificateAutoFixed', False), restart_required=diag_payload.get('restartRequired', False))
                    except Exception as html_err:
                        log("Error building diagnostics HTML: {}".format(html_err), level="WARNING")
                        diag_html = "<html><body><h1>Diagnostics</h1><pre>{}</pre></body></html>".format(
                            json.dumps(diag_payload, indent=2)
                        )
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.send_header('Access-Control-Allow-Private-Network', 'true')
                    self.end_headers()
                    try:
                        self.wfile.write(diag_html.encode('utf-8'))
                    except Exception as write_err:
                        log("Failed to write diagnostics HTML: {}".format(write_err))
                else:
                    # Return JSON diagnostics
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps(diag_payload).encode('utf-8'))
                    except Exception as write_err:
                        log("Failed to write diagnostics payload: {}".format(write_err))
                record_request_event('GET', '/_diag', 200, note='diagnostics', client=_get_client_ip(self))
                return
            elif self.path.startswith('/_troubleshoot'):
                # Comprehensive troubleshooting page
                try:
                    troubleshoot_html = self._build_troubleshoot_html()
                except Exception as ts_err:
                    log("Error building troubleshoot page: {}".format(ts_err), level="ERROR")
                    troubleshoot_html = html_build_simple_error_html("Troubleshooting Error", str(ts_err), server_port)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(troubleshoot_html.encode('utf-8'))
                except Exception as write_err:
                    log("Failed to write troubleshoot page: {}".format(write_err))
                record_request_event('GET', '/_troubleshoot', 200, note='troubleshoot', client=_get_client_ip(self))
                return
            elif self.path == '/_cert_download' or self.path.startswith('/_cert_download'):
                # Serve certificate file for download (check before /_cert to avoid path matching conflict)
                try:
                    if os.path.exists(cert_file):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/x-x509-ca-cert')
                        self.send_header('Content-Disposition', 'attachment; filename="medilink-local.crt"')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        with open(cert_file, 'rb') as f:
                            self.wfile.write(f.read())
                        record_request_event('GET', '/_cert_download', 200, note='cert-download', client=_get_client_ip(self))
                    else:
                        self.send_response(404)
                        self._set_headers()
                        self.end_headers()
                        self.wfile.write(b'Certificate file not found')
                        record_request_event('GET', '/_cert_download', 404, note='cert-not-found', client=_get_client_ip(self))
                except Exception as e:
                    log("Error serving certificate download: {}".format(e), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(b'Error serving certificate file')
                    except Exception:
                        pass
                return
            elif self.path == '/_cert_fingerprint':
                # Return certificate fingerprint as JSON (for diagnostics) - check before /_cert to avoid path matching conflict
                try:
                    fingerprint = http_get_certificate_fingerprint(cert_file, log=log)
                    cert_info = get_certificate_summary(cert_file)
                    response_data = {
                        'fingerprint': fingerprint,
                        'certificate': cert_info,
                        'download_url': '/_cert_download'
                    }
                    self.send_response(200)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                    record_request_event('GET', '/_cert_fingerprint', 200, note='cert-fingerprint', client=_get_client_ip(self))
                except Exception as e:
                    log("Error serving certificate fingerprint: {}".format(e), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                    except Exception:
                        pass
                return
            elif self.path == '/_cert_diagnose_firefox':
                # Diagnose Firefox certificate exceptions - check before /_cert to avoid path matching conflict
                try:
                    if not FIREFOX_CERT_DIAG_AVAILABLE:
                        response_data = {'error': 'Firefox certificate diagnostics not available'}
                    else:
                        # Try to get Firefox path from config
                        firefox_path = medi.get('firefox_path') or medi.get('browser_path')
                        diagnosis = diagnose_firefox_certificate_exceptions(
                            cert_file=cert_file,
                            server_port=server_port,
                            firefox_path=firefox_path,
                            log=log
                        )
                        response_data = diagnosis
                    
                    self.send_response(200)
                    self._set_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                    record_request_event('GET', '/_cert_diagnose_firefox', 200, note='cert-diagnose-firefox', client=_get_client_ip(self))
                except Exception as e:
                    log("Error serving Firefox certificate diagnosis: {}".format(e), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                    except Exception:
                        pass
                return
            elif self.path == '/_cert' or self.path.startswith('/_cert'):
                try:
                    cert_info = get_certificate_summary(cert_file)
                    fingerprint = http_get_certificate_fingerprint(cert_file, log=log)
                    
                    # Detect browser from User-Agent header for tailored instructions
                    browser_info = None
                    try:
                        user_agent = self.headers.get('User-Agent', '')
                        if 'Firefox/52' in user_agent and 'Windows NT 5' in user_agent:
                            browser_info = {'name': 'Firefox', 'version': '52', 'isWindowsXP': True}
                        elif 'Firefox/' in user_agent:
                            # Try to extract Firefox version
                            match = re.search(r'Firefox/(\d+)', user_agent)
                            if match:
                                version = match.group(1)
                                is_xp = 'Windows NT 5' in user_agent
                                browser_info = {'name': 'Firefox', 'version': version, 'isWindowsXP': is_xp}
                    except Exception as ua_err:
                        log("Error detecting browser from User-Agent: {}".format(ua_err), level="DEBUG")
                    
                    cert_html = html_build_cert_info_html(cert_info, fingerprint=fingerprint, browser_info=browser_info, server_port=server_port)
                except Exception as cert_err:
                    log("Error generating certificate info page: {}".format(cert_err), level="ERROR")
                    # Provide a fallback HTML page on error
                    cert_html = html_build_fallback_cert_html(str(cert_err), server_port)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(cert_html.encode('utf-8'))
                except Exception as write_err:
                    log("Failed to write cert info payload: {}".format(write_err))
                record_request_event('GET', '/_cert', 200, note='cert-info', client=_get_client_ip(self))
                return
            elif self.path.startswith('/ca/root.crt'):
                if not is_managed_ca_active():
                    self.send_response(404)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': 'Managed CA mode disabled'}).encode('utf-8'))
                    except Exception:
                        pass
                    record_request_event('GET', '/ca/root.crt', 404, note='ca-root-missing', client=_get_client_ip(self))
                    return
                root_path = CA_PROFILE.get('root_cert_path')
                if not root_path or not os.path.exists(root_path):
                    try:
                        certificate_authority.ensure_root(CA_PROFILE, log=log, subprocess_module=subprocess)
                        root_path = CA_PROFILE.get('root_cert_path')
                    except Exception as root_err:
                        log("Unable to ensure managed CA root before download: {}".format(root_err), level="ERROR")
                if not root_path or not os.path.exists(root_path):
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': 'Managed CA root not available'}).encode('utf-8'))
                    except Exception:
                        pass
                    record_request_event('GET', '/ca/root.crt', 500, note='ca-root-error', client=_get_client_ip(self))
                    return
                try:
                    with open(root_path, 'rb') as root_file:
                        root_bytes = root_file.read()
                except Exception as read_err:
                    log("Failed to read managed CA root for download: {}".format(read_err), level="ERROR")
                    self.send_response(500)
                    self._set_headers()
                    self.end_headers()
                    try:
                        self.wfile.write(json.dumps({'error': 'Unable to read managed root'}).encode('utf-8'))
                    except Exception:
                        pass
                    record_request_event('GET', '/ca/root.crt', 500, note='ca-root-read-failed', client=_get_client_ip(self))
                    return
                self.send_response(200)
                self.send_header('Content-type', 'application/x-x509-ca-cert')
                self.send_header('Content-Disposition', 'attachment; filename="medilink-managed-root.crt"')
                self.send_header('Cache-Control', 'no-store, max-age=0')
                self.send_header('Content-Length', str(len(root_bytes)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(root_bytes)
                except Exception as write_err:
                    log("Failed to stream managed CA root: {}".format(write_err), level="ERROR")
                record_request_event('GET', '/ca/root.crt', 200, note='ca-root-download', client=_get_client_ip(self))
                return
            elif self.path.startswith('/ca/server-info'):
                refresh = 'refresh=1' in self.path or 'full=1' in self.path
                status = get_managed_ca_status(refresh=refresh)
                payload = {
                    'mode': CERT_MODE,
                    'managed': is_managed_ca_active(),
                    'status': status,
                    'download': '/ca/root.crt'
                }
                response_code = 200 if payload['managed'] else 503
                self.send_response(response_code)
                self._set_headers()
                self.end_headers()
                try:
                    self.wfile.write(json.dumps(payload).encode('utf-8'))
                except Exception as info_err:
                    log("Failed to write CA status payload: {}".format(info_err), level="ERROR")
                record_request_event('GET', '/ca/server-info.json', response_code, note='ca-info', client=_get_client_ip(self))
                return
            if self.path.startswith("/?code="):
                try:
                    auth_code = self.path.split('=')[1].split('&')[0]
                except IndexError as e:
                    log("Invalid authorization code path format: {}".format(self.path), level="ERROR")
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    try:
                        self.wfile.write("Invalid authorization code format. Please try again.".encode())
                    except Exception:
                        pass
                    return
                try:
                    auth_code = requests.utils.unquote(auth_code)
                except Exception as e:
                    log("Error unquoting authorization code: {}".format(e), level="ERROR")
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    try:
                        self.wfile.write("Invalid authorization code format. Please try again.".encode())
                    except Exception:
                        pass
                    return
                log("Received authorization code: {}".format(_mask_token_value(auth_code)), level="DEBUG")
                if oauth_is_valid_authorization_code(auth_code, log):
                    try:
                        token_response = exchange_code_for_token(auth_code)
                        if 'access_token' not in token_response:
                            if token_response.get("status") == "error":
                                self.send_response(400)
                                self.send_header('Content-type', 'text/html')
                                self.end_headers()
                                self.wfile.write(token_response["message"].encode())
                                return
                            raise ValueError("Access token not found in response.")
                    except Exception as e:
                        log("Error during token exchange: {}".format(e))
                        self.send_response(500)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write("An error occurred during authentication. Please try again.".encode())
                    else:
                        log("Token response: {}".format(_mask_sensitive_dict(token_response)), level="DEBUG")
                    if 'access_token' in token_response:
                        if shared_save_gmail_token(token_response, log=log, medi_config=medi):
                            # Success - continue with response
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write("Authentication successful. You can close this window now.".encode())

                        # Only launch webapp if not in Gmail send-only mode
                        global httpd
                        if httpd is not None and not getattr(httpd, 'gmail_send_only_mode', False):
                            initiate_link_retrieval(config)
                        else:
                            # For Gmail send-only: just signal completion
                            log("Gmail send-only authentication complete. Server will shutdown after token poll.")
                            shutdown_event.set()
                    else:
                        log("Authentication failed with response: {}".format(_mask_sensitive_dict(token_response)))
                        if 'error' in token_response:
                            error_description = token_response.get('error_description', 'No description provided.')
                            log("Error details: {}".format(error_description))
                        if token_response.get('error') == 'invalid_grant':
                            log("Invalid grant error encountered. Authorization code: {}, Response: {}".format(_mask_token_value(auth_code), _mask_sensitive_dict(token_response)), level="DEBUG")
                            check_invalid_grant_causes(auth_code)
                            shared_clear_token_cache(log=log, medi_config=medi)
                            user_message = "Authentication failed: Invalid or expired authorization code. Please try again."
                        else:
                            user_message = "Authentication failed. Please check the logs for more details."
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(user_message.encode())
                        shutdown_event.set()
                else:
                    log("Invalid authorization code format: {}".format(_mask_token_value(auth_code)), level="DEBUG")
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    try:
                        self.wfile.write("Invalid authorization code format. Please try again.".encode())
                    except Exception:
                        pass
                    shutdown_event.set()
            elif self.path == '/downloaded-emails':
                self.send_response(200)
                self._set_headers()
                self.end_headers()
                downloaded_emails = load_downloaded_emails()
                response = json.dumps({"downloadedEmails": list(downloaded_emails)})
                try:
                    self.wfile.write(response.encode('utf-8'))
                except OSError as e:
                    if _is_expected_disconnect(e):
                        self.close_connection = True
                    else:
                        raise
            elif self.path == '/':
                # Serve friendly root status page
                # Detect Firefox from User-Agent
                user_agent = self.headers.get('User-Agent', '')
                is_firefox = 'Firefox/' in user_agent
                
                # Run Firefox certificate diagnostic if Firefox detected
                firefox_diagnosis = None
                if is_firefox and FIREFOX_CERT_DIAG_AVAILABLE:
                    try:
                        firefox_path = medi.get('firefox_path') or medi.get('browser_path')
                        firefox_diagnosis = diagnose_firefox_certificate_exceptions(
                            cert_file=cert_file,
                            server_port=server_port,
                            firefox_path=firefox_path,
                            log=log
                        )
                    except Exception as diag_err:
                        log("Error running Firefox diagnostic for root page: {}".format(diag_err), level="DEBUG")
                        # Continue without diagnosis - page will still render
                
                try:
                    safe_status = get_safe_status()
                    cert_info = get_certificate_summary(cert_file)
                    ca_payload = {
                        'mode': CERT_MODE,
                        'managed': is_managed_ca_active(),
                        'status': get_managed_ca_status()
                    }
                    root_html = html_build_root_status_html(
                        safe_status,
                        cert_info,
                        RECENT_REQUESTS,
                        server_port,
                        firefox_diagnosis=firefox_diagnosis,
                        ca_details=ca_payload,
                        use_http_mode=USE_HTTP_MODE
                    )
                except Exception as e:
                    log("Error building root status HTML: {}".format(e))
                    root_html = html_build_fallback_status_html(server_port)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.end_headers()
                try:
                    self.wfile.write(root_html.encode('utf-8'))
                except OSError as e:
                    if _is_expected_disconnect(e):
                        self.close_connection = True
                    else:
                        raise
                record_request_event('GET', '/', 200, note='root-page', client=_get_client_ip(self))
                return
            else:
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                try:
                    self.wfile.write(b'HTTPS server is running.')
                except OSError as e:
                    if _is_expected_disconnect(e):
                        self.close_connection = True
                    else:
                        raise
        except IndexError as e:
            log("IndexError in do_GET for path {}: {}".format(self.path, e), level="ERROR")
            try:
                self.send_response(400)
                self._set_headers()
                self.end_headers()
                error_response = json.dumps({"status": "error", "message": "Invalid request path format"})
                self.wfile.write(error_response.encode('utf-8'))
            except Exception:
                pass
        except OSError as e:
            from MediLink.gmail_http_utils import _is_expected_disconnect
            if _is_expected_disconnect(e):
                log("Client disconnected during GET request: {}".format(e), level="DEBUG")
                self.close_connection = True
            else:
                log("Connection error in GET request: {} - This usually indicates a network error, client disconnect, or socket issue on Windows XP".format(e), level="ERROR")
                send_error_response(self, 500, "Connection error", log_fn=log, error_details=str(e))
        except Exception as e:
            log_request_error(e, self.path, "GET", log, headers=self.headers)
            send_error_response(self, 500, "Internal server error", log_fn=log, error_details=str(e))

def generate_self_signed_cert(cert_path, key_path):
    """
    Ensure local HTTPS materials exist.

    When managed CA mode is enabled, delegate to certificate_authority helpers.
    Otherwise, fall back to the legacy self-signed generator.
    
    Returns early if HTTP mode is enabled (no certificates needed).
    """
    # Skip certificate generation in HTTP mode
    if USE_HTTP_MODE:
        log("Skipping certificate generation (HTTP mode enabled)", level="DEBUG")
        return
    
    global CA_STATUS_CACHE
    if MANAGED_CA_ENABLED and CA_PROFILE and certificate_authority:
        try:
            status = certificate_authority.ensure_managed_certificate(
                CA_PROFILE,
                log=log,
                subprocess_module=subprocess
            )
            CA_STATUS_CACHE = status or {}
            return status
        except Exception as ca_err:
            log("Managed CA ensure failed: {}. Falling back to self-signed certificates.".format(ca_err), level="WARNING")
    cert_days = medi.get('gmail_cert_days', DEFAULT_CERT_DAYS)
    http_generate_self_signed_cert(get_openssl_cnf(), cert_path, key_path, log, subprocess, cert_days)
    CA_STATUS_CACHE = {}
    return None

class SecureHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTPServer subclass that wraps accepted sockets with SSL.
    Threading prevents one slow handshake (e.g. browser trust prompt) from
    blocking subsequent requests (like the actual fetch).
    Supports both HTTP and HTTPS modes via use_http parameter.
    """
    daemon_threads = True  # Ensure threads exit with main thread

    def __init__(self, server_address, RequestHandlerClass, cert_file, key_file, log_fn, use_http=False):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.cert_file = cert_file
        self.key_file = key_file
        self.log_fn = log_fn
        self.use_http = use_http
        # Only create SSL context when not in HTTP mode
        if not use_http:
            from MediLink.gmail_http_utils import create_ssl_context_for_server
            self.context = create_ssl_context_for_server(cert_file, key_file, log_fn)
        else:
            self.context = None

    def get_request(self):
        """Override get_request to return raw socket. Handshake moved to handler thread."""
        client_sock, client_addr = self.socket.accept()
        # INSTRUMENTATION POINT: Log raw socket acceptance (client address) to track connection attempts.
        return client_sock, client_addr

def run_server():
    global httpd
    try:
        # INSTRUMENTATION POINT: Log server startup (port, cert/key paths) to verify server initialization.
        log("Attempting to start server on port " + str(server_port))
        
        # Skip certificate file checks in HTTP mode
        if not USE_HTTP_MODE:
            if not os.path.exists(cert_file):
                log("Error: Certificate file not found: " + cert_file)
            if not os.path.exists(key_file):
                log("Error: Key file not found: " + key_file)
        
        # Use our custom SecureHTTPServer instead of default HTTPServer
        # Pass use_http flag to server
        httpd = SecureHTTPServer(('0.0.0.0', server_port), RequestHandler, cert_file, key_file, log, use_http=USE_HTTP_MODE)
        httpd.gmail_send_only_mode = False  # Default: allow full webapp flow
        httpd.timeout = 30  # Request timeout
        
        # Log appropriate message based on mode
        if USE_HTTP_MODE:
            log("Starting HTTP server on port {}".format(server_port))
            try:
                print("[Server] HTTP server ready at http://{0}:{1}".format(SERVER_HOST, server_port))
            except Exception:
                pass
        else:
            log("Starting HTTPS server on port {}".format(server_port))
            try:
                print("[Server] HTTPS server ready at https://{0}:{1}".format(SERVER_HOST, server_port))
            except Exception:
                pass
        httpd.serve_forever()
    except Exception as e:
        global server_crashed
        server_crashed = True  # Mark that server has crashed
        import traceback
        tb_str = traceback.format_exc()
        
        # INSTRUMENTATION POINT: Log server crashes with full traceback to diagnose fatal errors.
        
        error_type = type(e).__name__
        error_msg = str(e)
        mode_str = "HTTP" if USE_HTTP_MODE else "HTTPS"
        error_msg_full = "{} server thread crashed: {}: {}".format(mode_str, error_type, error_msg)
        log(error_msg_full, level="ERROR")
        
        # Collect comprehensive diagnostic information
        diagnostic_info = {
            'error_type': error_type,
            'error_message': error_msg,
            'server_port': server_port,
            'cert_file_exists': os.path.exists(cert_file),
            'key_file_exists': os.path.exists(key_file),
            'server_thread_alive': False,
        }
        
        # Capture traceback once for logging and file writing
        tb_str = None
        try:
            tb_str = traceback.format_exc()
            log("Server thread crash traceback: {}".format(tb_str), level="ERROR")
            diagnostic_info['traceback'] = tb_str
        except Exception:
            pass
        
        # Log server state at time of crash
        try:
            status = get_safe_status()
            log("Server status at crash time: {}".format(status), level="ERROR")
            diagnostic_info['server_status'] = status
        except Exception:
            pass
        
        # Write traceback to file so error_reporter can include it in bundle
        if tb_str:
            try:
                trace_path = os.path.join(local_storage_path, 'traceback.txt')
                with open(trace_path, 'w') as f:
                    f.write(tb_str)
                log("Traceback saved to {}".format(trace_path), level="INFO")
            except Exception as trace_err:
                log("Failed to save traceback to file: {}".format(trace_err), level="WARNING")
        else:
            log("No traceback available to save", level="WARNING")
        
        # Automatically submit error report - error_reporter handles collection and submission
        report_submitted = False
        if _submit_support_bundle_email is not None:
            try:
                log("Submitting error report for server crash...", level="INFO")
                # Write diagnostic info to a temporary file for inclusion in bundle
                try:
                    diagnostic_file = os.path.join(local_storage_path, 'server_crash_diagnostics.json')
                    import json as json_module
                    with open(diagnostic_file, 'w') as df:
                        json_module.dump(diagnostic_info, df, indent=2)
                    log("Server crash diagnostic information saved to: {}".format(diagnostic_file), level="INFO")
                except Exception as diag_file_err:
                    log("Failed to save diagnostic file: {}".format(diag_file_err), level="WARNING")
                # submit_support_bundle_email() automatically collects bundle if zip_path is None
                # and handles online/offline submission, bundle size limits, etc.
                success = _submit_support_bundle_email(zip_path=None, include_traceback=True)
                report_submitted = success
                if success:
                    log("Error report submitted successfully for server crash", level="INFO")
                else:
                    log("Error report submission failed or queued for later submission", level="WARNING")
            except Exception as report_exc:
                log("Error report submission failed for server crash: {}".format(report_exc), level="WARNING")
        else:
            log("Support bundle reporter unavailable; cannot auto-submit crash diagnostics.", level="WARNING")
        
        # Display concise console message to user AFTER submission attempt
        try:
            print("\n" + "=" * 60)
            print("SERVER ERROR - HTTPS Server Thread Crashed")
            print("=" * 60)
            print("Error Type: {}".format(error_type))
            print("Error Message: {}".format(error_msg))
            if report_submitted:
                print("\nError report has been automatically submitted.")
            else:
                print("\nError report is being collected and will be submitted when possible.")
            print("Returning to main menu...")
            print("=" * 60 + "\n")
        except Exception:
            pass
        stop_server()

def stop_server():
    global httpd
    if httpd:
        log("Stopping HTTPS server.")
        # Close the server socket FIRST to interrupt serve_forever() blocking on accept()
        # This is critical - closing the socket will cause serve_forever() to exit
        try:
            if hasattr(httpd, 'socket') and httpd.socket:
                try:
                    httpd.socket.close()
                    log("Server socket closed.", level="DEBUG")
                except Exception as socket_close_err:
                    log("Error closing server socket: {}".format(socket_close_err), level="DEBUG")
        except Exception:
            pass
        # Now shutdown() should be quick since serve_forever() is exiting
        # But make it non-blocking with a timeout to prevent hanging
        try:
            from threading import Thread as ShutdownThread
            shutdown_done = Event()
            def _shutdown_in_thread():
                try:
                    httpd.shutdown()
                except Exception:
                    pass
                finally:
                    shutdown_done.set()
            shutdown_thread = ShutdownThread(target=_shutdown_in_thread, daemon=True)
            shutdown_thread.start()
            # Wait up to 2 seconds for shutdown to complete
            shutdown_done.wait(timeout=2)
            if not shutdown_done.is_set():
                log("Shutdown timed out, continuing anyway.", level="WARNING")
        except Exception as shutdown_err:
            log("Error during httpd.shutdown(): {}".format(shutdown_err), level="WARNING")
        try:
            httpd.server_close()
        except Exception as close_err:
            log("Error during httpd.server_close(): {}".format(close_err), level="WARNING")
        log("HTTPS server stopped.")
    shutdown_event.set()
    bring_window_to_foreground()

def load_downloaded_emails():
    downloaded_emails = set()
    if os.path.exists(downloaded_emails_file):
        with open(downloaded_emails_file, 'r') as file:
            downloaded_emails = set(line.strip() for line in file)
    log("Loaded downloaded emails: {}".format(downloaded_emails), level="DEBUG")
    return downloaded_emails

def add_downloaded_email(filename, config=None, log_fn=None):
    """
    Add a filename to downloaded_emails.txt.
    
    Reuses existing config loading pattern and file update logic.
    Can be called from both MediLink_Gmail.py and external scripts.
    
    Args:
        filename: Filename to add (just the name, not full path)
        config: Optional config dict. If None, loads using existing pattern
        log_fn: Optional logging function (defaults to module log)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use provided log function or fall back to module log
        _log = log_fn if log_fn is not None else log
        
        # Load config if not provided
        if config is None:
            try:
                config, _ = load_configuration()
            except Exception as e:
                _log("Failed to load configuration: {}".format(e), level="ERROR")
                return False
        
        # Extract MediLink config using existing pattern
        medi = extract_medilink_config(config)
        local_storage_path = medi.get('local_storage_path', '.')
        downloaded_emails_file_path = os.path.join(local_storage_path, 'downloaded_emails.txt')
        
        # Load existing entries to avoid duplicates (reusing load_downloaded_emails logic)
        downloaded_emails = set()
        if os.path.exists(downloaded_emails_file_path):
            try:
                with open(downloaded_emails_file_path, 'r') as file:
                    downloaded_emails = set(line.strip() for line in file if line.strip())
            except Exception as e:
                _log("Warning: Failed to read existing downloaded_emails.txt: {}".format(e), level="WARNING")
        
        # Check if already in list (case-insensitive check)
        filename_lower = filename.lower()
        if any(existing.lower() == filename_lower for existing in downloaded_emails):
            _log("Filename already in downloaded_emails.txt: {}".format(filename), level="DEBUG")
            return True  # Already exists, consider it successful
        
        # Add to set and append to file (reusing pattern from download_docx_files line 1787-1789)
        downloaded_emails.add(filename)
        try:
            with open(downloaded_emails_file_path, 'a') as file:
                file.write(filename + '\n')
            _log("Added filename to downloaded_emails.txt: {}".format(filename), level="DEBUG")
            return True
        except Exception as e:
            _log("Failed to write to downloaded_emails.txt: {}".format(e), level="ERROR")
            return False
            
    except Exception as e:
        _log = log_fn if log_fn is not None else log
        _log("Error in add_downloaded_email: {}".format(e), level="ERROR")
        return False

def download_docx_files(links):
    # Check internet connectivity before attempting downloads
    if not check_internet_connection():
        log("No internet connection available. Cannot download files without internet access.", level="WARNING")
        return
    
    downloaded_emails = load_downloaded_emails()
    downloads_count = 0
    docx_count = 0
    csv_count = 0
    total_detected = len(links)
    
    log("Starting download batch for {} detected file(s).".format(total_detected), level="INFO")
    
    for link in links:
        url = None  # Initialize to prevent NameError in exception handler
        try:
            url = link.get('url', '')
            filename = link.get('filename', '')
            log("Processing link: url='{}', filename='{}'".format(url, filename), level="DEBUG")
            
            lower_name = (filename or '').lower()
            is_csv = any(lower_name.endswith(ext) for ext in ['.csv', '.tsv', '.txt', '.dat'])
            is_docx = lower_name.endswith('.docx')
            file_type = "CSV" if is_csv else ("DOCX" if is_docx else "Unknown")
            
            if is_csv:
                log("[CSV Routing Preview] Detected CSV-like filename: {}. Will be routed to CSV processing directory.".format(filename))
            
            if filename in downloaded_emails:
                log("Skipping already downloaded email: {}".format(filename))
                continue
            
            log("Downloading {} file from URL: {}".format(file_type, url), level="DEBUG")
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                file_path = os.path.join(local_storage_path, filename)
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                log("Downloaded {} file: {}".format(file_type, filename))
                
                # Use extracted function to update downloaded_emails.txt (DRY)
                # Pass global config to use any runtime updates (see line 272)
                add_downloaded_email(filename, config=config)
                downloaded_emails.add(filename)
                
                downloads_count += 1
                if is_csv:
                    csv_count += 1
                elif is_docx:
                    docx_count += 1
                    
                try:
                    set_counts(files_downloaded=downloads_count)
                except Exception:
                    pass
            else:
                log("Failed to download {} file from URL: {}. Status code: {}".format(file_type, url, response.status_code))
        except Exception as e:
            log("Error downloading file from URL: {}. Error: {}".format(url, e))

    log("Download summary: Total detected={}, Successfully Downloaded={} ({} CSV, {} DOCX)".format(
        total_detected, downloads_count, csv_count, docx_count), level="INFO")

def open_browser_with_executable(url, browser_path=None):
    try:
        if browser_path:
            log("Attempting to open URL with provided executable: {} {}".format(browser_path, url), level="DEBUG")
            process = subprocess.Popen([browser_path, url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                log("Browser opened with provided executable path using subprocess.Popen.")
            else:
                log("Browser failed to open using subprocess.Popen. Return code: {}. Stderr: {}".format(process.returncode, stderr))
        else:
            log("No browser path provided. Attempting to open URL with default browser: {}".format(url), level="DEBUG")
            webbrowser.open(url)
            log("Default browser opened.", level="DEBUG")
    except Exception as e:
        log("Failed to open browser: {}".format(e))

def initiate_link_retrieval(config):
    log("Initiating two-tab launch: local status page first, then GAS webapp.")
    medi = extract_medilink_config(config)
    dep_id = (medi.get('webapp_deployment_id', '') or '').strip()
    if not dep_id:
        log("webapp_deployment_id is empty. Please set it in config before continuing.")
        shutdown_event.set()
        return

    # First tab: Open local status page to verify connectivity and trust
    local_status_url = LOCAL_SERVER_BASE_URL + '/'
    log("Opening local status page: {}".format(local_status_url))
    try:
        print("[Launch] Opening local server status page...")
        open_browser_with_executable(local_status_url)
        # Brief pause to let the first tab load and surface any certificate prompts
        time.sleep(1.5)
    except Exception as e:
        log("Warning: Failed to open local status page: {}".format(e))

    # Second tab: Open GAS webapp for the main workflow
    # Add http_mode parameter if HTTP mode is enabled (for immediate webapp detection)
    # NOTE: Even with http_mode=1, HTTP mode will NOT work from Google Apps Script (HTTPS)
    # due to Chrome Private Network Access blocking. The flag is passed but requests will fail.
    # To use HTTP mode, either:
    # 1. Serve webapp over HTTP (not from GAS)
    # 2. Disable Chrome PNA: --disable-features=BlockInsecurePrivateNetworkRequests
    # 3. Use HTTPS mode instead (recommended)
    http_mode_param = "&http_mode=1" if USE_HTTP_MODE else ""
    url_get = "https://script.google.com/macros/s/{}/exec?action=get_link{}".format(dep_id, http_mode_param)
    try:
        log("Opening GAS web app: {}".format(url_get), level="DEBUG")
    except Exception:
        pass
    # Preflight probe to surface HTTP status/redirects before opening the browser
    try:
        probe_url = "https://script.google.com/macros/s/{}/exec".format(dep_id)
        try:
            resp = requests.get(probe_url, allow_redirects=False, timeout=8)
            loc = resp.headers.get('Location')
            log("Preflight probe: status={} location={}".format(resp.status_code, loc), level="DEBUG")
        except Exception as probe_err:
            log("Preflight probe failed: {}".format(probe_err))
    except Exception:
        pass
    try:
        print("[Launch] Opening MediLink web application...")
        open_browser_with_executable(url_get)
    except Exception as e:
        log("Warning: Failed to open GAS webapp: {}".format(e))
    log("Preparing POST call.", level="DEBUG")
    url = "https://script.google.com/macros/s/{}/exec".format(dep_id)
    downloaded_emails = list(load_downloaded_emails())
    payload = {"downloadedEmails": downloaded_emails}
    access_token = get_access_token()
    if not access_token:
        log("Access token not found. Please authenticate first.")
        shutdown_event.set()
        return
    token_info = http_inspect_token(access_token, log, delete_token_file_fn=delete_token_file, stop_server_fn=stop_server)
    if token_info is None:
        log("Access token is invalid. Please re-authenticate.")
        shutdown_event.set()
        return
    headers = {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type': 'application/json'}
    log("Request headers: {}".format(_mask_sensitive_dict(headers)), level="DEBUG")
    log("Request payload: {}".format(payload), level="DEBUG")
    handle_post_response(url, payload, headers)

def handle_post_response(url, payload, headers):
    try:
        response = requests.post(url, json=payload, headers=headers)
        log("Response status code: {}".format(response.status_code), level="DEBUG")
        log("Response body: {}".format(response.text), level="DEBUG")
        if response.status_code == 200:
            response_data = response.json()
            log("Parsed response data: {}".format(response_data), level="DEBUG")
            if response_data.get("status") == "error":
                log("Error message from server: {}".format(response_data.get("message")))
                print("Error: {}".format(response_data.get("message")))
                shutdown_event.set()
            else:
                log("Link retrieval initiated successfully.")
        elif response.status_code == 401:
            # Automatic re-auth: clear token and prompt user to re-consent, keep server up
            log("Unauthorized (401). Clearing cached token and initiating re-authentication flow. Response body: {}".format(response.text))
            delete_token_file()
            auth_url = get_authorization_url()
            print("Your Google session needs to be refreshed to regain permissions. A browser window will open to re-authorize the app with the required scopes.")
            open_browser_with_executable(auth_url)
            # Wait for the OAuth redirect/flow to complete; the server remains running
            shutdown_event.wait()
        elif response.status_code == 403:
            # Treat 403 similarly; scopes may be missing/changed. Force a fresh consent.
            log("Forbidden (403). Clearing cached token and prompting for fresh consent. Response body: {}".format(response.text))
            delete_token_file()
            auth_url = get_authorization_url()
            print("Permissions appear insufficient (403). Opening browser to request the correct Google permissions.")
            open_browser_with_executable(auth_url)
            shutdown_event.wait()
        elif response.status_code == 404:
            log("Not Found. Verify the URL and ensure the Apps Script is deployed correctly. Response body: {}".format(response.text))
            shutdown_event.set()
        else:
            log("Failed to initiate link retrieval. Unexpected status code: {}. Response body: {}".format(response.status_code, response.text))
            shutdown_event.set()
    except requests.exceptions.RequestException as e:
        log("RequestException during link retrieval initiation: {}".format(e))
        shutdown_event.set()
    except Exception as e:
        log("Unexpected error during link retrieval initiation: {}".format(e))
        shutdown_event.set()

def send_delete_request_to_gas(file_ids):
    """Send a delete_files action to the Apps Script web app for the provided Drive file IDs.
    Relies on OAuth token previously obtained. Sends user notifications via GAS.
    """
    try:
        medi = extract_medilink_config(config)
        url = "https://script.google.com/macros/s/{}/exec".format(medi.get('webapp_deployment_id', ''))
        access_token = get_access_token()
        if not access_token:
            log("Access token not found. Skipping cleanup request to GAS.")
            return False
        headers = {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type': 'application/json'}
        payload = {"action": "delete_files", "fileIds": list(file_ids)}
        log("Initiating cleanup request to GAS. Payload size: {} id(s)".format(len(file_ids)))
        resp = requests.post(url, json=payload, headers=headers)
        log("Cleanup response status: {}".format(resp.status_code))
        # Print a concise console message
        if resp.ok:
            try:
                body = resp.json()
                msg = body.get('message', 'Files deleted successfully') if isinstance(body, dict) else 'Files deleted successfully'
            except Exception:
                msg = 'Files deleted successfully'
            print("Cleanup complete: {} ({} file(s))".format(msg, len(file_ids)))
            return True
        else:
            print("Cleanup failed with status {}: {}".format(resp.status_code, resp.text))
            return False
    except Exception as e:
        log("Error sending delete request to GAS: {}".format(e))
        print("Cleanup request error: {}".format(e))
        return False

def inspect_token(access_token):
    return http_inspect_token(access_token, log, delete_token_file_fn=delete_token_file, stop_server_fn=stop_server)

def delete_token_file():
    try:
        if os.path.exists(TOKEN_PATH):
            shared_clear_token_cache(log=log, medi_config=medi)
            if os.path.exists(TOKEN_PATH):
                log("Failed to remove token cache at {}. Check file locks/permissions.".format(TOKEN_PATH), level="WARNING")
            else:
                log("Deleted token cache at {}".format(TOKEN_PATH))
        else:
            log("Token cache already cleared (no file at {}).".format(TOKEN_PATH), level="DEBUG")
    except Exception as e:
        log("Error deleting token cache at {}: {}".format(TOKEN_PATH, e), level="ERROR")

def signal_handler(sig, frame):
    log("Signal received: {}. Initiating shutdown.".format(sig))
    stop_server()
    sys.exit(0)

def auth_and_retrieval():
    access_token = get_access_token()
    if not access_token:
        log("Access token not found or expired. Please authenticate first.")
        auth_url = get_authorization_url()
        open_browser_with_executable(auth_url)
        shutdown_event.wait()
    else:
        log("Access token found. Proceeding.")
        initiate_link_retrieval(config)
        shutdown_event.wait()

def is_valid_authorization_code(auth_code):
    return oauth_is_valid_authorization_code(auth_code, log)

def clear_token_cache():
    shared_clear_token_cache(log=log, medi_config=medi)

def check_invalid_grant_causes(auth_code):
    log("FUTURE IMPLEMENTATION: Checking common causes for invalid_grant error with auth code: {}".format(_mask_token_value(auth_code)))


def ensure_authenticated_for_gmail_send(max_wait_seconds=120):
    """Ensure a valid Gmail access token is available for sending.

    - Reuses existing OAuth helpers in this module.
    - Starts the local HTTPS server if needed, opens the browser for consent,
      and polls for a token for up to max_wait_seconds.
    - Returns True if a usable access token is available after the flow; otherwise False.
    """
    try:
        token = get_access_token()
    except Exception:
        token = None
    if token:
        return True

    # Prepare server and certificates (skip certificates in HTTP mode)
    if not USE_HTTP_MODE:
        try:
            generate_self_signed_cert(cert_file, key_file)
        except Exception as e:
            log("Warning: could not ensure self-signed certs: {}".format(e))

    server_started_here = False
    global httpd
    try:
        if httpd is None:
            mode_str = "HTTP" if USE_HTTP_MODE else "HTTPS"
            log("Starting local {} server for OAuth redirect handling.".format(mode_str))
            server_thread = Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()
            ensure_connection_watchdog_running()
            server_started_here = True
            time.sleep(0.5)  # Wait for server to initialize
            # Set flag to prevent webapp launch
            if httpd is not None:
                httpd.gmail_send_only_mode = True
    except Exception as e:
        log("Failed to start OAuth local server: {}".format(e))

    try:
        auth_url = get_authorization_url()
        print("Opening browser to authorize Gmail permission for sending...")
        open_browser_with_executable(auth_url)
    except Exception as e:
        log("Failed to open authorization URL: {}".format(e))

    # Poll for token availability within timeout
    start_ts = time.time()
    token = None
    while time.time() - start_ts < max_wait_seconds:
        try:
            token = get_access_token()
        except Exception:
            token = None
        if token:
            break
        time.sleep(3)

    if server_started_here:
        try:
            # Reset flag before shutdown
            if httpd is not None:
                httpd.gmail_send_only_mode = False
            stop_server()
        except Exception:
            pass

    if not token:
        print("Gmail authorization not completed within timeout. Please finish consent and retry.")

    return bool(token)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        # Run diagnostics with auto_fix enabled at startup (skip in HTTP mode)
        if not USE_HTTP_MODE and DIAGNOSTICS_AVAILABLE:
            try:
                diag_report = run_connection_diagnostics(
                    cert_file=cert_file,
                    key_file=key_file,
                    server_port=server_port,
                    auto_fix=True,  # Enable auto-fix at startup
                    openssl_cnf=get_openssl_cnf()
                )
                # Log if certificate was auto-fixed
                if diag_report.get('fixes_successful'):
                    log("Auto-fixed certificate issues: {}".format(diag_report['fixes_successful']), level="INFO")
            except Exception as diag_err:
                log("Error running startup diagnostics: {}".format(diag_err), level="WARNING")
                # Continue - certificate generation will still run below
        
        # Existing certificate generation (fallback if diagnostics not available) - skip in HTTP mode
        if not USE_HTTP_MODE:
            generate_self_signed_cert(cert_file, key_file)
        from threading import Thread
        log("Starting server thread.")
        server_thread = Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        ensure_connection_watchdog_running()
        auth_and_retrieval()
        log("Stopping HTTPS server.")
        stop_server()
        log("Waiting for server thread to finish.")
        server_thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
        
        # If server thread is still alive after join timeout, it's likely blocking on serve_forever()
        # Force cleanup and continue - daemon thread will be killed on process exit anyway
        if server_thread.is_alive():
            log("Server thread still alive after join timeout. Thread is daemon, will exit with process.", level="WARNING")
        
        # Check if server crashed - if so, exit with error code so batch file can return to menu
        # Note: Reading global variable doesn't require 'global' declaration
        if server_crashed:
            log("Server thread crashed. Exiting with error code to return to main menu.", level="ERROR")
            sys.exit(1)
        
        # Explicitly exit to ensure clean shutdown (daemon threads will be terminated)
        sys.exit(0)
    except KeyboardInterrupt:
        log("KeyboardInterrupt received, stopping server.")
        stop_server()
        sys.exit(0)
    except Exception as e:
        error_msg = "An error occurred: {}".format(e)
        log(error_msg, level="ERROR")
        # Also print to console so user sees the error immediately
        try:
            import traceback
            print("[ERROR] {}".format(error_msg))
            traceback.print_exc()
        except Exception:
            pass
        stop_server()
        sys.exit(1)