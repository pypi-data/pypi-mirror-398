# core_utils.py
"""
Core utilities module for MediCafe
This module contains shared functionality between MediBot and MediLink modules
to break circular import dependencies.
"""

import os, sys, time, subprocess

# Ensure proper path setup for imports
# Get the project root directory (parent of MediCafe directory)
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Only add project root to sys.path; do NOT add package directories directly
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Remove any direct package paths that may have been injected elsewhere
_pkg_dirs = [os.path.join(project_dir, 'MediLink'), os.path.join(project_dir, 'MediBot')]
for _p in list(sys.path):
    if _p in _pkg_dirs:
        try:
            while _p in sys.path:
                sys.path.remove(_p)
        except Exception:
            pass

# Common constants and configurations
DEFAULT_CONFIG_PATH = os.path.join(project_dir, 'json', 'config.json')
DEFAULT_CROSSWALK_PATH = os.path.join(project_dir, 'json', 'crosswalk.json')

# Environment flags controlling import behavior
_STRICT_IMPORT = os.environ.get('MEDICAFE_IMPORT_STRICT', '0').strip().lower() in ('1', 'true', 'yes', 'y')
_DEBUG_IMPORT = os.environ.get('MEDICAFE_IMPORT_DEBUG', '0').strip().lower() in ('1', 'true', 'yes', 'y')

# Simple memoization cache for resolved imports
_IMPORT_CACHE = {}

def _cache_get(key):
    try:
        return _IMPORT_CACHE.get(key)
    except Exception:
        return None

def _cache_set(key, value):
    try:
        _IMPORT_CACHE[key] = value
    except Exception:
        pass

def _module_provenance_ok(module):
    """Return True if module appears to come from this workspace."""
    try:
        module_file = getattr(module, '__file__', '') or ''
        return os.path.abspath(project_dir) in os.path.abspath(module_file)
    except Exception:
        return False

def require_functions(module, names):
    """Ensure the module exposes all required attributes; raise RuntimeError on failure in strict mode; return bool otherwise."""
    missing = [name for name in names if not hasattr(module, name)]
    if missing:
        message = "Missing required symbols {} in module {}".format(missing, getattr(module, '__name__', 'unknown'))
        if _STRICT_IMPORT:
            raise RuntimeError(message)
        if _DEBUG_IMPORT:
            try:
                print("[IMPORT DIAG] {} (file: {})".format(message, getattr(module, '__file__', 'unknown')))
            except Exception:
                pass
        return False
    return True

def print_import_diagnostics(label, module):
    """Print a single-line diagnostic about a resolved module (debug only)."""
    if not _DEBUG_IMPORT:
        return
    try:
        print("[IMPORT DIAG] {} -> name={} file={} workspace_provenance={}".format(
            label,
            getattr(module, '__name__', 'unknown'),
            getattr(module, '__file__', 'unknown'),
            _module_provenance_ok(module)
        ))
    except Exception:
        pass

def setup_project_path(file_path=None):
    """
    Standard project path setup function used by all entry points.
    
    Args:
        file_path: The __file__ of the calling module. If None, uses this file's directory.
    
    Returns:
        The project directory path.
    """
    if file_path is None:
        file_path = __file__
    
    project_dir = os.path.abspath(os.path.join(os.path.dirname(file_path), ".."))
    current_dir = os.path.abspath(os.path.dirname(file_path))
    
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    return project_dir

def setup_module_paths(file_path):
    """
    Enhanced path setup for individual modules.
    Sets up both project root and module directory paths.
    
    Args:
        file_path: The __file__ of the calling module
    
    Returns:
        Tuple of (project_dir, current_dir)
    """
    project_dir = os.path.abspath(os.path.join(os.path.dirname(file_path), ".."))
    current_dir = os.path.abspath(os.path.dirname(file_path))
    
    # Add only project root and current module dir; avoid adding package dirs explicitly
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    return project_dir, current_dir

