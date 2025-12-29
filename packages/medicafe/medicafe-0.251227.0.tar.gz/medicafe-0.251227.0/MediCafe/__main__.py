#!/usr/bin/env python3
"""
MediCafe Entry Point (__main__.py)

This module serves as the main entry point for the MediCafe package.
It can be called directly from the batch file and routes user choices
to the appropriate sub-applications without adding interface layers.

Usage:
    python -m MediCafe <command> [args...]
    
Commands:
    launcher [options]        - Launch interactive MediCafe UI menu
    medibot [config_file]     - Run MediBot data entry automation
    medilink                  - Run MediLink claims processing  
    claims_status             - Run United Claims Status checker
    deductible               - Run United Deductible checker
    download_emails          - Run email download functionality
    send_error_report   - Create and email a TEST support bundle
    version                  - Show MediCafe version information
    
The entry point preserves user choices and navigational flow from the
batch script without adding unnecessary interface layers.
"""

import sys
import os
import argparse
import subprocess
from MediCafe.core_utils import import_medilink_module, require_functions, print_import_diagnostics

# Set up module paths for proper imports
def setup_entry_point_paths():
    """Set up paths for the MediCafe entry point"""
    # Get the parent directory (workspace root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(current_dir)
    
    # Add to Python path if not already present
    workspace_str = workspace_root
    if workspace_str not in sys.path:
        sys.path.insert(0, workspace_str)
    
    # Ensure we do NOT add package directories directly; only project root should be on sys.path
    # Clean any existing direct package paths that could break package imports (e.g., 'MediLink' is not a package)
    for pkg_dir in (os.path.join(workspace_root, 'MediBot'), os.path.join(workspace_root, 'MediLink')):
        while pkg_dir in sys.path:
            sys.path.remove(pkg_dir)

def validate_critical_imports():
    """Validate key modules and capabilities before launching subprocesses.
    - Ensures we resolve the in-repo MediLink_DataMgmt and it exposes required functions.
    Behavior depends on env flags handled inside core_utils.require_functions.
    """
    try:
        datamgmt = import_medilink_module('MediLink_DataMgmt')
        if datamgmt is not None:
            print_import_diagnostics('MediLink_DataMgmt', datamgmt)
            # These are used by both MediBot and MediLink flows
            require_functions(datamgmt, ['read_general_fixed_width_data', 'read_fixed_width_data', 'parse_fixed_width_data'])
    except Exception as e:
        # Fail fast only if strict mode is enabled (exception originates from require_functions)
        print("Import validation warning: {}".format(e))

def run_medibot(config_file=None):
    """Run MediBot application"""
    try:
        print("Starting MediBot...")

        # Resolve workspace root and MediBot.py path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(current_dir)
        medibot_path = os.path.join(workspace_root, 'MediBot', 'MediBot.py')

        if not os.path.exists(medibot_path):
            print("Error: MediBot.py not found at {}".format(medibot_path))
            return 1

        # Pre-flight import validation (no-op unless strict/debug enabled)
        validate_critical_imports()

        # Build subprocess arguments
        args = [sys.executable, medibot_path]
        if config_file:
            args.append(config_file)

        # Ensure subprocess can import project packages
        env = os.environ.copy()
        python_path = workspace_root
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = python_path + os.pathsep + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = python_path

        # Run MediBot as a script so its __main__ block executes
        result = subprocess.call(args, cwd=os.path.dirname(medibot_path), env=env)
        return result

    except Exception as e:
        print("Error running MediBot: {}".format(e))
        return 1

def run_medilink():
    """Run MediLink application"""
    try:
        print("Starting MediLink...")
        # Pre-flight import validation (no-op unless strict/debug enabled)
        validate_critical_imports()
        # Use subprocess.call for Python 3.4.4 compatibility
        
        # Get the path to MediLink_main.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(current_dir)
        medilink_main_path = os.path.join(workspace_root, 'MediLink', 'MediLink_main.py')
        
        if os.path.exists(medilink_main_path):
            # Set up environment for subprocess to find MediCafe
            env = os.environ.copy()
            python_path = workspace_root
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = python_path + os.pathsep + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = python_path
            
            # Set working directory to MediLink directory for proper file paths
            medilink_dir = os.path.dirname(medilink_main_path)
            
            # Use subprocess.call for Python 3.4.4 compatibility
            result = subprocess.call([sys.executable, medilink_main_path], 
                                   cwd=medilink_dir,
                                   env=env)
            return result
        else:
            print("Error: MediLink_main.py not found at {}".format(medilink_main_path))
            return 1
        
    except ImportError as e:
        print("Error: Unable to import MediLink: {}".format(e))
        return 1
    except Exception as e:
        print("Error running MediLink: {}".format(e))
        return 1

