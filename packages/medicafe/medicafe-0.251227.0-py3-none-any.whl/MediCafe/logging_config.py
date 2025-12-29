# MediCafe/logging_config.py
"""
Centralized logging configuration for MediCafe package.
This module contains all logging control flags that can be imported by any module.

CONFIG FILE SETUP:
To configure logging flags, add the following to your config.json file:

{
  "MediLink_Config": {
    "DEBUG": true,              // Enable verbose API call logging and processing messages
    "CONSOLE_LOGGING": true,    // Enable console logging output
    "PERFORMANCE_LOGGING": false // Enable performance timing messages
  }
}

All flags default to False if not present in the config file.
"""

# =============================================================================
# CONFIG LOADING FUNCTION
# =============================================================================

def _env_true(var_name, default=False):
    try:
        import os
        value = os.environ.get(var_name, None)
        if value is None:
            return default
        value_l = str(value).strip().lower()
        return value_l in ('1', 'true', 'yes', 'on')
    except Exception:
        return default

def _load_logging_flags_from_config():
    """
    Load logging flags from config file with fallback defaults.
    Returns a dictionary with the logging flags.
    """
    # Default values
    default_flags = {
        'DEBUG': False,
        'CONSOLE_LOGGING': False,
        'PERFORMANCE_LOGGING': False
    }
    
    try:
        # Use MediCafe config loader
        from MediCafe.MediLink_ConfigLoader import load_configuration
        config, crosswalk = load_configuration()
        
        # Get logging flags from MediLink_Config section
        medi_config = config.get('MediLink_Config', {})
        
        flags = {}
        flags['DEBUG'] = medi_config.get('DEBUG', default_flags['DEBUG'])
        flags['CONSOLE_LOGGING'] = medi_config.get('CONSOLE_LOGGING', default_flags['CONSOLE_LOGGING'])
        flags['PERFORMANCE_LOGGING'] = medi_config.get('PERFORMANCE_LOGGING', default_flags['PERFORMANCE_LOGGING'])

        # Environment overrides (session-level control)
        # MEDICAFE_DEBUG, MEDICAFE_CONSOLE_LOGGING, MEDICAFE_PERFORMANCE_LOGGING
        if _env_true('MEDICAFE_DEBUG', None) is not None:
            flags['DEBUG'] = _env_true('MEDICAFE_DEBUG', flags['DEBUG'])
        if _env_true('MEDICAFE_CONSOLE_LOGGING', None) is not None:
            flags['CONSOLE_LOGGING'] = _env_true('MEDICAFE_CONSOLE_LOGGING', flags['CONSOLE_LOGGING'])
        if _env_true('MEDICAFE_PERFORMANCE_LOGGING', None) is not None:
            flags['PERFORMANCE_LOGGING'] = _env_true('MEDICAFE_PERFORMANCE_LOGGING', flags['PERFORMANCE_LOGGING'])
        
        return flags
                
    except Exception as e:
        # If any error occurs during config loading, return defaults
        print("Warning: Could not load logging configuration from config file: {}".format(e))
        return default_flags

# =============================================================================
# LOGGING CONTROL FLAGS
# =============================================================================

# Load flags from config file with fallback defaults
_logging_flags = _load_logging_flags_from_config()

# DEBUG flag to control verbose API call logging and processing messages
DEBUG = _logging_flags['DEBUG']

# Console output control for logging
CONSOLE_LOGGING = _logging_flags['CONSOLE_LOGGING']

# Performance logging control
PERFORMANCE_LOGGING = _logging_flags['PERFORMANCE_LOGGING']

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def enable_debug_mode():
    """Enable all debug logging for troubleshooting"""
    global DEBUG, CONSOLE_LOGGING, PERFORMANCE_LOGGING
    DEBUG = True
    CONSOLE_LOGGING = True
    PERFORMANCE_LOGGING = True

def enable_performance_mode():
    """Enable only performance logging for timing analysis"""
    global DEBUG, CONSOLE_LOGGING, PERFORMANCE_LOGGING
    DEBUG = False
    CONSOLE_LOGGING = False
    PERFORMANCE_LOGGING = True

def enable_quiet_mode():
    """Enable quiet mode with minimal output"""
    global DEBUG, CONSOLE_LOGGING, PERFORMANCE_LOGGING
    DEBUG = False
    CONSOLE_LOGGING = False
    PERFORMANCE_LOGGING = False

def get_logging_status():
    """Get current logging configuration status"""
    return {
        'DEBUG': DEBUG,
        'CONSOLE_LOGGING': CONSOLE_LOGGING,
        'PERFORMANCE_LOGGING': PERFORMANCE_LOGGING
    }

def print_logging_status():
    """Print current logging configuration status"""
    status = get_logging_status()
    print("Current Logging Configuration:")
    print("  DEBUG: {}".format(status['DEBUG']))
    print("  CONSOLE_LOGGING: {}".format(status['CONSOLE_LOGGING']))
    print("  PERFORMANCE_LOGGING: {}".format(status['PERFORMANCE_LOGGING']))

def reload_logging_config():
    """Reload logging configuration from config file"""
    global DEBUG, CONSOLE_LOGGING, PERFORMANCE_LOGGING, _logging_flags
    
    _logging_flags = _load_logging_flags_from_config()
    DEBUG = _logging_flags['DEBUG']
    CONSOLE_LOGGING = _logging_flags['CONSOLE_LOGGING']
    PERFORMANCE_LOGGING = _logging_flags['PERFORMANCE_LOGGING']
    
    print("Logging configuration reloaded from config file")
    print_logging_status() 