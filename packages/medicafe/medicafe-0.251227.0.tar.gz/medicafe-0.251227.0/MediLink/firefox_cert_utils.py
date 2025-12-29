"""
Firefox Certificate Exception Diagnostic Utilities

Provides diagnostic functions to analyze Firefox certificate exception storage
(cert_override.txt) to identify why certificate exceptions aren't working.

Python 3.4.4 compatible - uses os.path instead of pathlib.
"""

import os
import platform

# Try to import centralized logging
try:
    from MediCafe.core_utils import get_shared_config_loader
    _config_loader = get_shared_config_loader()
    if _config_loader:
        _central_log = _config_loader.log
    else:
        _central_log = None
except ImportError:
    _central_log = None


def _get_firefox_profile_paths():
    """
    Get potential Firefox profile directory paths for Windows XP and modern Windows.
    
    Returns:
        list: List of potential profile directory paths to check
    """
    paths = []
    
    # Try APPDATA environment variable first (works on both XP and modern Windows)
    appdata = os.environ.get('APPDATA')
    if appdata:
        mozilla_path = os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles')
        if os.path.exists(mozilla_path):
            paths.append(mozilla_path)
    
    # XP-specific path: Documents and Settings
    # Try expanduser for user home directory
    try:
        home_dir = os.path.expanduser('~')
        if home_dir and home_dir != '~':
            xp_appdata = os.path.join(home_dir, 'Application Data', 'Mozilla', 'Firefox', 'Profiles')
            if os.path.exists(xp_appdata) and xp_appdata not in paths:
                paths.append(xp_appdata)
    except Exception:
        pass
    
    # Also try the Documents and Settings path directly (XP)
    try:
        if platform.system() == 'Windows' and platform.release() == 'XP':
            username = os.environ.get('USERNAME') or os.environ.get('USER')
            if username:
                xp_path = os.path.join('C:\\Documents and Settings', username, 'Application Data', 'Mozilla', 'Firefox', 'Profiles')
                if os.path.exists(xp_path) and xp_path not in paths:
                    paths.append(xp_path)
    except Exception:
        pass
    
    return paths