def run_claims_status():
    """Run United Claims Status checker"""
    try:
        print("Starting United Claims Status...")
        # Use subprocess.call for Python 3.4.4 compatibility
        
        # Get the path to MediLink_ClaimStatus.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(current_dir)
        claims_status_path = os.path.join(workspace_root, 'MediLink', 'MediLink_ClaimStatus.py')
        
        if os.path.exists(claims_status_path):
            # Set up environment for subprocess to find MediCafe
            env = os.environ.copy()
            python_path = workspace_root
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = python_path + os.pathsep + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = python_path
            
            # Set working directory to MediLink directory for proper file paths
            medilink_dir = os.path.dirname(claims_status_path)
            
            # Use subprocess.call for Python 3.4.4 compatibility
            result = subprocess.call([sys.executable, claims_status_path], 
                                   cwd=medilink_dir,
                                   env=env)
            return result
        else:
            print("Error: MediLink_ClaimStatus.py not found at {}".format(claims_status_path))
            return 1
        
    except ImportError as e:
        print("Error: Unable to import MediLink_ClaimStatus: {}".format(e))
        return 1
    except Exception as e:
        print("Error running Claims Status: {}".format(e))
        return 1

def run_deductible():
    """Run United Deductible checker"""
    try:
        print("Starting United Deductible...")
        # Use subprocess.call for Python 3.4.4 compatibility
        
        # Get the path to MediLink_Deductible.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(current_dir)
        deductible_path = os.path.join(workspace_root, 'MediLink', 'MediLink_Deductible.py')
        
        if os.path.exists(deductible_path):
            # Set up environment for subprocess to find MediCafe
            env = os.environ.copy()
            python_path = workspace_root
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = python_path + os.pathsep + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = python_path
            
            # Set working directory to MediLink directory for proper file paths
            medilink_dir = os.path.dirname(deductible_path)
            
            # Use subprocess.call for Python 3.4.4 compatibility
            result = subprocess.call([sys.executable, deductible_path], 
                                   cwd=medilink_dir,
                                   env=env)
            return result
        else:
            print("Error: MediLink_Deductible.py not found at {}".format(deductible_path))
            return 1
        
    except ImportError as e:
        print("Error: Unable to import MediLink_Deductible: {}".format(e))
        return 1
    except Exception as e:
        print("Error running Deductible checker: {}".format(e))
        return 1

def run_download_emails():
    """Run email download functionality"""
    try:
        print("Starting email download...")
        # Use subprocess.call for Python 3.4.4 compatibility
        
        # Get the path to MediLink_Gmail.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(current_dir)
        medilink_gmail_path = os.path.join(workspace_root, 'MediLink', 'MediLink_Gmail.py')
        
        if os.path.exists(medilink_gmail_path):
            # Set up environment for subprocess to find MediCafe
            env = os.environ.copy()
            python_path = workspace_root
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = python_path + os.pathsep + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = python_path
            
            # Set working directory to MediLink directory for proper file paths
            medilink_dir = os.path.dirname(medilink_gmail_path)
            
            # Use subprocess.call for Python 3.4.4 compatibility
            result = subprocess.call([sys.executable, medilink_gmail_path], 
                                   cwd=medilink_dir,
                                   env=env)
            return result
        else:
            print("Error: MediLink_Gmail.py not found at {}".format(medilink_gmail_path))
            return 1
        
    except ImportError as e:
        print("Error: Unable to import MediLink_Gmail: {}".format(e))
        return 1

def show_version():
    """Show MediCafe version information"""
    try:
        from MediCafe import __version__, __author__
        print("MediCafe version {}".format(__version__))
        print("Author: {}".format(__author__))
        return 0
    except ImportError:
        print("MediCafe version information not available")
        return 1

def main():
    """Main entry point for MediCafe"""
    # Set up paths first
    setup_entry_point_paths()
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='MediCafe - Medical Practice Management Automation Suite',
        prog='python -m MediCafe'
    )
    
    parser.add_argument(
        'command',
        choices=['launcher', 'medibot', 'medilink', 'claims_status', 'deductible', 'download_emails', 'send_error_report', 'version'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'config_file',
        nargs='?',
        help='Configuration file path (for medibot command)'
    )
    
    # Parse arguments
    if len(sys.argv) < 2:
        parser.print_help()
        return 1
        
    args = parser.parse_args()
    
    # Route to appropriate function based on command
    try:
        if args.command == 'launcher':
            # Launcher has its own argument parser, so pass remaining args
            # Detect position of the 'launcher' token regardless of how python -m invoked us
            from MediCafe.launcher import main as launcher_main
            # Temporarily replace sys.argv so launcher's parser works correctly
            original_argv = sys.argv
            try:
                try:
                    launcher_index = original_argv.index('launcher')
                except ValueError:
                    launcher_index = 1  # default: treat everything after module as launcher args
                launcher_args = original_argv[launcher_index + 1:] if launcher_index + 1 < len(original_argv) else []
                sys.argv = [original_argv[0]] + launcher_args
                return launcher_main()
            finally:
                sys.argv = original_argv
        elif args.command == 'medibot':
            return run_medibot(args.config_file)
        elif args.command == 'medilink':
            return run_medilink()
        elif args.command == 'claims_status':
            return run_claims_status()
        elif args.command == 'deductible':
            return run_deductible()
        elif args.command == 'download_emails':
            return run_download_emails()
        elif args.command == 'send_error_report':
            # Import lazily and call directly to avoid middlemen
            from MediCafe.error_reporter import email_test_error_report_flow
            return email_test_error_report_flow()
        elif args.command == 'version':
            return show_version()
        else:
            print("Unknown command: {}".format(args.command))
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print("Unexpected error: {}".format(e))
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)