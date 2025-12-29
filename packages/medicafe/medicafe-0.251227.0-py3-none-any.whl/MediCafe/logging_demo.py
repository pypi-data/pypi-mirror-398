# MediCafe/logging_demo.py
"""
Demo script showing how to use the centralized logging configuration.
This demonstrates the different logging modes available.
"""

from MediCafe.logging_config import (
    DEBUG, CONSOLE_LOGGING, PERFORMANCE_LOGGING,
    enable_debug_mode, enable_performance_mode, enable_quiet_mode,
    get_logging_status, print_logging_status
)

def demo_logging_modes():
    """Demonstrate different logging modes"""
    
    print("=" * 60)
    print("MEDICAFE LOGGING CONFIGURATION DEMO")
    print("=" * 60)
    
    # Show initial status
    print("\n1. Initial Status:")
    print_logging_status()
    
    # Demo quiet mode
    print("\n2. Enabling Quiet Mode (minimal output):")
    enable_quiet_mode()
    print_logging_status()
    
    # Demo performance mode
    print("\n3. Enabling Performance Mode (timing only):")
    enable_performance_mode()
    print_logging_status()
    
    # Demo debug mode
    print("\n4. Enabling Debug Mode (full verbose output):")
    enable_debug_mode()
    print_logging_status()
    
    # Reset to quiet
    print("\n5. Resetting to Quiet Mode:")
    enable_quiet_mode()
    print_logging_status()
    
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES:")
    print("=" * 60)
    print("from MediCafe.logging_config import enable_debug_mode")
    print("enable_debug_mode()  # Enable all verbose logging")
    print("")
    print("from MediCafe.logging_config import enable_performance_mode")
    print("enable_performance_mode()  # Enable only timing messages")
    print("")
    print("from MediCafe.logging_config import enable_quiet_mode")
    print("enable_quiet_mode()  # Enable minimal output")
    print("")
    print("from MediCafe.logging_config import DEBUG, CONSOLE_LOGGING")
    print("if DEBUG: print('Debug message')")
    print("if CONSOLE_LOGGING: print('Console message')")

if __name__ == "__main__":
    demo_logging_modes() 