def safe_import_with_fallback(primary_import_path, fallback_import_path=None, function_name=None):
    """
    Safely import a module or function with fallback options.
    
    Args:
        primary_import_path (str): Primary import path to try
        fallback_import_path (str): Fallback import path if primary fails
        function_name (str): Specific function name to extract from module
    
    Returns:
        The imported module or function, or None if all imports fail
    """
    try:
        if function_name:
            module = __import__(primary_import_path, fromlist=[function_name])
            return getattr(module, function_name)
        else:
            return __import__(primary_import_path)
    except ImportError:
        if fallback_import_path:
            try:
                if function_name:
                    module = __import__(fallback_import_path, fromlist=[function_name])
                    return getattr(module, function_name)
                else:
                    return __import__(fallback_import_path)
            except ImportError:
                return None
        return None

def smart_import(import_specs, default_value=None):
    """
    Enhanced import function that tries multiple import strategies intelligently.
    
    Args:
        import_specs (list): List of import specifications. Each can be:
            - String: Direct import path
            - Tuple: (import_path, function_name)
            - Dict: {'path': import_path, 'function': function_name, 'fallback': fallback_path}
        default_value: Value to return if all imports fail
    
    Returns:
        The imported module/function or default_value
    """
    for spec in import_specs:
        try:
            if isinstance(spec, str):
                # Simple string - direct import
                # If dotted path, ensure we get the submodule, not just the top-level package
                cached = _cache_get(('str', spec))
                if cached is not None:
                    if _DEBUG_IMPORT:
                        print("[IMPORT DIAG] Cache hit for {}".format(spec))
                    return cached
                if '.' in spec:
                    result = __import__(spec, fromlist=['*'])
                else:
                    result = __import__(spec)
                _cache_set(('str', spec), result)
                if _DEBUG_IMPORT:
                    print_import_diagnostics("smart_import:{}".format(spec), result)
                return result
            elif isinstance(spec, tuple):
                # Tuple - (path, function_name)
                path, function_name = spec
                cached = _cache_get(('tuple', path, function_name))
                if cached is not None:
                    return cached
                module = __import__(path, fromlist=[function_name])
                result = getattr(module, function_name)
                _cache_set(('tuple', path, function_name), result)
                return result
            elif isinstance(spec, dict):
                # Dict with fallback
                path = spec['path']
                function_name = spec.get('function')
                fallback = spec.get('fallback')
                
                try:
                    cache_key = ('dict', path, function_name)
                    cached = _cache_get(cache_key)
                    if cached is not None:
                        return cached
                    if function_name:
                        module = __import__(path, fromlist=[function_name])
                        result = getattr(module, function_name)
                    else:
                        # If dotted, use fromlist to return the submodule
                        if '.' in path:
                            result = __import__(path, fromlist=['*'])
                        else:
                            result = __import__(path)
                    _cache_set(cache_key, result)
                    return result
                except ImportError:
                    if fallback:
                        try:
                            cache_key = ('dict_fallback', fallback, function_name)
                            cached = _cache_get(cache_key)
                            if cached is not None:
                                return cached
                            if function_name:
                                module = __import__(fallback, fromlist=[function_name])
                                result = getattr(module, function_name)
                            else:
                                if '.' in fallback:
                                    result = __import__(fallback, fromlist=['*'])
                                else:
                                    result = __import__(fallback)
                            _cache_set(cache_key, result)
                            return result
                        except ImportError:
                            continue
                    continue
        except ImportError:
            continue
    
    return default_value

def import_medibot_module(module_name, function_name=None):
    """
    Centralized function to import MediBot modules with intelligent fallbacks.
    
    Args:
        module_name (str): Name of the MediBot module (e.g., 'MediBot_dataformat_library')
        function_name (str): Specific function to extract (optional)
    
    Returns:
        The imported module/function or None
    """
    import_specs = [
        # Direct import first
        module_name,
        # Then try with MediBot prefix
        'MediBot.{}'.format(module_name),
        # Then try relative import
        '.{}'.format(module_name),
        # Finally try as a submodule
        {'path': 'MediBot.{}'.format(module_name), 'fallback': module_name}
    ]
    
    if function_name:
        # If we need a specific function, modify specs to extract it
        function_specs = []
        for spec in import_specs:
            if isinstance(spec, str):
                function_specs.append((spec, function_name))
            elif isinstance(spec, dict):
                function_specs.append({
                    'path': spec['path'],
                    'function': function_name,
                    'fallback': spec.get('fallback')
                })
        return smart_import(function_specs)
    else:
        return smart_import(import_specs)

