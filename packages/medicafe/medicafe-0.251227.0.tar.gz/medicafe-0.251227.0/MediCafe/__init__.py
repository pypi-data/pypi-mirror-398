# MediCafe package
"""
MediCafe - Medical Practice Management Automation Suite

A comprehensive suite for automating medical administrative tasks in Medisoft.
Includes MediBot for data entry automation and MediLink for claims processing.

Smart Import System:
    The MediCafe package now includes a smart import system that provides
    centralized component management for all MediBot and MediLink modules.
    
    Quick Start:
        # Get specific components
        from MediCafe import get_components
        api_core, logging_config = get_components('api_core', 'logging_config')
        
        # Setup for MediBot
        from MediCafe import setup_for_medibot
        components = setup_for_medibot('medibot_preprocessor')
        
        # Setup for MediLink  
        from MediCafe import setup_for_medilink
        components = setup_for_medilink('medilink_main')
        
        # Get complete API access
        from MediCafe import get_api_access
        api_suite = get_api_access()
"""

__version__ = "0.251227.0"
__author__ = "Daniel Vidaud"
__email__ = "daniel@personalizedtransformation.com"

# Import and expose the smart import system
try:
    from .smart_import import (
        # Main interface
        get_components,
        
        # Convenience functions
        get_api_access,
        get_logging,
        get_core_utils,
        setup_for_medibot,
        setup_for_medilink,
        
        # Discovery functions
        list_components,
        list_module_types,
        describe_module_type,
        
        # Validation and utilities
        validate_setup,
        show_usage_examples
    )
    
    # Mark smart import system as available
    __smart_import_available__ = True
    
except Exception as e:
    # Fallback if smart import system is not available or raises any error
    __smart_import_available__ = False
    
    def _smart_import_unavailable(*args, **kwargs):
        raise ImportError("MediCafe Smart Import System is not available: {}".format(e))
    
    # Provide error functions for missing imports
    get_components = _smart_import_unavailable
    get_api_access = _smart_import_unavailable
    get_logging = _smart_import_unavailable
    get_core_utils = _smart_import_unavailable
    setup_for_medibot = _smart_import_unavailable
    setup_for_medilink = _smart_import_unavailable
    list_components = _smart_import_unavailable
    list_module_types = _smart_import_unavailable
    describe_module_type = _smart_import_unavailable
    validate_setup = _smart_import_unavailable
    show_usage_examples = _smart_import_unavailable

# Legacy imports for backward compatibility
__legacy_imports_available__ = True
try:
    from . import api_core
except Exception as e:
    __legacy_imports_available__ = False
    print("[MediCafe] Warning: Failed to import api_core: {}".format(e))

try:
    from . import logging_config
except Exception as e:
    if __legacy_imports_available__:  # Only set once, avoid redundant assignments
        __legacy_imports_available__ = False
    print("[MediCafe] Warning: Failed to import logging_config: {}".format(e))

try:
    from . import core_utils
except Exception as e:
    if __legacy_imports_available__:  # Only set once, avoid redundant assignments
        __legacy_imports_available__ = False
    print("[MediCafe] Warning: Failed to import core_utils: {}".format(e))

try:
    from . import MediLink_ConfigLoader
except Exception as e:
    if __legacy_imports_available__:  # Only set once, avoid redundant assignments
        __legacy_imports_available__ = False
    print("[MediCafe] Warning: Failed to import MediLink_ConfigLoader: {}".format(e))

# Package information
__all__ = [
    # Smart import system
    'get_components',
    'get_api_access', 
    'get_logging',
    'get_core_utils',
    'setup_for_medibot',
    'setup_for_medilink',
    'list_components',
    'list_module_types', 
    'describe_module_type',
    'validate_setup',
    'show_usage_examples',
    
    # Core modules (legacy compatibility)
    'MediLink_ConfigLoader',
    'core_utils',
    'api_core',
    'logging_config',
    
    # Package metadata
    '__version__',
    '__author__',
    '__email__',
    '__smart_import_available__',
    '__legacy_imports_available__'
]

def get_package_info():
    """Get information about the MediCafe package and its capabilities."""
    info = {
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'smart_import_available': __smart_import_available__,
        'legacy_imports_available': __legacy_imports_available__
    }
    
    if __smart_import_available__:
        try:
            info['available_components'] = len(list_components())
            info['available_module_types'] = len(list_module_types())
        except:
            info['available_components'] = 'unknown'
            info['available_module_types'] = 'unknown'
    
    return info

def quick_start_guide():
    """Display a quick start guide for using MediCafe."""
    guide = """
    MediCafe Quick Start Guide
    =========================
    
    1. Basic Usage - Get specific components:
       from MediCafe import get_components
       api_core, logging = get_components('api_core', 'logging_config')
    
    2. MediBot Setup - Get everything for MediBot:
       from MediCafe import setup_for_medibot
       components = setup_for_medibot('medibot_preprocessor')
       
    3. MediLink Setup - Get everything for MediLink:
       from MediCafe import setup_for_medilink  
       components = setup_for_medilink('medilink_main')
       
    4. API Access - Get complete API suite:
       from MediCafe import get_api_access
       api_suite = get_api_access()
       
    5. Discovery - See what's available:
       from MediCafe import list_components, list_module_types
       print("Components:", list_components())
       print("Module types:", list_module_types())
    
    6. Validation - Test the system:
       from MediCafe import validate_setup
       validate_setup()
    """
    print(guide)

# Auto-validation message (only if smart import is available)
if __smart_import_available__:
    try:
        # Silent validation on package import
        pass
    except:
        pass 