def _find_firefox_profiles(profile_base_dir):
    """
    Find Firefox profile directories and determine the active/default profile.
    
    Args:
        profile_base_dir: Base directory containing Firefox profiles
        
    Returns:
        dict: {
            'profiles': list of profile directory paths,
            'default_profile': str or None (path to default profile),
            'profiles_ini_path': str or None
        }
    """
    result = {
        'profiles': [],
        'default_profile': None,
        'profiles_ini_path': None
    }
    
    if not os.path.exists(profile_base_dir):
        return result
    
    # Look for profiles.ini to identify default profile
    profiles_ini = os.path.join(os.path.dirname(profile_base_dir), 'profiles.ini')
    if os.path.exists(profiles_ini):
        result['profiles_ini_path'] = profiles_ini
        try:
            with open(profiles_ini, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Parse profiles.ini - look for Default=1 profiles with Path
                lines = content.split('\n')
                current_path = None
                is_relative = True  # Default is relative
                is_default = False
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('[Profile'):
                        # Start of new profile section - process previous one if it was default
                        if current_path and is_default:
                            # Profile path might be relative or absolute based on IsRelative
                            if is_relative:
                                profile_path = os.path.join(profile_base_dir, current_path)
                            else:
                                profile_path = current_path
                            
                            if os.path.exists(profile_path):
                                result['default_profile'] = profile_path
                                result['profiles'].append(profile_path)
                                # Found default, no need to continue
                                break
                        
                        # Reset for new profile
                        current_path = None
                        is_relative = True
                        is_default = False
                    elif line.startswith('Path='):
                        current_path = line.split('=', 1)[1]
                    elif line == 'Default=1':
                        is_default = True
                    elif line.startswith('IsRelative='):
                        is_relative_str = line.split('=', 1)[1].strip()
                        is_relative = (is_relative_str == '1')
                
                # Process last profile in file (if default wasn't found yet)
                if not result['default_profile'] and current_path and is_default:
                    if is_relative:
                        profile_path = os.path.join(profile_base_dir, current_path)
                    else:
                        profile_path = current_path
                    
                    if os.path.exists(profile_path):
                        result['default_profile'] = profile_path
                        result['profiles'].append(profile_path)
        except Exception:
            pass
    
    # If no default found via profiles.ini, scan for profile directories
    if not result['default_profile']:
        try:
            entries = os.listdir(profile_base_dir)
            for entry in entries:
                entry_path = os.path.join(profile_base_dir, entry)
                if os.path.isdir(entry_path):
                    # Firefox profiles typically contain prefs.js
                    prefs_js = os.path.join(entry_path, 'prefs.js')
                    if os.path.exists(prefs_js):
                        result['profiles'].append(entry_path)
                        # If no default yet, use the first one found (often most recent)
                        if not result['default_profile']:
                            result['default_profile'] = entry_path
        except Exception:
            pass
    
    return result


def _parse_cert_override_file(cert_override_path):
    """
    Parse Firefox cert_override.txt file to extract certificate exceptions.
    
    Format: host:port\t<fingerprint_hash>\t<error_bits>\t<timestamp>
    
    Args:
        cert_override_path: Path to cert_override.txt file
        
    Returns:
        list: List of parsed exception dictionaries
    """
    exceptions = []
    
    if not os.path.exists(cert_override_path):
        return exceptions
    
    try:
        with open(cert_override_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Split by tab
                parts = line.split('\t')
                if len(parts) >= 2:
                    host_port = parts[0].strip()
                    fingerprint = parts[1].strip()
                    error_bits = parts[2].strip() if len(parts) > 2 else ''
                    timestamp = parts[3].strip() if len(parts) > 3 else ''
                    
                    # Parse host:port (use rsplit to handle IPv6 addresses like [::1]:8000)
                    if ':' in host_port:
                        try:
                            # Check for IPv6 format [::1]:port
                            if host_port.startswith('[') and ']:' in host_port:
                                bracket_end = host_port.index(']:')
                                host = host_port[1:bracket_end]
                                port_str = host_port[bracket_end + 2:]
                            else:
                                host, port_str = host_port.rsplit(':', 1)
                            port = int(port_str)
                        except (ValueError, AttributeError, IndexError):
                            # Invalid format, skip this line
                            continue
                    else:
                        host = host_port
                        port = None
                    
                    exceptions.append({
                        'host': host,
                        'port': port,
                        'host_port': host_port,
                        'stored_fingerprint': fingerprint,
                        'error_bits': error_bits,
                        'timestamp': timestamp,
                        'line_number': line_num
                    })
    except Exception:
        pass
    
    return exceptions


def diagnose_firefox_certificate_exceptions(cert_file, server_port=8000, firefox_path=None, log=None):
    """
    Diagnose Firefox certificate exception issues by analyzing cert_override.txt.
    
    Checks if Firefox is installed, finds the profile directory, reads certificate
    exceptions, and compares stored fingerprints with the current certificate.
    
    Args:
        cert_file: Path to current certificate file
        server_port: Server port number (default 8000)
        firefox_path: Optional path to Firefox executable (can be retrieved from config)
        log: Optional logging function (uses _central_log if available, else no-op)
    
    Returns:
        dict: Diagnostic results with the following structure:
            {
                'firefox_installed': bool,
                'firefox_path': str or None,
                'profile_found': bool,
                'profile_path': str or None,
                'cert_override_file_exists': bool,
                'cert_override_file_path': str or None,
                'exceptions_found': int,
                'matching_exceptions': list of exception dicts,
                'current_cert_fingerprint_sha1': str or None,
                'current_cert_fingerprint_sha256': str or None,
                'diagnosis': str,
                'recommendations': list of str,
                'errors': list of str
            }
    """
    # Use provided log function or fallback to central log or no-op
    log_fn = log if log else (_central_log if _central_log else lambda msg, level="INFO": None)
    
    result = {
        'firefox_installed': False,
        'firefox_path': None,
        'profile_found': False,
        'profile_path': None,
        'cert_override_file_exists': False,
        'cert_override_file_path': None,
        'exceptions_found': 0,
        'matching_exceptions': [],
        'current_cert_fingerprint_sha1': None,
        'current_cert_fingerprint_sha256': None,
        'diagnosis': 'Firefox not found or profile not accessible',
        'recommendations': [],
        'errors': []
    }
    
    # Check if Firefox executable exists (if path provided)
    if firefox_path and os.path.exists(firefox_path):
        result['firefox_installed'] = True
        result['firefox_path'] = firefox_path
    else:
        # Try common Firefox paths
        common_paths = [
            r'C:\Program Files\Mozilla Firefox\firefox.exe',
            r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
        ]
        for path in common_paths:
            if os.path.exists(path):
                result['firefox_installed'] = True
                result['firefox_path'] = path
                break
    
    # Get current certificate fingerprint using existing function
    try:
        from MediLink.gmail_http_utils import get_certificate_fingerprint
        fingerprint_data = get_certificate_fingerprint(cert_file, log=log_fn)
        result['current_cert_fingerprint_sha1'] = fingerprint_data.get('sha1')
        result['current_cert_fingerprint_sha256'] = fingerprint_data.get('sha256')
    except Exception as e:
        result['errors'].append("Failed to extract current certificate fingerprint: {}".format(str(e)))
        log_fn("Error getting certificate fingerprint: {}".format(e), level="DEBUG")
    
    # Find Firefox profile directories
    profile_base_dirs = _get_firefox_profile_paths()
    if not profile_base_dirs:
        result['errors'].append("Firefox profile directory not found")
        result['diagnosis'] = "Firefox profile directory not found. Firefox may not be installed or profile is in an unexpected location."
        result['recommendations'].append("Ensure Firefox is installed and has been run at least once to create a profile.")
        return result
    
    # Try each profile base directory
    profile_info = None
    for profile_base_dir in profile_base_dirs:
        profile_info = _find_firefox_profiles(profile_base_dir)
        if profile_info.get('default_profile'):
            break
    
    if not profile_info or not profile_info.get('default_profile'):
        result['errors'].append("No Firefox profiles found")
        result['diagnosis'] = "Firefox profiles directory found, but no valid profiles detected."
        result['recommendations'].append("Ensure Firefox has been run at least once to create a profile.")
        return result
    
    result['profile_found'] = True
    result['profile_path'] = profile_info['default_profile']
    
    # Look for cert_override.txt
    cert_override_path = os.path.join(profile_info['default_profile'], 'cert_override.txt')
    if os.path.exists(cert_override_path):
        result['cert_override_file_exists'] = True
        result['cert_override_file_path'] = cert_override_path
    else:
        result['errors'].append("cert_override.txt not found in profile directory")
        result['diagnosis'] = "Firefox profile found, but cert_override.txt does not exist. No certificate exceptions have been added yet."
        result['recommendations'].append("Add a certificate exception in Firefox by navigating to https://127.0.0.1:{} and clicking 'Add Exception'.".format(server_port))
        return result
    
    # Parse cert_override.txt
    try:
        exceptions = _parse_cert_override_file(cert_override_path)
        result['exceptions_found'] = len(exceptions)
        
        # Find matching exceptions for our server
        matching_hosts = ['127.0.0.1', 'localhost', '::1']
        for exc in exceptions:
            # Match if host matches and port matches (port must not be None)
            if exc['host'] in matching_hosts and exc['port'] is not None and exc['port'] == server_port:
                # Compare fingerprints
                stored_fp_raw = exc.get('stored_fingerprint', '') or ''
                stored_fp = stored_fp_raw.replace(':', '').replace('-', '').lower() if stored_fp_raw else ''
                current_fp_sha1 = result['current_cert_fingerprint_sha1']
                
                matches = False
                mismatch_reason = None
                
                if current_fp_sha1:
                    # Firefox stores SHA-1 fingerprints
                    if stored_fp == current_fp_sha1:
                        matches = True
                    else:
                        mismatch_reason = "Stored fingerprint does not match current certificate fingerprint"
                else:
                    mismatch_reason = "Could not extract current certificate fingerprint for comparison"
                
                exc_result = {
                    'host': exc['host'],
                    'port': exc['port'],
                    'stored_fingerprint': exc['stored_fingerprint'],
                    'error_bits': exc['error_bits'],
                    'timestamp': exc['timestamp'],
                    'matches_current_cert': matches,
                    'current_fingerprint': current_fp_sha1,
                    'mismatch_reason': mismatch_reason
                }
                result['matching_exceptions'].append(exc_result)
    except Exception as e:
        result['errors'].append("Error parsing cert_override.txt: {}".format(str(e)))
        log_fn("Error parsing cert_override.txt: {}".format(e), level="DEBUG")
    
    # Generate diagnosis and recommendations
    if result['matching_exceptions']:
        matching = result['matching_exceptions'][0]
        if matching['matches_current_cert']:
            result['diagnosis'] = "Certificate exception found and fingerprint matches current certificate. Exception should be working."
            result['recommendations'].append("If connection still fails, try closing and reopening Firefox completely.")
            result['recommendations'].append("Check Firefox's certificate manager (Options > Privacy & Security > Certificates > View Certificates > Servers tab).")
        else:
            result['diagnosis'] = "Certificate exception found but fingerprint does not match current certificate. Certificate may have been regenerated."
            result['recommendations'].append("Remove the old exception from Firefox certificate manager.")
            result['recommendations'].append("Add a new exception by navigating to https://127.0.0.1:{}".format(server_port))
    elif result['exceptions_found'] > 0:
        result['diagnosis'] = "Certificate exceptions exist in Firefox, but none match {}:{}".format('127.0.0.1', server_port)
        result['recommendations'].append("Add a certificate exception for {}:{}".format('127.0.0.1', server_port))
    else:
        result['diagnosis'] = "No certificate exceptions found in Firefox profile."
        result['recommendations'].append("Add a certificate exception by navigating to https://127.0.0.1:{} and clicking 'Add Exception'.".format(server_port))
    
    return result