def import_medibot_module_with_debug(module_name, function_name=None):
    """
    Enhanced version of import_medibot_module with debugging information.
    
    Args:
        module_name (str): Name of the MediBot module
        function_name (str): Specific function to extract (optional)
    
    Returns:
        The imported module/function or None
    """
    # Try the standard import first
    result = import_medibot_module(module_name, function_name)
    if result is not None:
        return result
    
    # If that fails, try additional strategies with debugging
    additional_specs = [
        # Try as a direct file import
        '{}.py'.format(module_name),
        # Try with full path resolution
        'MediBot.{}.py'.format(module_name),
        # Try importing from current directory
        './{}'.format(module_name),
        # Try importing from parent directory
        '../{}'.format(module_name)
    ]
    
    for spec in additional_specs:
        try:
            if _DEBUG_IMPORT:
                print("[IMPORT DIAG] Trying additional spec: {}".format(spec))
            if function_name:
                module = __import__(spec, fromlist=[function_name])
                return getattr(module, function_name)
            else:
                return __import__(spec)
        except ImportError as e:
            if _DEBUG_IMPORT:
                print("[IMPORT DIAG] Additional spec {} failed: {}".format(spec, e))
            continue
    
    # If all else fails, log the failure
    config_loader = get_shared_config_loader()
    if config_loader:
        config_loader.log("Failed to import MediBot module: {}".format(module_name), level="WARNING")
    else:
        print("[WARNING] Failed to import MediBot module: {}".format(module_name))
    
    return None

def import_medilink_module(module_name, function_name=None):
    """
    Centralized function to import MediLink modules with intelligent fallbacks.
    
    Args:
        module_name (str): Name of the MediLink module
        function_name (str): Specific function to extract (optional)
    
    Returns:
        The imported module/function or None
    """
    # Prefer importing from the in-repo MediLink package first to avoid
    # accidentally picking up a similarly named top-level/site-packages module.
    import_specs = [
        # Prefer package-qualified import first (local codebase)
        'MediLink.{}'.format(module_name),
        # Then try direct import (legacy/installed module)
        module_name,
        # Then try relative import
        '.{}'.format(module_name),
        # Finally try as a submodule with fallback
        {'path': 'MediLink.{}'.format(module_name), 'fallback': module_name}
    ]
    
    if function_name:
        # If we need a specific function, modify specs to extract it
        function_specs = []
        for spec in import_specs:
            if isinstance(spec, str):
                function_specs.append((spec, function_name))
            elif isinstance(spec, dict):
                function_specs.append({
                    'path': spec['path'],
                    'function': function_name,
                    'fallback': spec.get('fallback')
                })
        result = smart_import(function_specs)
        if result is not None and _DEBUG_IMPORT:
            try:
                print_import_diagnostics('import_medilink_module:{}:function'.format(module_name), result)
            except Exception:
                pass
        return result
    else:
        result = smart_import(import_specs)
        if result is not None:
            # In strict mode, verify provenance and capabilities if demanded by callers
            if _STRICT_IMPORT and not _module_provenance_ok(result):
                raise RuntimeError("Imported module '{}' from outside workspace: {}".format(
                    module_name, getattr(result, '__file__', 'unknown')))
            print_import_diagnostics('import_medilink_module:{}'.format(module_name), result)
        return result

def get_shared_config_loader():
    """
    Returns the MediLink_ConfigLoader module using safe import patterns.
    This is used by both MediBot and MediLink modules.
    
    Returns:
        MediLink_ConfigLoader module or None if import fails
    """
    # Try multiple import strategies - now including the new MediCafe location
    try:
        # First try to import directly from MediCafe package
        from MediCafe import MediLink_ConfigLoader
        return MediLink_ConfigLoader
    except ImportError:
        try:
            # Try direct import from MediCafe directory
            import MediLink_ConfigLoader
            return MediLink_ConfigLoader
        except ImportError:
            try:
                # Try relative import from current directory
                from . import MediLink_ConfigLoader
                return MediLink_ConfigLoader
            except ImportError:
                return None


