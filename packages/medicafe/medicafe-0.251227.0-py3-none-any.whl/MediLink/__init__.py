# MediLink package
"""
MediLink - Medical Claims Processing and Data Management

MediLink provides comprehensive claims processing, data management, and
communication capabilities for medical practice management.

Smart Import Integration:
    Instead of importing MediLink modules directly, use the MediCafe smart
    import system for better dependency management and to avoid circular imports.
    
    Examples:
        # Get everything for MediLink main functionality
        from MediCafe import setup_for_medilink
        components = setup_for_medilink('medilink_main')
        
        # Get everything for claims processing
        components = setup_for_medilink('medilink_claim_processing')
        
        # Get specific MediLink components
        from MediCafe import get_components
        datamgmt = get_components('medilink_datamgmt')
"""

__version__ = "0.251227.0"
__author__ = "Daniel Vidaud"
__email__ = "daniel@personalizedtransformation.com"

# Provide information about smart import integration
def get_smart_import_info():
    """Get information about using MediLink with the smart import system."""
    return {
        'recommended_approach': 'Use MediCafe smart import system',
        'setup_function': 'setup_for_medilink(module_type)',
        'available_module_types': [
            'medilink_main',
            'medilink_claim_processing',
            'medilink_deductible_processing', 
            'medilink_communication',
            'medilink_data_management'
        ],
        'example': """
# Recommended usage:
from MediCafe import setup_for_medilink
components = setup_for_medilink('medilink_claim_processing')

# Access components:
api_core = components.get('api_core')
datamgmt = components.get('medilink_datamgmt')
encoder = components.get('medilink_837p_encoder')
"""
    }

# Show smart import guide
def show_smart_import_guide():
    """Display a guide for using MediLink with smart imports."""
    info = get_smart_import_info()
    print("MediLink Smart Import Guide")
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
        "Direct MediLink imports may cause circular dependencies. "
        "Consider using 'from MediCafe import setup_for_medilink' instead.",
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
    'MediLink_insurance_utils'
]

# Export key modules for backward compatibility
try:
    from . import MediLink_insurance_utils
except ImportError as e:
    # Fallback if module is not available
    import sys
    print("Warning: MediLink.MediLink_insurance_utils import failed: {}".format(e))
    print("This is a non-critical import failure. MediLink will continue to function.")
    MediLink_insurance_utils = None
except Exception as e:
    # Handle any other import errors
    import sys
    print("Warning: Unexpected error importing MediLink_insurance_utils: {}".format(e))
    print("This may be due to missing configuration files. MediLink will continue to function.")
    MediLink_insurance_utils = None

# Optional: Show guide on import (can be disabled)
import os
if os.environ.get('MEDILINK_SHOW_SMART_IMPORT_GUIDE', '').lower() == 'true':
    try:
        show_smart_import_guide()
    except:
        pass 