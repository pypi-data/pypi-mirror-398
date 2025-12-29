# MediLink_ConfigLoader.py
import os, json, logging, sys, platform, copy, tempfile
try:
    import yaml
except ImportError:
    yaml = None
from datetime import datetime
from collections import OrderedDict
from functools import reduce

# Global configuration cache to prevent repeated loading
_CONFIG_CACHE = None
_CROSSWALK_CACHE = None

_CERT_PROVIDER_DEFAULTS = {
    'mode': 'self_signed',
    'profile': 'default',
    'root_subject': 'CN=MediLink Managed Root CA',
    'server_subject': 'CN=127.0.0.1',
    'san': ['127.0.0.1', 'localhost'],
    'root_valid_days': 3650,
    'server_valid_days': 365
}


def _copy_cert_provider_defaults():
    try:
        return copy.deepcopy(_CERT_PROVIDER_DEFAULTS)
    except Exception:
        return {
            'mode': 'self_signed',
            'profile': 'default',
            'root_subject': 'CN=MediLink Managed Root CA',
            'server_subject': 'CN=127.0.0.1',
            'san': ['127.0.0.1', 'localhost'],
            'root_valid_days': 3650,
            'server_valid_days': 365
        }

# Import centralized logging configuration
try:
    from MediCafe.logging_config import PERFORMANCE_LOGGING
except ImportError:
    # Fallback to local flag if centralized config is not available
    PERFORMANCE_LOGGING = False

try:
    from MediBot.config_editor_helpers import (
        save_config_atomic as _editor_save_config_atomic,
        resolve_config_path as _editor_resolve_config_path,
        load_config_safe as _editor_load_config_safe,
    )
except Exception:
    _editor_save_config_atomic = None
    _editor_resolve_config_path = None
    _editor_load_config_safe = None

def get_default_config():
    """Provide a default configuration when config files are missing."""
    return {
        'MediLink_Config': {
            'local_storage_path': '.',
            'receiptsRoot': './receipts',
            # HTTP mode flag: when True, server runs without SSL/TLS encryption
            # WARNING: Only suitable for localhost (127.0.0.1/localhost) development
            # Do not use in production or over network connections
            #
            # IMPORTANT LIMITATION: HTTP mode does NOT work when webapp is served from HTTPS pages
            # (e.g., Google Apps Script). Chrome's Private Network Access (PNA) blocks HTTPS-to-HTTP
            # localhost requests at the browser level, before they reach the server.
            #
            # Workarounds:
            # 1. Use HTTPS mode (recommended): Avoids PNA blocking but requires certificate trust
            # 2. Serve webapp over HTTP: HTTP mode works when webapp is served from HTTP (not GAS)
            # 3. Disable Chrome PNA (development only): Launch Chrome with flag:
            #    --disable-features=BlockInsecurePrivateNetworkRequests
            #    Example: chrome.exe --disable-features=BlockInsecurePrivateNetworkRequests
            #
            # Recommendation: Use HTTPS mode for production. HTTP mode is only suitable for:
            # - Development when webapp is served over HTTP (not from Google Apps Script)
            # - Testing with PNA disabled via browser flag
            'use_http_mode': False,  # Default: use HTTPS (secure)
            'api_endpoints': {
                'base_url': 'https://api.example.com',
                'timeout': 30
            },
            'logging': {
                'level': 'INFO',
                'console_output': True
            },
            'error_reporting': {
                'enabled': False,
                'endpoint_url': '',
                'auth_token': '',
                'insecure_http': False,
                'max_bundle_bytes': 2097152,
                'email': {
                    'enabled': False,
                    'to': '',
                    'subject_prefix': 'MediCafe Error Report',
                    'max_bundle_bytes': 1572864
                }
            },
            'certificate_provider': {
                'mode': 'self_signed',
                'profile': 'default',
                'root_subject': 'CN=MediLink Managed Root CA',
                'server_subject': 'CN=127.0.0.1',
                'san': ['127.0.0.1', 'localhost'],
                'root_valid_days': 3650,
                'server_valid_days': 365
            },
            # STRATEGIC NOTE (COB Configuration): COB library is fully implemented and ready
            # To enable COB functionality, add the following configuration:
            # 'cob_settings': {
            #     'enabled': False,  # Set to True to activate COB processing
            #     'medicare_payer_ids': ['00850', 'MEDICARE', 'CMS', 'MCARE'],
            #     'cob_mode': 'single_payer_only',  # or 'multi_payer_supported'
            #     'validation_level': 3,  # SNIP level 3+ recommended for COB
            #     'medicare_advantage_identifiers': ['MA', 'MC'],
            #     'default_medicare_type': 'MB',
            #     'require_835_validation': False  # Set True for production
            # }
        }
    }