def create_fallback_logger():
    """
    Creates a minimal fallback logger when MediLink_ConfigLoader is unavailable.
    
    Returns:
        A simple logger object with a log method
    """
    class FallbackLogger:
        def log(self, message, level="INFO"):
            print("[{}] {}".format(level, message))
    
    return FallbackLogger()


def get_config_loader_with_fallback():
    """
    Get MediLink_ConfigLoader with automatic fallback to simple logger.
    
    Returns:
        MediLink_ConfigLoader or FallbackLogger
    """
    config_loader = get_shared_config_loader()
    if config_loader is None:
        return create_fallback_logger()
    return config_loader

def log_import_error(module_name, error, level="WARNING"):
    """
    Centralized logging for import errors.
    
    Args:
        module_name (str): Name of the module that failed to import
        error (Exception): The import error that occurred
        level (str): Log level (WARNING, ERROR, etc.)
    """
    config_loader = get_shared_config_loader()
    if config_loader and hasattr(config_loader, 'log'):
        config_loader.log("Failed to import {}: {}".format(module_name, error), level=level)
    else:
        print("[{}] Failed to import {}: {}".format(level, module_name, error))

def create_config_cache():
    """
    Creates a lazy configuration loading pattern for modules.
    Returns a tuple of (get_config_function, cache_variables).
    
    Usage:
        _get_config, (_config_cache, _crosswalk_cache) = create_config_cache()
        
        # Later in functions:
        config, crosswalk = _get_config()
    """
    _config_cache = None
    _crosswalk_cache = None
    
    def _get_config():
        nonlocal _config_cache, _crosswalk_cache
        if _config_cache is None:
            config_loader = get_shared_config_loader()
            if config_loader:
                _config_cache, _crosswalk_cache = config_loader.load_configuration()
            else:
                _config_cache, _crosswalk_cache = {}, {}
        return _config_cache, _crosswalk_cache
    
    return _get_config, (_config_cache, _crosswalk_cache)

# Common import patterns used throughout the codebase
def import_with_alternatives(import_specs):
    """
    Import a module using multiple alternative paths.
    
    Args:
        import_specs (list): List of tuples containing (import_path, function_name_or_None)
    
    Returns:
        The first successfully imported module or function
    """
    for import_path, function_name in import_specs:
        result = safe_import_with_fallback(import_path, function_name=function_name)
        if result is not None:
            return result
    return None

# API Client Factory Integration
def get_api_client_factory():
    """
    Get configured API client factory using shared configuration.
    
    Returns:
        APIClientFactory: Configured factory instance or None if unavailable
    """
    # Try multiple import paths for factory
    import_specs = [
        ('MediCafe.api_factory', 'APIClientFactory')
    ]
    
    APIClientFactory = import_with_alternatives(import_specs)
    if not APIClientFactory:
        log_import_error('MediCafe.api_factory', Exception("All import paths failed"))
        return None
    
    try:
        config_loader = get_shared_config_loader()
        if config_loader:
            try:
                # Be resilient to SystemExit raised inside loaders
                config, _ = config_loader.load_configuration()
                factory_config = config.get('API_Factory_Config', {}) if isinstance(config, dict) else {}
                return APIClientFactory(factory_config)
            except BaseException:
                # Fall back to default configuration on any loader failure (including SystemExit)
                return APIClientFactory()
        else:
            return APIClientFactory()
    except BaseException:
        # Do not allow API client factory acquisition to crash callers during import time
        return None

def get_api_client(**kwargs):
    """
    Convenience function to get API client directly.
    
    Args:
        **kwargs: Additional parameters
        
    Returns:
        APIClient: v3 API client instance or None if unavailable
    """
    factory = get_api_client_factory()
    if factory:
        return factory.get_client(**kwargs)
    return None

