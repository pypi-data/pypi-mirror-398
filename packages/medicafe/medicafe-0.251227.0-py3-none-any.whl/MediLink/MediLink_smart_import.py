#MediLink_smart_import.py
"""
Upgraded MediLink main module using MediCafe Smart Import System

This is a demonstration of how MediLink_main.py should be migrated to use the
new centralized smart import system, eliminating complex imports and
circular dependency risks.
"""

import os, sys, time

# Add workspace directory to Python path for MediCafe imports
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(current_dir)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

# NEW SMART IMPORT APPROACH - Replace all complex imports with this
from MediCafe import setup_for_medilink, get_components, get_api_access

print("[*] Loading MediLink components via smart import system...")

# Get everything needed for MediLink main functionality
try:
    components = setup_for_medilink('medilink_main')
    print("[+] Loaded {} components for MediLink main".format(len(components)))
    
    # Extract core components
    api_core = components.get('api_core')
    logging_config = components.get('logging_config')
    core_utils = components.get('core_utils')
    
    # MediLink specific components
    medilink_datamgmt = components.get('medilink_datamgmt')
    medilink_parser = components.get('medilink_parser')
    medilink_up = components.get('medilink_up')
    medilink_down = components.get('medilink_down')
    medilink_ui = components.get('medilink_ui')
    medilink_patient_processor = components.get('medilink_patient_processor')
    
    print("[+] MediLink components extracted")
    
except Exception as e:
    print("[!] Some components unavailable (expected in dev): {}".format(e))
    # Fallback to individual components
    try:
        api_core = get_components('api_core', silent_fail=True)
        logging_config = get_components('logging_config', silent_fail=True)
        core_utils = get_components('core_utils', silent_fail=True)
        # Initialize MediLink components as None for fallback
        medilink_datamgmt = None
        medilink_parser = None
        medilink_up = None
        medilink_down = None
        medilink_ui = None
        medilink_patient_processor = None
        print("[+] Fallback to core components")
    except Exception as e:
        # Keep non-blocking behavior; include reason for easier debugging
        print("[-] Smart import system not available: {}".format(e))
        api_core = None
        logging_config = None
        core_utils = None
        medilink_datamgmt = None
        medilink_parser = None
        medilink_up = None
        medilink_down = None
        medilink_ui = None
        medilink_patient_processor = None

# Configuration loader setup
MediLink_ConfigLoader = None
if core_utils:
    try:
        get_shared_config_loader = getattr(core_utils, 'get_shared_config_loader', None)
        if get_shared_config_loader:
            MediLink_ConfigLoader = get_shared_config_loader()
            print("[+] Configuration loader initialized")
    except Exception as e:
        print("[!] Configuration loader issue: {}".format(e))

# Performance logging setup
PERFORMANCE_LOGGING = False
if logging_config:
    try:
        PERFORMANCE_LOGGING = getattr(logging_config, 'PERFORMANCE_LOGGING', False)
        print("[+] Performance logging: {}".format(PERFORMANCE_LOGGING))
    except Exception as e:
        print("[!] Performance logging setup issue: {}".format(e))

# Legacy import compatibility
try:
    from tqdm import tqdm
    print("[+] tqdm available")
except ImportError:
    # Fallback for when tqdm is not available
    def tqdm(iterable, **kwargs):
        return iterable
    print("[!] tqdm not available - using fallback")

# Module function extraction (if components are available)
def get_medilink_function(component, function_name):
    """Extract a function from a MediLink component safely."""
    if component:
        return getattr(component, function_name, None)
    return None