def get_default_crosswalk():
    """Provide a default crosswalk when crosswalk files are missing."""
    return {
        'insurance_types': {},
        'diagnosis_codes': {},
        'procedure_codes': {},
        'payer_mappings': {}
    }

"""
This function should be generalizable to have a initialization script over all the Medi* functions
"""
def load_configuration(config_path=os.path.join(os.path.dirname(__file__), '..', 'json', 'config.json'), crosswalk_path=os.path.join(os.path.dirname(__file__), '..', 'json', 'crosswalk.json')):
    """
    Loads endpoint configuration, credentials, and other settings from JSON or YAML files.
        
    Returns: A tuple containing dictionaries with configuration settings for the main config and crosswalk.
    """
    global _CONFIG_CACHE, _CROSSWALK_CACHE
    
    # Return cached configuration if available
    if _CONFIG_CACHE is not None and _CROSSWALK_CACHE is not None:
        return _CONFIG_CACHE, _CROSSWALK_CACHE
    
    import time
    config_start = time.time()
    if PERFORMANCE_LOGGING:
        print("Configuration loading started...")
    
    # TODO (Low Config Upgrade) The Medicare / Private differentiator flag probably needs to be pulled or passed to this.
    # SUGGESTION:
    # - Introduce optional keys under MediLink_Config: {'payer_type': 'Medicare'|'Private'} or per-endpoint flags.
    # - Keep behavior identical when key is absent. Only consumers that opt-in should read this.
    # - XP note: keep the structure flat to avoid deep dict traversal when used in hot paths.
    # Use provided paths, or fall back to platform-specific defaults
    path_check_start = time.time()
    if not os.path.exists(config_path):
        # Try platform-specific paths as fallback
        if platform.system() == 'Windows' and platform.release() == 'XP':
            # Use F: paths for Windows XP
            config_path = "F:\\Medibot\\json\\config.json"
            crosswalk_path = "F:\\Medibot\\json\\crosswalk.json"
        elif platform.system() == 'Windows':
            # Use current working directory for other versions of Windows
            current_dir = os.getcwd()
            config_path = os.path.join(current_dir, 'json', 'config.json')
            crosswalk_path = os.path.join(current_dir, 'json', 'crosswalk.json')
        # If not Windows or if local files don't exist, keep the default paths
    
    path_check_end = time.time()
    if PERFORMANCE_LOGGING:
        print("Path resolution completed in {:.2f} seconds".format(path_check_end - path_check_start))
    
    # Load configuration with graceful fallback
    config = None
    crosswalk = None
    
    try:
        config_load_start = time.time()
        with open(config_path, 'r') as config_file:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config = yaml.safe_load(config_file)
            elif config_path.endswith('.json'):
                config = json.load(config_file, object_pairs_hook=OrderedDict)
            else:
                raise ValueError("Unsupported configuration format.")
            
            if 'MediLink_Config' not in config:
                raise KeyError("MediLink_Config key is missing from the loaded configuration.")
            else:
                try:
                    _ensure_certificate_provider_section(config.get('MediLink_Config'))
                except Exception:
                    pass
        
        config_load_end = time.time()
        if PERFORMANCE_LOGGING:
            print("Config file loading completed in {:.2f} seconds".format(config_load_end - config_load_start))

        # FUTURE: centralize crosswalk writes for atomic updates from encoder flows
        # e.g., def save_crosswalk(crosswalk): write temp file then replace to avoid partial writes on XP.
        crosswalk_load_start = time.time()
        with open(crosswalk_path, 'r') as crosswalk_file:
            crosswalk = json.load(crosswalk_file)
        crosswalk_load_end = time.time()
        if PERFORMANCE_LOGGING:
            print("Crosswalk file loading completed in {:.2f} seconds".format(crosswalk_load_end - crosswalk_load_start))

    except FileNotFoundError:
        # Graceful fallback to default configurations
        print("Configuration files not found. Using default configurations.")
        print("Config path: {}, Crosswalk path: {}".format(config_path, crosswalk_path))
        print("To use custom configurations, create the 'json' directory and add config.json and crosswalk.json files.")
        
        config = get_default_config()
        crosswalk = get_default_crosswalk()
        
        # Log the fallback for debugging
        if PERFORMANCE_LOGGING:
            print("Using default configurations due to missing files")
            
    except ValueError as e:
        # LOUD NOTIFICATION for malformed JSON files
        print("\n" + "="*80)
        print("*** CRITICAL ERROR: MALFORMED JSON CONFIGURATION FILES ***")
        print("="*80)
        if isinstance(e, UnicodeDecodeError):
            print("ERROR: Cannot decode configuration file - invalid character encoding")
            print("DETAILS: {}".format(e))
        else:
            print("ERROR: Configuration files contain invalid JSON syntax")
            print("DETAILS: {}".format(e))
        print("\nAFFECTED FILES:")
        print("- Config file: {}".format(config_path))
        print("- Crosswalk file: {}".format(crosswalk_path))
        print("\nACTION REQUIRED:")
        print("1. Check JSON syntax in both files")
        print("2. Validate JSON using an online validator")
        print("3. Fix syntax errors and restart the application")
        print("\nFALLBACK: Using default configurations (may cause issues)")
        print("="*80 + "\n")
        
        config = get_default_config()
        crosswalk = get_default_crosswalk()
    except KeyError as e:
        # LOUD NOTIFICATION for missing required configuration keys
        print("\n" + "="*80)
        print("*** CRITICAL ERROR: MISSING REQUIRED CONFIGURATION ***")
        print("="*80)
        print("ERROR: Required configuration key is missing")
        print("DETAILS: {}".format(e))
        print("\nAFFECTED FILE: {}".format(config_path))
        print("\nACTION REQUIRED:")
        print("1. Ensure 'MediLink_Config' section exists in config.json")
        print("2. Check that all required configuration keys are present")
        print("3. Verify JSON structure matches expected format")
        print("\nFALLBACK: Using default configurations (may cause issues)")
        print("="*80 + "\n")
        
        config = get_default_config()
        crosswalk = get_default_crosswalk()
    except Exception as e:
        print("An unexpected error occurred while loading the configuration: {}".format(e))
        print("Falling back to default configurations...")
        config = get_default_config()
        crosswalk = get_default_crosswalk()

    config_end = time.time()
    if PERFORMANCE_LOGGING:
        print("Total configuration loading completed in {:.2f} seconds".format(config_end - config_start))
    
    # Cache the loaded configuration
    _CONFIG_CACHE = config
    _CROSSWALK_CACHE = crosswalk
    
    return config, crosswalk