def extract_medilink_config(config):
    """
    Safely extract the MediLink_Config subsection from a configuration object
    without mutating or reassigning the original config. Returns an empty dict
    if not available. XP/Python 3.4.4 friendly.

    Philosophy:
    - Keep and pass the full config across the codebase for logging/path access
    - Derive a local 'medi' section only where endpoint-specific fields are needed
    - Avoid deep chained get() calls by normalizing once per function
    """
    try:
        if not isinstance(config, dict):
            return {}
        medi = config.get('MediLink_Config')
        if isinstance(medi, dict):
            return medi
        # If config already looks like a MediLink section (flat), return as-is
        return config
    except Exception:
        return {}

def get_api_core_client(**kwargs):
    """
    Get API client from MediCafe core API module.
    
    Args:
        **kwargs: Additional parameters
        
    Returns:
        APIClient: Core API client instance or None if unavailable
    """
    try:
        from MediCafe.api_core import APIClient
        return APIClient(**kwargs)
    except ImportError:
        # Don't log error here - just return None silently
        return None

# --- Compatibility & Process Utilities (Python 3.4.4 / Windows XP friendly) ---

def is_python_34_compatible(version_info=None):
    """
    Return True if the interpreter is Python 3.4.4+ (as required in XP env).
    This consolidates scattered version checks into a single function so
    call sites remain concise and intention-revealing.
    """
    try:
        if version_info is None:
            version_info = sys.version_info
        major = getattr(version_info, 'major', version_info[0])
        minor = getattr(version_info, 'minor', version_info[1])
        micro = getattr(version_info, 'micro', version_info[2])
        return (major, minor, micro) >= (3, 4, 4)
    except Exception:
        # Be conservative if we cannot determine
        return False

def format_py34(template, *args, **kwargs):
    """
    Safe stand-in for f-strings (not available in Python 3.4).
    Centralized to avoid ad-hoc "format_string" helpers scattered around.
    """
    try:
        return template.format(*args, **kwargs)
    except Exception:
        # If formatting fails, return template unmodified to avoid crashes
        return template

def _decode_bytes(data, encoding_list=None):
    """
    Decode bytes to text using a tolerant strategy.
    We avoid relying on platform defaults (XP may vary) and try multiple
    encodings to reduce boilerplate at call sites.
    """
    if data is None:
        return ''
    if isinstance(data, str):
        return data
    if encoding_list is None:
        encoding_list = ['utf-8', 'latin-1', 'ascii']
    for enc in encoding_list:
        try:
            return data.decode(enc, 'ignore')
        except Exception:
            continue
    # Last resort: str() on bytes
    try:
        return str(data)
    except Exception:
        return ''

def run_cmd(cmd, timeout=None, input_text=None, shell=False, cwd=None, env=None):
    """
    Cross-version subprocess runner for Python 3.4/XP environments.
    - Uses subprocess.Popen (subprocess.run is 3.5+)
    - Returns (returncode, stdout_text, stderr_text)
    - Accepts optional timeout (best-effort with polling for 3.4)
    - Accepts optional input_text (string) which will be encoded to bytes
    This consolidates repetitive Popen/communicate/decode blocks.
    """
    import subprocess
    try:
        # Prepare stdin if input is provided
        stdin_pipe = subprocess.PIPE if input_text is not None else None
        p = subprocess.Popen(
            cmd,
            stdin=stdin_pipe,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            cwd=cwd,
            env=env
        )
        if timeout is None:
            out_bytes, err_bytes = p.communicate(
                input=input_text.encode('utf-8') if isinstance(input_text, str) else input_text
            )
            return p.returncode, _decode_bytes(out_bytes), _decode_bytes(err_bytes)
        # Implement simple timeout loop compatible with 3.4
        import time
        start_time = time.time()
        while True:
            if p.poll() is not None:
                out_bytes, err_bytes = p.communicate()
                return p.returncode, _decode_bytes(out_bytes), _decode_bytes(err_bytes)
            if time.time() - start_time > timeout:
                try:
                    p.kill()
                except Exception:
                    try:
                        p.terminate()
                    except Exception:
                        pass
                out_bytes, err_bytes = p.communicate()
                return 124, _decode_bytes(out_bytes), _decode_bytes(err_bytes)
            time.sleep(0.05)
    except Exception as e:
        # Standardize failure surface
        return 1, '', str(e)