# Main menu function using smart imports
def main_menu():
    """
    Main menu using smart import system.
    All component access is now centralized and safe.
    """
    print("\n[*] MediLink Starting with Smart Import System")
    print("=" * 50)
    
    # Check component availability
    components_status = {
        'Configuration': MediLink_ConfigLoader is not None,
        'API Access': api_core is not None,
        'Data Management': medilink_datamgmt is not None,
        'Parser': medilink_parser is not None,
        'Upload Module': medilink_up is not None,
        'Download Module': medilink_down is not None,
        'UI Module': medilink_ui is not None,
        'Patient Processor': medilink_patient_processor is not None
    }
    
    print("Component Status:")
    for component, status in components_status.items():
        status_icon = "[+]" if status else "[!]"
        print("  {} {}".format(status_icon, component))
    
    # Get API access suite for additional functionality
    try:
        api_suite = get_api_access()
        print("[+] API suite loaded with {} components".format(len(api_suite)))
    except Exception as e:
        print("[!] API suite issue: {}".format(e))
    
    print("\n[i] Smart Import Benefits:")
    print("  - No complex import chains")
    print("  - No circular dependency risks")
    print("  - Graceful component fallbacks")
    print("  - Centralized configuration")
    print("  - Easy testing and validation")
    
    return components_status

def demonstrate_claim_processing():
    """Demonstrate claim processing with smart imports."""
    print("\n[*] Claim Processing Demo")
    print("-" * 30)
    
    try:
        # Get specialized components for claim processing
        claim_components = setup_for_medilink('medilink_claim_processing')
        print("[+] Loaded {} claim processing components".format(len(claim_components)))
        
        # Extract claim-specific components
        encoder_837p = claim_components.get('medilink_837p_encoder')
        utilities_837p = claim_components.get('medilink_837p_utilities')
        claim_status = claim_components.get('medilink_claim_status')
        
        if encoder_837p:
            print("[+] 837P encoder ready")
        if utilities_837p:
            print("[+] 837P utilities ready")
        if claim_status:
            print("[+] Claim status module ready")
        
        return True
        
    except Exception as e:
        print("[!] Claim processing setup issue: {}".format(e))
        return False

def demonstrate_deductible_processing():
    """Demonstrate deductible processing with smart imports."""
    print("\n[*] Deductible Processing Demo")
    print("-" * 30)
    
    try:
        # Get specialized components for deductible processing
        deductible_components = setup_for_medilink('medilink_deductible_processing')
        print("[+] Loaded {} deductible processing components".format(len(deductible_components)))
        
        # Extract deductible-specific components
        deductible_module = deductible_components.get('medilink_deductible')
        deductible_validator = deductible_components.get('medilink_deductible_validator')
        insurance_utils = deductible_components.get('medilink_insurance_utils')
        
        if deductible_module:
            print("[+] Deductible module ready")
        if deductible_validator:
            print("[+] Deductible validator ready")
        if insurance_utils:
            print("[+] Insurance utilities ready")
        
        return True
        
    except Exception as e:
        print("[!] Deductible processing setup issue: {}".format(e))
        return False

def demonstrate_communication():
    """Demonstrate communication functionality with smart imports."""
    print("\n[*] Communication Demo")
    print("-" * 30)
    
    try:
        # Get specialized components for communication
        comm_components = setup_for_medilink('medilink_communication')
        print("[+] Loaded {} communication components".format(len(comm_components)))
        
        # Extract communication-specific components
        gmail_module = comm_components.get('medilink_gmail')
        mailer_module = comm_components.get('medilink_mailer')
        display_utils = comm_components.get('medilink_display_utils')
        
        if gmail_module:
            print("[+] Gmail module ready")
        if mailer_module:
            print("[+] Mailer module ready")
        if display_utils:
            print("[+] Display utilities ready")
        
        return True
        
    except Exception as e:
        print("[!] Communication setup issue: {}".format(e))
        return False

def main():
    """Main function demonstrating smart import usage."""
    start_time = time.time()
    
    if PERFORMANCE_LOGGING:
        print("Performance logging enabled")
    
    # Run main menu
    status = main_menu()
    
    # Demonstrate different module types
    print("\n[*] Testing Specialized Module Types:")
    demonstrate_claim_processing()
    demonstrate_deductible_processing()
    demonstrate_communication()
    
    end_time = time.time()
    print("\n[*] Total initialization time: {:.2f} seconds".format(end_time - start_time))
    
    # Summary
    available_components = sum(status.values())
    total_components = len(status)
    print("\n[*] Summary: {}/{} components available".format(available_components, total_components))
    
    return available_components > 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[+] MediLink smart import demonstration completed successfully!")
    else:
        print("\n[-] MediLink smart import demonstration had issues")