def clear_config_cache():
    """Clear the configuration cache to force reloading on next call."""
    global _CONFIG_CACHE, _CROSSWALK_CACHE
    _CONFIG_CACHE = None
    _CROSSWALK_CACHE = None


def _ensure_certificate_provider_section(medi_config):
    if not isinstance(medi_config, dict):
        return _copy_cert_provider_defaults()
    provider = medi_config.get('certificate_provider')
    if not isinstance(provider, dict):
        provider = _copy_cert_provider_defaults()
        medi_config['certificate_provider'] = provider
        return provider
    defaults = _copy_cert_provider_defaults()
    for key, value in defaults.items():
        if key not in provider:
            provider[key] = copy.deepcopy(value) if isinstance(value, (list, dict)) else value
    if not isinstance(provider.get('san'), list):
        provider['san'] = list(defaults['san'])
    return provider


def get_certificate_provider_config(source_config=None, use_cache=True):
    """
    Return certificate provider settings merged with defaults.
    Accepts either a full config dict or the MediLink_Config subsection.
    """
    try:
        config = source_config
        if config is None:
            config = _CONFIG_CACHE if use_cache and _CONFIG_CACHE else load_configuration()[0]
        if isinstance(config, dict):
            medi = config.get('MediLink_Config')
            if isinstance(medi, dict):
                provider = _ensure_certificate_provider_section(medi)
                return copy.deepcopy(provider)
            provider = _ensure_certificate_provider_section(config)
            return copy.deepcopy(provider)
    except Exception:
        pass
    return _copy_cert_provider_defaults()