def file_is_ascii(file_path):
    """
    Return True if the given file can be read as ASCII-only.
    Consolidates repeated try/open/decode blocks into one helper.
    """
    try:
        if not os.path.exists(file_path):
            return False
        # Use strict ASCII to detect any non-ASCII characters
        f = open(file_path, 'r')
        try:
            # Explicit codec arg not supported in some XP Python builds for text mode
            # so we emulate by checking ordinals while reading
            data = f.read()
        finally:
            try:
                f.close()
            except Exception:
                pass
        try:
            data.encode('ascii')
            return True
        except Exception:
            return False
    except Exception:
        return False

def check_ascii_files(paths):
    """
    Given a list of paths (absolute or relative), return a list of those that
    contain non-ASCII characters or could not be checked. This replaces
    duplicated loops in various verification scripts.
    """
    problematic = []
    try:
        for p in paths:
            # Normalize relative to current working directory for consistency
            if not os.path.isabs(p):
                abs_p = os.path.abspath(p)
            else:
                abs_p = p
            if not file_is_ascii(abs_p):
                problematic.append(p)
    except Exception:
        # If a failure occurs mid-scan, return what we have so far
        return problematic
    return problematic

def sanitize_log(message):
    # Simple masking: replace DOB-like with ****-**-**, IDs with last4
    import re
    message = re.sub(r'\d{4}-\d{2}-\d{2}', '****-**-**', message)  # DOB
    message = re.sub(r'\d{9,}', lambda m: '***' + m.group(0)[-4:], message)  # IDs
    return message

# --- Internet Connectivity Check (Centralized) ---

def check_internet_connection(max_retries=3, initial_delay=1):
    """
    Central internet connectivity check function with automatic retry logic.
    Retries with exponential backoff if the initial check fails, to handle finicky connections.
    
    This is the central function used by both MediBot and MediLink modules.
    It respects TestMode configuration and provides robust retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1)
    
    Returns: 
        Boolean indicating internet connectivity status.
    """
    # Check if TestMode is enabled (if config loader is available)
    try:
        config_loader = get_shared_config_loader()
        if config_loader:
            config, _ = config_loader.load_configuration()
            if config.get("MediLink_Config", {}).get("TestMode", False):
                # If TestMode is True, skip the connectivity check and return True
                return True
    except Exception:
        # If config loading fails, continue with normal check
        pass
    
    # Try to use requests if available (faster method)
    try:
        import requests
        for attempt in range(max_retries):
            try:
                # Use lightweight endpoint with short timeout
                # Explicitly close connection to prevent script from hanging
                resp = requests.get("http://www.google.com", timeout=5, allow_redirects=False)
                resp.close()  # Explicitly close connection
                return True
            except Exception:
                # If this wasn't the last attempt, sleep before retrying
                if attempt < max_retries - 1:
                    delay = initial_delay * (attempt + 1)  # Exponential backoff: 1s, 2s, 3s, etc.
                    time.sleep(delay)
    except ImportError:
        # requests not available, fall through to ping method
        pass
    
    # Fallback: use ping as a lightweight reachability check (XP compatible)
    for attempt in range(max_retries):
        try:
            # Run a ping command to a reliable external server (Google's DNS server)
            ping_process = subprocess.Popen(
                ["ping", "-n", "1", "8.8.8.8"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            ping_output, ping_error = ping_process.communicate()
            
            # Check if the ping was successful
            if "Reply from" in _decode_bytes(ping_output):
                return True
        except Exception as e:
            # Only log error on last attempt to avoid noise
            if attempt == max_retries - 1:
                try:
                    config_loader = get_shared_config_loader()
                    if config_loader and hasattr(config_loader, 'log'):
                        config_loader.log("An error occurred checking for internet connectivity: {}".format(e), level="WARNING")
                    else:
                        print("An error occurred checking for internet connectivity: {}".format(e))
                except Exception:
                    pass
        
        # If this wasn't the last attempt, sleep before retrying
        if attempt < max_retries - 1:
            delay = initial_delay * (attempt + 1)  # Exponential backoff: 1s, 2s, 3s, etc.
            time.sleep(delay)
    
    return False