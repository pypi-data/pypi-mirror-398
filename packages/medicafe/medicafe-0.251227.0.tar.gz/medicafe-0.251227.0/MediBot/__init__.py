# MediBot package
"""
MediBot - Medical Practice Data Entry Automation

MediBot provides automated data entry capabilities for medical practice
management systems, with focus on Medisoft automation.

Smart Import Integration:
    Instead of importing MediBot modules directly, use the MediCafe smart
    import system for better dependency management and to avoid circular imports.
    
    Examples:
        # Get everything for MediBot preprocessor work
        from MediCafe import setup_for_medibot
        components = setup_for_medibot('medibot_preprocessor')
        
        # Get specific MediBot components
        from MediCafe import get_components
        medibot_main = get_components('medibot_main')
"""

__version__ = "0.251227.0"
__author__ = "Daniel Vidaud"
__email__ = "daniel@personalizedtransformation.com"

# Provide information about smart import integration
def get_smart_import_info():
    """Get information about using MediBot with the smart import system."""
    return {
        'recommended_approach': 'Use MediCafe smart import system',
        'setup_function': 'setup_for_medibot(module_type)',
        'available_module_types': [
            'medibot_preprocessor',
            'medibot_ui', 
            'medibot_crosswalk',
            'medibot_document_processing'
        ],
        'example': """
# Recommended usage:
from MediCafe import setup_for_medibot
components = setup_for_medibot('medibot_preprocessor')

# Access components:
api_core = components.get('api_core')
logging_config = components.get('logging_config')
preprocessor_lib = components.get('medibot_preprocessor_lib')
"""
    }

# Show smart import guide
def show_smart_import_guide():
    """Display a guide for using MediBot with smart imports."""
    info = get_smart_import_info()
    print("MediBot Smart Import Guide")
    print("=" * 40)
    print("Recommended approach: {}".format(info['recommended_approach']))
    print("Setup function: {}".format(info['setup_function']))
    print("\nAvailable module types:")
    for module_type in info['available_module_types']:
        print("  - {}".format(module_type))
    print("\nExample usage:\n{}".format(info['example']))

# Legacy import warning
def _show_legacy_warning():
    """Show a warning about direct imports."""
    import warnings
    warnings.warn(
        "Direct MediBot imports may cause circular dependencies. "
        "Consider using 'from MediCafe import setup_for_medibot' instead.",
        FutureWarning,
        stacklevel=3
    )

# Package metadata
__all__ = [
    '__version__',
    '__author__', 
    '__email__',
    'get_smart_import_info',
    'show_smart_import_guide',
    'MediBot_Preprocessor_lib'
]

# Export key modules for backward compatibility
try:
    from . import MediBot_Preprocessor_lib
except ImportError:
    # Fallback if module is not available
    MediBot_Preprocessor_lib = None

# Optional: Show guide on import (can be disabled)
import os
if os.environ.get('MEDIBOT_SHOW_SMART_IMPORT_GUIDE', '').lower() == 'true':
    try:
        show_smart_import_guide()
    except:
        pass