def update_certificate_provider_config(new_values, config_path=None, create_backup=True):
    """
    Merge new certificate provider settings into config.json using atomic write semantics.
    
    Args:
        new_values (dict): Keys/values to merge into certificate_provider.
        config_path (str): Optional override path to config.json.
        create_backup (bool): Placeholder for future behavior (backups handled by editor helpers).
    
    Returns:
        (success, error_message)
    """
    if not isinstance(new_values, dict):
        return False, "new_values must be a dict"
    
    target_path = config_path or os.path.join(os.path.dirname(__file__), '..', 'json', 'config.json')
    if _editor_resolve_config_path:
        try:
            target_path = _editor_resolve_config_path(target_path)
        except Exception:
            pass
    
    if _editor_load_config_safe:
        config_data, load_err = _editor_load_config_safe(target_path)
        if load_err:
            config_data = copy.deepcopy(get_default_config())
    else:
        config_data = copy.deepcopy(load_configuration()[0])
    
    if 'MediLink_Config' not in config_data or not isinstance(config_data['MediLink_Config'], dict):
        config_data['MediLink_Config'] = {}
    provider = _ensure_certificate_provider_section(config_data['MediLink_Config'])
    for key, value in new_values.items():
        provider[key] = value
    _ensure_certificate_provider_section(config_data['MediLink_Config'])
    
    writer = _editor_save_config_atomic
    if writer:
        success, error = writer(target_path, config_data)
    else:
        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', dir=os.path.dirname(target_path) or None)
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                    json.dump(config_data, temp_file, ensure_ascii=False, indent=4, separators=(',', ': '))
                if os.name == 'nt' and os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(temp_path, target_path)
            except Exception:
                try:
                    os.close(temp_fd)
                except Exception:
                    pass
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
            success, error = True, None
        except Exception as write_err:
            success, error = False, "Error writing config: {}".format(write_err)
    
    if success:
        clear_config_cache()
    return success, error
        
def require_config_value(key_path, use_cache=True):
    # TODO This needs expanding a little bit but generally this type of functionality is good to have at this level.
    config = _CONFIG_CACHE if use_cache and _CONFIG_CACHE else load_configuration()[0]
    return reduce(lambda d, k: d[k], key_path.split('.'), config)

# Logs messages with optional error type and claim data.
def log(message, config=None, level="INFO", error_type=None, claim=None, verbose=False, console_output=False):
    
    # Check for environment variable to override verbose setting (session-level control)
    if not verbose:
        env_verbose = os.environ.get('MEDICAFE_VERBOSE_LOGGING', '').strip().lower()
        if env_verbose in ('1', 'true', 'yes', 'on'):
            verbose = True
    
    # If config is not provided, use cached config or load it
    if config is None:
        try:
            if _CONFIG_CACHE is None:
                config, _ = load_configuration()
            else:
                config = _CONFIG_CACHE
        except BaseException:
            # Configuration unavailable; fall back to minimal console logging
            config = {}
    
    # Setup logger if not already configured
    if not logging.root.handlers:
        local_storage_path = '.'
        if isinstance(config, dict):
            try:
                local_storage_path = config.get('MediLink_Config', {}).get('local_storage_path', '.')
            except Exception:
                local_storage_path = '.'
        log_filename = datetime.now().strftime("Log_%m%d%Y.log")
        log_filepath = os.path.join(local_storage_path, log_filename)
        
        # Set logging level based on verbosity
        logging_level = logging.DEBUG if verbose else logging.INFO
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        handlers = []
        try:
            # Create file handler when path is usable
            file_handler = logging.FileHandler(log_filepath, mode='a')
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception:
            # Fall back to console-only if file handler cannot be created
            pass
        
        # Add console handler only if console_output is True
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)
        
        # If no handlers could be added (e.g., file path invalid and console_output False), add a console handler
        if not handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)
        
        logging.basicConfig(level=logging_level, handlers=handlers)
    else:
        # Logger already configured; update level if verbose mode changed
        if verbose:
            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)
            # Update all handlers to DEBUG level
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
    
    # Prepare log message
    claim_data = " - Claim Data: {}".format(claim) if claim else ""
    error_info = " - Error Type: {}".format(error_type) if error_type else ""
    full_message = "{} {}{}".format(message, claim_data, error_info)

    # Log the message
    logger = logging.getLogger()
    getattr(logger, level.lower())(full_message)