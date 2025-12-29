#!/usr/bin/env python
"""
High-level MediCafe launcher implemented in Python so that the legacy
MediBot.bat wrapper can remain tiny while all meaningful logic is handled
in one place.

The implementation focuses on:
  - Parsing the same flags that MediBot.bat understands today
  - Detecting XP production (F:\ based) versus Win11/dev environments
  - Handling the debug gates, migrations, CSV bootstrap, and menu routing
  - Delegating work to existing MediCafe/MediBot/MediLink modules
  - Providing a single failure wrapper that can trigger error bundles
    and rollback without duplicating the work already done inside the
    deeper scripts such as MediBot.py

Only Python 3.4 compatible language features are used so that the exact
same file can run on both XP SP3 and the Win11 dev workstation.
"""
from __future__ import print_function

import argparse
import hashlib
import json
import os
import sys
import subprocess
import tempfile
import shutil
import time

# Windows-specific console closing helper
def _exit_and_close_console():
    """Exit the process and attempt to close console window on Windows."""
    if os.name == 'nt':  # Windows
        # Use os._exit() to immediately terminate the process
        # This bypasses Python cleanup but ensures immediate exit
        # The console window should close when the process terminates
        os._exit(0)
    else:
        # On non-Windows, use normal exit
        sys.exit(0)

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

try:
    # These helpers already exist inside MediCafe and should be reused
    from MediCafe.error_reporter import collect_support_bundle, submit_support_bundle_email
except Exception:
    collect_support_bundle = None
    submit_support_bundle_email = None

try:
    from MediCafe.core_utils import check_internet_connection
except Exception:
    check_internet_connection = None


class LauncherError(Exception):
    """Base class for launcher-specific failures."""


class LauncherArgumentError(LauncherError):
    """Raised when CLI arguments cannot be parsed."""


class LauncherConfigError(LauncherError):
    """Raised when configuration validation fails."""


class LauncherArgumentParser(argparse.ArgumentParser):
    """Argument parser that raises instead of exiting so we can handle errors."""

    def error(self, message):
        raise LauncherArgumentError(message)


class SessionConfig(object):
    """Container for CLI + environment derived options."""

    def __init__(self, args):
        self.skip_startup_csv = args.skip_csv
        self.direct_action = args.direct_action
        self.debug_mode = args.debug_mode
        self.auto_menu_choice = args.auto_choice
        self.auto_menu_source = None

        allow_auto = os.environ.get('MEDICAFE_ALLOW_AUTO')
        env_choice = os.environ.get('MEDICAFE_AUTO_CHOICE')
        if (not self.auto_menu_choice) and allow_auto == '1' and env_choice:
            self.auto_menu_choice = env_choice.strip()
            self.auto_menu_source = 'ENV'
        elif self.auto_menu_choice:
            self.auto_menu_source = 'CLI'


class ErrorBundleCoordinator(object):
    """Centralize bundle creation to avoid duplicates and capture context."""

    def __init__(self):
        self.bundle_path = None
        self.bundle_signature = None

    def collect_once(self, context):
        if collect_support_bundle is None:
            return None
        signature = self._compute_signature(context)
        if signature and self.bundle_path and self.bundle_signature == signature and os.path.exists(self.bundle_path):
            return self.bundle_path
        if signature:
            last_sig = os.environ.get('MEDICAFE_LAST_ERROR_SIGNATURE')
            last_path = os.environ.get('MEDICAFE_LAST_BUNDLE_PATH')
            if last_sig == signature and last_path and os.path.exists(last_path):
                self.bundle_signature = signature
                self.bundle_path = last_path
                return last_path
        try:
            bundle = collect_support_bundle(include_traceback=True, extra_meta=context or {})
        except Exception as err:
            print('Failed to build support bundle: {0}'.format(err))
            return None
        if bundle:
            self.bundle_path = bundle
            self.bundle_signature = signature
            if signature:
                os.environ['MEDICAFE_LAST_ERROR_SIGNATURE'] = signature
            os.environ['MEDICAFE_LAST_BUNDLE_PATH'] = bundle
        return bundle

    def _compute_signature(self, context):
        if not context:
            return None
        try:
            serialized = json.dumps(context, sort_keys=True, default=str)
        except Exception:
            serialized = repr(context)
        return hashlib.sha1(serialized.encode('utf-8', 'ignore')).hexdigest()


def build_arg_parser():
    parser = LauncherArgumentParser(
        description='Python MediCafe UI orchestrator',
        prefix_chars='-/'  # Support both legacy /switch and modern --switch styles
    )
    parser.add_argument('--skip-csv', '/skip-csv', dest='skip_csv', action='store_true',
                        help='Skip automatic CSV processing on startup')
    parser.add_argument('--no-csv', '/no-csv', dest='skip_csv', action='store_true',
                        help='Alias for --skip-csv')
    parser.add_argument('--rollback', '/rollback', dest='direct_action', action='store_const',
                        const='rollback', help='Jump directly to rollback flow')
    parser.add_argument('--troubleshooting', '/troubleshooting', dest='direct_action',
                        action='store_const', const='troubleshooting',
                        help='Jump directly to troubleshooting menu')
    parser.add_argument('--auto-choice', '/auto-choice', dest='auto_choice', default=None,
                        help='Provide a menu choice non-interactively (single use)')
    parser.add_argument('--debug', '/debug', dest='debug_mode', action='store_true',
                        help='Open the debug gate immediately')
    parser.set_defaults(skip_csv=False, debug_mode=False, direct_action=None)
    return parser


class MediCafeOrchestrator(object):
    """Encapsulates startup, menu routing, and failure handling."""

    def __init__(self, session_config):
        self.session = session_config
        # New path calculation (file is now in MediCafe/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_root = os.path.dirname(current_dir)
        self.medibot_dir = os.path.join(self.repo_root, 'MediBot')
        self.cmd_exe = os.environ.get('COMSPEC', 'cmd.exe')
        self.python_exe = os.environ.get('MEDICAFE_PYTHON', sys.executable)
        self.startup_notices = []
        self.bundle_coordinator = ErrorBundleCoordinator()
        
        # Log error bundling system status
        if collect_support_bundle is not None:
            self._record_notice('INFO', 'Error bundling system active')
        else:
            self._record_notice('WARNING', 'Error bundling system unavailable (error_reporter import failed)')
        
        # Concern #1: Set working directory for consistent relative paths
        # This ensures all relative paths resolve correctly regardless of where
        # the script was invoked from (matches batch file behavior)
        os.chdir(self.repo_root)
        
        self.environment = self._resolve_environment()
        self.update_script = self.environment.get('upgrade_medicafe')
        self.update_available_version = None
        self.medicafe_version = None
        self.prepared = False
        self.failure_bundle_path = None

    # ------------------------------------------------------------------ #
    # Bootstrap helpers
    # ------------------------------------------------------------------ #
    def _resolve_environment(self):
        """Determine directory layout based on legacy F: drive availability.
        
        Two architectures are supported:
        1. Production (XP SP3): Uses F: drive and C:\MEDIANSI paths
        2. Development: Uses relative paths from repo_root
        
        Key paths on dev machine (relative to repo_root):
        - json/config.json, json/crosswalk.json
        - MediBot/DOWNLOADS/ for local storage
        - MediBot/update_json.py for scripts
        """
        env = {}
        env['medicafe_package'] = 'medicafe'

        # Production XP paths (absolute)
        env['source_folder_production'] = r'C:\MEDIANSI\MediCare'
        env['target_folder_production'] = r'C:\MEDIANSI\MediCare\CSV'
        env['python_script_production'] = r'C:\Python34\Lib\site-packages\MediBot\update_json.py'
        env['python_script2_production'] = r'C:\Python34\Lib\site-packages\MediBot\MediBot.py'

        # Development paths (relative to repo_root)
        # Note: json/ is at repo root, not inside MediBot/
        env['source_folder_dev'] = os.path.join(self.repo_root, 'MediBot', 'DOWNLOADS')
        env['target_folder_dev'] = os.path.join(self.repo_root, 'MediBot', 'DOWNLOADS', 'CSV')
        env['python_script_dev'] = os.path.join(self.medibot_dir, 'update_json.py')
        env['python_script2_dev'] = os.path.join(self.medibot_dir, 'MediBot.py')

        local_upgrade = os.path.join(self.medibot_dir, 'update_medicafe.py')
        legacy_upgrade = r'F:\Medibot\update_medicafe.py'
        env['upgrade_medicafe_local'] = local_upgrade
        env['upgrade_medicafe_legacy'] = legacy_upgrade
        env['upgrade_medicafe'] = None

        env['local_storage_legacy'] = r'F:\Medibot\DOWNLOADS'
        env['local_storage_local'] = os.path.join('MediBot', 'DOWNLOADS')
        env['config_file_legacy'] = r'F:\Medibot\json\config.json'
        # Config files are at repo_root/json/, not MediBot/json/
        env['config_file_local'] = os.path.join('json', 'config.json')
        env['temp_file_legacy'] = r'F:\Medibot\last_update_timestamp.txt'
        env['temp_file_local'] = os.path.join('MediBot', 'last_update_timestamp.txt')

        # Detect environment: Check for F: drive (production) vs dev machine
        f_drive_exists = os.path.exists(r'F:\\')
        legacy_folder_exists = os.path.exists(r'F:\Medibot')
        production_source_exists = os.path.exists(env['source_folder_production'])
        
        # Production environment detection
        is_production = legacy_folder_exists or production_source_exists
        
        if f_drive_exists and not legacy_folder_exists:
            try:
                os.makedirs(r'F:\Medibot')
                legacy_folder_exists = True
                is_production = True
            except OSError:
                pass  # Might not have permission, continue with local paths

        if is_production and legacy_folder_exists:
            # Production XP environment with F: drive
            env['local_storage_path'] = env['local_storage_legacy']
            env['config_file'] = env['config_file_legacy']
            env['temp_file'] = env['temp_file_legacy']
            env['source_folder'] = env['source_folder_production']
            env['target_folder'] = env['target_folder_production']
            env['python_script'] = env['python_script_production']
            env['python_script2'] = env['python_script2_production']
            
            # Only use legacy updater if it exists
            if os.path.exists(legacy_upgrade):
                env['upgrade_medicafe'] = legacy_upgrade
            elif os.path.exists(local_upgrade):
                env['upgrade_medicafe'] = local_upgrade
            else:
                env['upgrade_medicafe'] = None
        else:
            # Development environment - use relative paths from repo_root
            env['local_storage_path'] = env['local_storage_local']
            env['config_file'] = env['config_file_local']
            env['temp_file'] = env['temp_file_local']
            env['source_folder'] = env['source_folder_dev']
            env['target_folder'] = env['target_folder_dev']
            env['python_script'] = env['python_script_dev']
            env['python_script2'] = env['python_script2_dev']
            env['upgrade_medicafe'] = local_upgrade if os.path.exists(local_upgrade) else None
            
            # Ensure dev directories exist
            try:
                if not os.path.exists(env['source_folder']):
                    os.makedirs(env['source_folder'])
                if not os.path.exists(env['target_folder']):
                    os.makedirs(env['target_folder'])
            except OSError:
                pass  # Will be created by _ensure_directories if needed

        return env

    def _ensure_directories(self):
        """Make sure relative fallback directories exist."""
        # json/ is at repo root, not inside MediBot/
        json_dir = os.path.join(self.repo_root, 'json')
        dl_dir = os.path.join(self.repo_root, 'MediBot', 'DOWNLOADS')
        csv_dir = os.path.join(dl_dir, 'CSV')
        try:
            if not os.path.exists(json_dir):
                os.makedirs(json_dir)
            if not os.path.exists(dl_dir):
                os.makedirs(dl_dir)
            if not os.path.exists(csv_dir):
                os.makedirs(csv_dir)
        except Exception as exc:
            self._record_notice('WARNING', 'Failed to create fallback directories: {0}'.format(exc))

    def _record_notice(self, level, message):
        """Record a notice to log file, and console for WARNING/ERROR only."""
        self.startup_notices.append((level, message))
        
        # Only print to console for WARNING and ERROR levels
        # INFO messages are logged to file but not displayed on console
        if level in ('WARNING', 'ERROR'):
            print('[{0}] {1}'.format(level, message))
        
        # Always write to the actual log file for persistence (no console output)
        try:
            from MediCafe.MediLink_ConfigLoader import log as config_log
            # Log to file only - don't print to console (console_output=False)
            config_log(message, level=level, console_output=False)
        except Exception:
            # Fallback: try to write directly to log file if ConfigLoader unavailable
            try:
                import logging
                logger = logging.getLogger('MediCafe.launcher')
                log_method = getattr(logger, level.lower(), logger.info)
                log_method(message)
            except Exception:
                # Only print to console as last resort if logging completely fails
                if level in ('WARNING', 'ERROR'):
                    print('[{0}] {1}'.format(level, message))

    def _copy_update_script_to_legacy(self):
        """Copy update script to F: drive if available."""
        local_path = self.environment.get('upgrade_medicafe_local')
        legacy_path = self.environment.get('upgrade_medicafe_legacy')
        if not local_path or not os.path.exists(local_path):
            return
        
        # Check if F: drive exists
        if not os.path.exists(r'F:\\'):
            return
            
        try:
            legacy_dir = os.path.dirname(legacy_path)
            if not os.path.exists(legacy_dir):
                os.makedirs(legacy_dir)
            shutil.copy2(local_path, legacy_path)
            self.environment['upgrade_medicafe'] = legacy_path
        except Exception as exc:
            self._record_notice('WARNING', 'Could not copy updater to legacy path: {0}'.format(exc))

    def _validate_config(self):
        """Concern #5: Validate config file exists, prompt if missing."""
        config_file = self.environment.get('config_file')
        if not config_file:
            raise LauncherConfigError('Configuration file path could not be resolved.')
            
        if os.path.exists(config_file):
            return
            
        # Config file missing - prompt user
        print('')
        print('Configuration file missing.')
        print('')
        print('Expected configuration file path: {0}'.format(config_file))
        print('')
        print('Would you like to provide an alternate path for the configuration file?')
        choice = self._prompt("Enter 'Y' to provide alternate path, or any other key to exit: ")
        
        if choice and choice.strip().upper() == 'Y':
            while True:
                print('')
                print('Please enter the full path to your configuration file.')
                print('Example: C:\\MediBot\\config\\config.json')
                print('Example with spaces: "G:\\My Drive\\MediBot\\config\\config.json"')
                print('')
                print('Note: If your path contains spaces, please include quotes around the entire path.')
                print('')
                alt_path = self._prompt('Enter configuration file path: ')
                # Remove any surrounding quotes from user input
                alt_path = alt_path.strip().strip('"').strip("'")
                
                if os.path.exists(alt_path):
                    print('Configuration file found at: {0}'.format(alt_path))
                    self.environment['config_file'] = alt_path
                    return True
                else:
                    print('Configuration file not found at: {0}'.format(alt_path))
                    retry = self._prompt('Would you like to try another path? (Y/N): ')
                    if not retry or retry.strip().upper() != 'Y':
                        break
        raise LauncherConfigError('Configuration file is required but was not located: {0}'.format(config_file))

    def _determine_medicafe_version(self):
        try:
            cmd = [sys.executable, '-c',
                   'import pkg_resources; '
                   'print("MediCafe=="+pkg_resources.get_distribution("medicafe").version)']
            temp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.repo_root)
            stdout, _ = temp.communicate()
            # Ensure subprocess is properly closed
            try:
                if temp.poll() is None:
                    temp.terminate()
                    temp.wait(timeout=1)
            except Exception:
                try:
                    temp.kill()
                    temp.wait()
                except Exception:
                    pass
            if stdout:
                decoded = stdout.decode('ascii', 'ignore').strip()
                parts = decoded.split('==')
                if len(parts) == 2:
                    self.medicafe_version = parts[1]
        except Exception:
            self.medicafe_version = 'unknown'

    def _check_for_updates(self):
        """Check PyPI for available package updates (may take a few seconds)."""
        script_path = self.environment.get('upgrade_medicafe')
        if not script_path or not os.path.exists(script_path):
            return
        
        # Show console output for update check since it takes several seconds
        # This is an exception to INFO suppression - user needs feedback during delay
        print("Checking for updates...", end='', flush=True)
        
        # Log that update check is starting (this may take a few seconds due to PyPI network request)
        try:
            from MediCafe.MediLink_ConfigLoader import log as config_log
            config_log("Checking PyPI for package updates (this may take a few seconds)", level="INFO", console_output=False)
        except Exception:
            pass
        
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.close()
            cmd = [self.python_exe, script_path, '--check-only']
            with open(temp_file.name, 'w+b') as handle:
                proc = subprocess.Popen(cmd, stdout=handle, stderr=subprocess.PIPE, cwd=self.repo_root)
                _, stderr = proc.communicate()
                # Ensure subprocess is properly closed
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        proc.wait(timeout=1)
                except Exception:
                    try:
                        proc.kill()
                        proc.wait()
                    except Exception:
                        pass
                if proc.returncode != 0 and stderr:
                    self._record_notice('WARNING', 'Update check failed: {0}'.format(stderr))
            with open(temp_file.name, 'r') as reader:
                for line in reader:
                    line = line.strip()
                    if line.startswith('UPDATE_AVAILABLE:'):
                        self.update_available_version = line.split(':', 1)[1].strip()
                        # Log if update is available
                        try:
                            config_log("Update available: {0}".format(self.update_available_version), level="INFO", console_output=False)
                        except Exception:
                            pass
                    elif line == 'UP_TO_DATE':
                        # Log that we're up to date
                        try:
                            config_log("Package is up to date", level="INFO", console_output=False)
                        except Exception:
                            pass
            
            # Log completion of update check
            try:
                config_log("Update check completed", level="INFO", console_output=False)
            except Exception:
                pass
            
            # Complete console message
            print(" done")
        except Exception as exc:
            print(" failed")  # Show failure on console
            self._record_notice('WARNING', 'Unable to perform update check: {0}'.format(exc))
        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def prepare(self):
        """Run one-time bootstrap steps."""
        if self.prepared:
            return
        
        # Log initialization steps for visibility (file only, no console)
        try:
            from MediCafe.MediLink_ConfigLoader import log as config_log
            config_log("Initializing MediCafe launcher", level="INFO", console_output=False)
            config_log("Ensuring required directories exist", level="INFO", console_output=False)
        except Exception:
            pass
        
        if os.name != 'nt':
            self._record_notice('WARNING', 'This launcher expects Windows. Some features are disabled.')
        
        self._ensure_directories()
        
        try:
            config_log("Copying update script to legacy location", level="INFO", console_output=False)
        except Exception:
            pass
        self._copy_update_script_to_legacy()
        
        # Concern #5: Validate config before proceeding
        try:
            config_log("Validating configuration", level="INFO", console_output=False)
        except Exception:
            pass
        self._validate_config()
        
        try:
            config_log("Determining MediCafe version", level="INFO", console_output=False)
        except Exception:
            pass
        self._determine_medicafe_version()
        
        # Update check happens in _check_for_updates() which logs its own start/completion
        self._check_for_updates()
        
        try:
            config_log("MediCafe launcher initialization complete", level="INFO", console_output=False)
        except Exception:
            pass
        self.prepared = True

    # ------------------------------------------------------------------ #
    # Main entry routing
    # ------------------------------------------------------------------ #
    def run(self):
        try:
            # Clear console and show header immediately, before any preparation steps
            self._clear_console()
            self._print_legacy_banner('MediCafe Launcher')
            
            # Now run preparation steps (they'll log to file, not console for INFO level)
            self.prepare()
            
            if self.session.direct_action == 'rollback':
                self.forced_version_rollback()
                return
            if self.session.direct_action == 'troubleshooting':
                self.troubleshooting_menu()
                return
            if self.session.debug_mode:
                self.debug_menu()
                return
            self.start_normal_mode()
        except KeyboardInterrupt:
            print('\nUser interrupted execution.')
        except Exception as exc:
            # Concern #9: Only bundle on orchestrator exceptions, not subprocess failures
            self.handle_fatal_error(exc)

    def start_normal_mode(self):
        # Clear console right before version display to remove any preparation output (e.g. "Checking for updates...")
        self._clear_console()
        self._print_version_details()        
        # Run startup tasks (they'll log to file, not console for INFO level)
        self._run_startup_tasks()
        
        # Now show the full menu (header already displayed, so skip it on first iteration)
        self.main_menu_loop(show_header_on_first=False)

    def _run_startup_tasks(self):
        self._run_download_migration()
        if not self.session.skip_startup_csv:
            self._launch_startup_csv()
        else:
            self._record_notice('INFO', 'Startup CSV processing skipped by flag.')

    # ------------------------------------------------------------------ #
    # Debug / Troubleshooting
    # ------------------------------------------------------------------ #
    def debug_menu(self):
        print('')
        print('========================================')
        print('       MEDICAFE DEBUG OPTIONS          ')
        print('========================================')
        print('1. Normal Mode (continue)')
        print('2. Run interactive debug suite')
        print('3. Run non-interactive debug suite')
        print('4. Emergency rollback')
        print('5. Troubleshooting toolkit')
        choice = raw_input('Choose an option (1-5): ') if sys.version_info[0] < 3 else input('Choose an option (1-5): ')
        if choice == '2':
            self._call_batch('full_debug_suite.bat', ['/interactive'])
        elif choice == '3':
            self._call_batch('full_debug_suite.bat', [])
        elif choice == '4':
            self.forced_version_rollback()
            return
        elif choice == '5':
            self.troubleshooting_menu()
            return
        self.start_normal_mode()

    def troubleshooting_menu(self):
        while True:
            self._clear_console()
            self._print_legacy_banner('MediCafe Troubleshooting Toolkit', width=40)
            self._print_troubleshooting_group('Reporting & Logs', [
                '1)  Submit error report (email)',
                '2)  View latest run log',
                '3)  View WinSCP transfer logs',
            ])
            self._print_troubleshooting_group('Logging Controls', [
                '4)  Toggle performance logging (session)',
                '5)  Toggle verbose logging (session)',
            ])
            self._print_troubleshooting_group('Cache & Token Maintenance', [
                '6)  Manage Python cache',
                '7)  Reset Gmail OAuth token',
            ])
            self._print_troubleshooting_group('Data Intake', [
                '8)  Force CSV intake (includes deductible cache build)',
            ])
            self._print_troubleshooting_group('Safety & Recovery', [
                '9)  Emergency MediCafe rollback',
            ])
            self._print_troubleshooting_group('Advanced Tools', [
                '10) Launch config editor',
            ])
            print('Navigation')
            print(' 11) Return to Main Menu')
            print('')
            choice = self._prompt('Enter your choice: ')
            if choice == '1':
                self.run_medicafe_command('send_error_report')
            elif choice == '2':
                self.open_latest_log()
            elif choice == '3':
                self.open_winscp_logs()
            elif choice == '4':
                self.toggle_session_flag('MEDICAFE_PERFORMANCE_LOGGING')
            elif choice == '5':
                self.toggle_session_flag('MEDICAFE_VERBOSE_LOGGING')
            elif choice == '6':
                self.clear_cache_menu()
            elif choice == '7':
                self.force_gmail_reauth()
            elif choice == '8':
                self.process_csvs()
            elif choice == '9':
                self.forced_version_rollback()
            elif choice == '10':
                self._call_batch('config_editor.bat', [])
            elif choice == '11':
                return
            else:
                print('Invalid choice.')

    # ------------------------------------------------------------------ #
    # Menu + options
    # ------------------------------------------------------------------ #
    def main_menu_loop(self, show_header_on_first=True):
        first_iteration = True
        while True:
            if first_iteration and not show_header_on_first:
                # Header already displayed, just show menu content
                self._print_welcome_block()
                self._print_main_menu_options()
                first_iteration = False
            else:
                # Menu refresh after operation - just show menu content, header already visible
                print()  # Blank line to separate from operation output
                self._print_welcome_block()
                self._print_main_menu_options()
            
            choice = self._get_menu_choice()

            if choice == '1':
                self.run_update_flow()
            elif choice == '2':
                self.download_emails()
            elif choice == '3':
                self.run_medicafe_command('medilink')
            elif choice == '4':
                self.run_medicafe_command('claims_status')
            elif choice == '5':
                self.run_medicafe_command('deductible')
            elif choice == '6':
                self.run_medicafe_command('medibot')
            elif choice == '7':
                self.troubleshooting_menu()
            elif choice == '8':
                print('Exiting MediCafe UI.')
                # Exit and close console immediately
                # On Windows, this ensures the console window closes when launched from batch files
                _exit_and_close_console()
            else:
                print('Invalid choice.')
                time.sleep(1.5)

    def _prompt(self, message):
        if sys.version_info[0] < 3:
            return raw_input(message)
        return input(message)

    def _clear_console(self):
        command = 'cls' if os.name == 'nt' else 'clear'
        try:
            os.system(command)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Feature actions
    # ------------------------------------------------------------------ #
    def run_update_flow(self):
        script_path = self.environment.get('upgrade_medicafe')
        if not script_path or not os.path.exists(script_path):
            self._record_notice('ERROR', 'Update script not found.')
            return
        runner_path = self._build_update_runner(script_path)
        if not runner_path:
            self._record_notice('ERROR', 'Unable to create update runner.')
            return
        print('Launching MediCafe updater...')
        subprocess.Popen([self.cmd_exe, '/c', runner_path], cwd=self.repo_root)
        sys.exit(0)

    def _build_update_runner(self, script_path):
        """Build temporary batch script to run updater. Concerns #4 and #6."""
        temp_dir = os.environ.get('TEMP') or self.repo_root
        if not os.path.exists(temp_dir):
            try:
                os.makedirs(temp_dir)
            except Exception:
                temp_dir = self.repo_root
        runner = os.path.join(temp_dir, 'medicafe_update_runner_{0}.cmd'.format(os.getpid()))
        try:
            # Quote python_exe to handle paths with spaces
            python_exe_quoted = '"{0}"'.format(self.python_exe)
            script_path_quoted = '"{0}"'.format(script_path)
            batch_path_quoted = '"{0}"'.format(self._batch_path())
            
            with open(runner, 'w') as handle:
                handle.write('@echo off\n')
                handle.write('setlocal enabledelayedexpansion\n')
                handle.write('set "MEDIBOT_PATH={0}"\n'.format(batch_path_quoted))
                handle.write('ping 127.0.0.1 -n 3 >nul\n')
                # Concern #4: Use resolved python path, not literal 'python'
                handle.write('{0} {1}\n'.format(python_exe_quoted, script_path_quoted))
                handle.write('if errorlevel 1 goto failure\n')
                handle.write('if exist !MEDIBOT_PATH! start "" !MEDIBOT_PATH!\n')
                handle.write('exit /b 0\n')
                handle.write(':failure\n')
                handle.write('echo Update failed. Press any key to close...\n')
                handle.write('pause >nul\n')
                handle.write('exit /b 1\n')
            return runner
        except Exception as exc:
            self._record_notice('ERROR', 'Failed to write runner script: {0}'.format(exc))
            return None

    def download_emails(self):
        self.run_medicafe_command('download_emails')
        self.process_csvs(silent=True)

    def run_medicafe_command(self, command, extra_args=None):
        """Run a MediCafe CLI command. Concern #9: Don't bundle on subprocess failures."""
        args = [sys.executable, '-m', 'MediCafe', command]
        if extra_args:
            args.extend(extra_args)
        # Concern #9: Subprocess failures are expected, just log them
        rc = subprocess.call(args, cwd=self.repo_root)
        if rc != 0:
            self._record_notice('ERROR', 'Command {0} failed with code {1}'.format(command, rc))
        return rc

    def process_csvs(self, silent=False):
        """Run CSV processing using Python script directly."""
        self._record_notice('INFO', 'Starting CSV processing')
        
        script = os.path.join(self.medibot_dir, 'process_csvs.py')
        if not os.path.exists(script):
            self._record_notice('WARNING', 'process_csvs.py not found at: {0}'.format(script))
            return
        
        config_file = self.environment.get('config_file', '')
        source_folder = self.environment.get('source_folder', '')
        target_folder = self.environment.get('target_folder', '')
        local_storage_path = self.environment.get('local_storage_path', '')
        python_script = self.environment.get('python_script', '')
        
        if not config_file:
            self._record_notice('WARNING', 'CSV processing skipped: config_file not set')
            return
        
        if not source_folder:
            self._record_notice('WARNING', 'CSV processing skipped: source_folder not set')
            return
        
        if not target_folder:
            self._record_notice('WARNING', 'CSV processing skipped: target_folder not set')
            return
        
        self._record_notice('INFO', 'CSV processing config_file: {0}'.format(config_file))
        self._record_notice('INFO', 'CSV processing source_folder: {0}'.format(source_folder))
        self._record_notice('INFO', 'CSV processing target_folder: {0}'.format(target_folder))
        
        # Build command with required arguments
        command = [
            self.python_exe,
            script,
            '--config', config_file,
            '--source-folder', source_folder,
            '--target-folder', target_folder,
        ]
        
        # Add optional arguments if provided
        if local_storage_path:
            command.extend(['--local-storage-path', local_storage_path])
        if python_script:
            command.extend(['--python-script', python_script])
        if silent:
            command.append('--silent')
        
        try:
            proc = subprocess.Popen(
                command,
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate()
            rc = proc.returncode
            # Ensure subprocess is properly closed
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                    proc.wait()
                except Exception:
                    pass
            
            if rc == 0:
                self._record_notice('INFO', 'CSV processing completed successfully')
            else:
                self._record_notice('WARNING', 'CSV processing exited with code {0}'.format(rc))
                if stderr:
                    stderr_text = stderr.decode('utf-8', errors='replace').strip()
                    if stderr_text:
                        # Log error lines
                        stderr_lines = stderr_text.split('\n')
                        for line in stderr_lines[:5]:  # Log first 5 lines of stderr
                            if line.strip() and ('ERROR' in line.upper() or 'WARNING' in line.upper()):
                                self._record_notice('WARNING', 'CSV processing stderr: {0}'.format(line.strip()[:200]))
        except Exception as e:
            self._record_notice('WARNING', 'Failed to run CSV processing: {0}'.format(e))

    def _run_download_migration(self):
        """Run browser downloads migration using Python script directly."""
        self._record_notice('INFO', 'Starting browser downloads migration')
        
        script = os.path.join(self.medibot_dir, 'migrate_browser_downloads.py')
        if not os.path.exists(script):
            self._record_notice('WARNING', 'migrate_browser_downloads.py not found at: {0}'.format(script))
            return
        
        config_file = self.environment.get('config_file', '')
        source_folder = self.environment.get('source_folder', '')
        
        if not config_file:
            self._record_notice('WARNING', 'Migration skipped: config_file not set')
            return
        
        if not source_folder:
            self._record_notice('WARNING', 'Migration skipped: source_folder not set')
            return
        
        self._record_notice('INFO', 'Migration config_file: {0}'.format(config_file))
        self._record_notice('INFO', 'Migration source_folder: {0}'.format(source_folder))
        
        # Call Python script directly with --execute and --silent flags
        command = [
            self.python_exe,
            script,
            '--config', config_file,
            '--source-folder', source_folder,
            '--execute',
            '--silent'
        ]
        
        try:
            proc = subprocess.Popen(
                command,
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate()
            rc = proc.returncode
            # Ensure subprocess is properly closed
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                    proc.wait()
                except Exception:
                    pass
            
            if rc == 0:
                # Log success - check stdout for summary if available
                if stdout:
                    stdout_text = stdout.decode('utf-8', errors='replace').strip()
                    # Look for summary line in silent mode output
                    found_summary = False
                    for line in stdout_text.split('\n'):
                        if '[INFO] Browser downloads:' in line:
                            self._record_notice('INFO', line.strip())
                            found_summary = True
                            break
                    if not found_summary:
                        self._record_notice('INFO', 'Browser downloads migration completed successfully (no files processed)')
                else:
                    self._record_notice('INFO', 'Browser downloads migration completed successfully')
            else:
                self._record_notice('WARNING', 'Browser downloads migration exited with code {0}'.format(rc))
                if stderr:
                    stderr_text = stderr.decode('utf-8', errors='replace').strip()
                    if stderr_text:
                        # Log error lines
                        stderr_lines = stderr_text.split('\n')
                        for line in stderr_lines[:5]:  # Log first 5 lines of stderr
                            if line.strip() and ('ERROR' in line.upper() or 'WARNING' in line.upper()):
                                self._record_notice('WARNING', 'Migration stderr: {0}'.format(line.strip()[:200]))
        except Exception as e:
            self._record_notice('WARNING', 'Failed to run browser downloads migration: {0}'.format(e))

    def _launch_startup_csv(self):
        """Launch CSV processing in background. Concern #7: Visibility is acceptable parity."""
        script = os.path.join(self.medibot_dir, 'process_csvs.py')
        if not os.path.exists(script):
            self._record_notice('WARNING', 'process_csvs.py not found.')
            return
        if os.name != 'nt':
            self._record_notice('INFO', 'Non-Windows platform: running CSV inline.')
            self.process_csvs(silent=True)
            return
        try:
            config_file = self.environment.get('config_file', '')
            source_folder = self.environment.get('source_folder', '')
            target_folder = self.environment.get('target_folder', '')
            local_storage_path = self.environment.get('local_storage_path', '')
            python_script = self.environment.get('python_script', '')
            
            # Validate required variables
            if not config_file or not source_folder or not target_folder:
                self._record_notice('WARNING', 'Background CSV: Missing required environment variables')
                return
            
            self._record_notice('INFO', 'Launching background CSV processing')
            
            # Build command with required arguments
            command = [
                self.python_exe,
                script,
                '--config', config_file,
                '--source-folder', source_folder,
                '--target-folder', target_folder,
                '--silent'
            ]
            
            # Add optional arguments if provided
            if local_storage_path:
                command.extend(['--local-storage-path', local_storage_path])
            if python_script:
                command.extend(['--python-script', python_script])
            
            # Launch as background process in a separate minimized console window
            # This allows users to observe CSV processing progress by opening the window
            # Use start /MIN to create a minimized window that doesn't interfere with main menu
            if os.name == 'nt':
                # Build properly quoted command string for start /MIN
                # For start command: start "Window Title" /MIN executable args...
                # We need to quote all paths/arguments to handle spaces properly
                quoted_command_parts = []
                for arg in command:
                    # Escape any existing quotes and wrap in quotes
                    # This ensures paths with spaces work correctly
                    escaped_arg = arg.replace('"', '""')
                    quoted_command_parts.append('"{0}"'.format(escaped_arg))
                
                # Use start /MIN to create a separate minimized console window
                # Format: start "Window Title" /MIN "python.exe" "script.py" "arg1" "arg2" ...
                cmd_string = 'start "CSV Processing" /MIN {0}'.format(' '.join(quoted_command_parts))
                
                subprocess.Popen(
                    cmd_string,
                    shell=True,
                    cwd=self.repo_root
                )
            else:
                # Non-Windows: run in background without window
                subprocess.Popen(
                    command,
                    cwd=self.repo_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
        except Exception as e:
            self._record_notice('WARNING', 'Failed to start CSV background process: {0}. Running inline.'.format(e))
            self.process_csvs(silent=True)

    def open_latest_log(self):
        logs_dir = self.environment.get('local_storage_path')
        if not logs_dir:
            print('Log directory unknown.')
            return
        logs_dir = self._make_absolute(logs_dir)
        if not os.path.exists(logs_dir):
            print('Log directory missing: {0}'.format(logs_dir))
            return
        latest = None
        for item in sorted(os.listdir(logs_dir), reverse=True):
            if item.lower().endswith('.log'):
                latest = os.path.join(logs_dir, item)
                break
        if not latest:
            print('No log files found in {0}'.format(logs_dir))
            return
        self._launch_viewer(latest)

    def open_winscp_logs(self):
        base = self.environment.get('local_storage_path')
        if not base:
            return
        base = self._make_absolute(base)
        download = os.path.join(base, 'winscp_download.log')
        upload = os.path.join(base, 'winscp_upload.log')
        opened = False
        for path in [download, upload]:
            if os.path.exists(path):
                self._launch_viewer(path)
                opened = True
        if not opened:
            print('No WinSCP logs found at {0}'.format(base))

    def clear_cache_menu(self):
        print('')
        print('1. Quick clear (compileall + delete __pycache__)')
        print('2. Deep clear (update_medicafe.py)')
        print('3. Back')
        choice = self._prompt('Choice: ')
        if choice == '1':
            self._call_batch('clear_cache.bat', ['--quick'])
        elif choice == '2':
            self._call_batch('clear_cache.bat', ['--deep'])

    def force_gmail_reauth(self):
        candidates = [
            os.path.join(self.repo_root, 'MediLink', 'token.json'),
            os.path.join(self.repo_root, 'token.json')
        ]
        cleared = False
        for path in candidates:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print('[OK] Removed {0}'.format(path))
                    cleared = True
                except Exception as exc:
                    print('[WARN] Could not remove {0}: {1}'.format(path, exc))
        if not cleared:
            print('No Gmail tokens found to remove.')

    def toggle_session_flag(self, env_var):
        current = os.environ.get(env_var, '0')
        new_value = '0' if current == '1' else '1'
        os.environ[env_var] = new_value
        print('{0} set to {1} for this session.'.format(env_var, new_value))

    # ------------------------------------------------------------------ #
    # Rollback + error handling
    # ------------------------------------------------------------------ #
    def forced_version_rollback(self, version='0.251120.0'):
        package = self.environment.get('medicafe_package', 'medicafe')
        target = '{0}=={1}'.format(package, version)
        print('Forcing reinstall of {0}'.format(target))
        rc = subprocess.call([self.python_exe, '-m', 'pip', 'install',
                              '--no-deps', '--force-reinstall', target], cwd=self.repo_root)
        if rc != 0:
            print('force-reinstall not supported, attempting uninstall/install fallback.')
            subprocess.call([self.python_exe, '-m', 'pip', 'uninstall', '-y', package], cwd=self.repo_root)
            rc = subprocess.call([self.python_exe, '-m', 'pip', 'install', '--no-deps', target], cwd=self.repo_root)
        if rc == 0:
            print('Rollback complete.')
        else:
            print('Rollback failed. Check logs for details.')

    def handle_fatal_error(self, exc):
        """Handle fatal orchestrator errors. Concern #9: Only bundle orchestrator exceptions."""
        print('=' * 60)
        print('MEDICAFE ORCHESTRATOR FAILURE')
        print('=' * 60)
        if isinstance(exc, LauncherConfigError):
            print('Configuration error: {0}'.format(exc))
            print('Please update your config file path or restore the expected file.')
        else:
            print('Error: {0}'.format(exc))
        print('=' * 60)
        context = self._build_bundle_context(exc)
        self.failure_bundle_path = self._collect_error_bundle(context)
        print('Choose how to proceed:')
        print('1. Attempt rollback')
        print('2. Exit without changes')
        choice = self._prompt('Selection: ')
        if choice == '1':
            self.forced_version_rollback()
        else:
            print('Exiting without rollback.')

    def _collect_error_bundle(self, context):
        """Collect error bundle for orchestrator failures only."""
        bundle = self.bundle_coordinator.collect_once(context)
        if not bundle:
            return None
        print('Error bundle available at {0}'.format(bundle))
        if submit_support_bundle_email and check_internet_connection:
            try:
                if check_internet_connection():
                    sent = submit_support_bundle_email(bundle)
                    if sent:
                        os.remove(bundle)
                    else:
                        print('Bundle send failed; file retained.')
            except Exception:
                print('Bundle transmission error; file retained.')
        return bundle

    def _build_bundle_context(self, exc):
        """Assemble structured metadata for the error bundle."""
        try:
            session_info = {
                'skip_startup_csv': bool(self.session.skip_startup_csv),
                'direct_action': self.session.direct_action,
                'debug_mode': bool(self.session.debug_mode),
                'auto_choice_source': self.session.auto_menu_source,
            }
        except Exception:
            session_info = {}
        env_snapshot = {
            'config_file': self.environment.get('config_file'),
            'local_storage_path': self.environment.get('local_storage_path'),
            'temp_file': self.environment.get('temp_file'),
            'upgrade_script': self.environment.get('upgrade_medicafe'),
            'repo_root': self.repo_root,
        }
        launcher_state = {
            'medicafe_version': self.medicafe_version,
            'update_available_version': self.update_available_version,
            'python_executable': sys.executable,
            'cwd': os.getcwd(),
            'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        notices = ['[{0}] {1}'.format(level, msg) for level, msg in self.startup_notices]
        context = {
            'exception_type': exc.__class__.__name__,
            'exception_message': str(exc),
            'session': session_info,
            'environment': env_snapshot,
            'launcher_state': launcher_state,
            'startup_notices': notices
        }
        return context

    # ------------------------------------------------------------------ #
    # Utility helpers
    # ------------------------------------------------------------------ #
    def _batch_path(self):
        """Get path to MediBot.bat file."""
        return os.path.join(self.medibot_dir, 'MediBot.bat')

    def _call_batch(self, script_name, args):
        """Call a batch script. Concern #2: Quote paths for spaces."""
        script = os.path.join(self.medibot_dir, script_name)
        if not os.path.exists(script):
            self._record_notice('WARNING', '{0} not found.'.format(script_name))
            return
        # Quote script path so cmd.exe treats it as a single argument even with spaces.
        script_quoted = '"{0}"'.format(script)
        command = [self.cmd_exe, '/c', 'call', script_quoted]
        if args:
            command.extend(args)
        
        # Build environment with required variables for batch scripts
        # These variables are expected by process_csvs.py
        env = os.environ.copy()
        batch_env_vars = {
            'source_folder': self.environment.get('source_folder', ''),
            'target_folder': self.environment.get('target_folder', ''),
            'config_file': self.environment.get('config_file', ''),
            'python_script': self.environment.get('python_script', ''),
            'local_storage_path': self.environment.get('local_storage_path', ''),
        }
        env.update(batch_env_vars)
        
        # Log batch script invocation for debugging (INFO level)
        self._log_batch_invocation(script_name, batch_env_vars, args)
        
        # Always run from repo_root for consistent working directory
        # Capture output to enable logging of errors
        try:
            proc = subprocess.Popen(
                command,
                cwd=self.repo_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate()
            rc = proc.returncode
            # Ensure subprocess is properly closed
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                    proc.wait()
                except Exception:
                    pass
            
            # Log results based on exit code
            if rc != 0:
                self._record_notice('WARNING', 'Batch script {0} exited with code {1}'.format(script_name, rc))
                if stderr:
                    stderr_text = stderr.decode('utf-8', errors='replace').strip()
                    if stderr_text:
                        # Log full stderr for debugging (split into multiple notices if needed)
                        stderr_lines = stderr_text.split('\n')
                        for line in stderr_lines[:10]:  # Log first 10 lines of stderr
                            if line.strip():
                                self._record_notice('WARNING', 'Batch stderr: {0}'.format(line.strip()[:200]))
                        if len(stderr_lines) > 10:
                            self._record_notice('WARNING', 'Batch stderr: ... ({0} more lines)'.format(len(stderr_lines) - 10))
                if stdout:
                    stdout_text = stdout.decode('utf-8', errors='replace').strip()
                    # Check for common error patterns in stdout
                    if 'cannot find' in stdout_text.lower() or 'error' in stdout_text.lower() or '[error]' in stdout_text.lower() or '[debug]' in stdout_text.lower():
                        stdout_lines = stdout_text.split('\n')
                        for line in stdout_lines[:10]:  # Log first 10 lines of relevant stdout
                            line_lower = line.lower()
                            if 'cannot find' in line_lower or 'error' in line_lower or '[error]' in line_lower or '[debug]' in line_lower:
                                self._record_notice('WARNING', 'Batch stdout: {0}'.format(line.strip()[:200]))
        except Exception as e:
            self._record_notice('ERROR', 'Failed to execute batch script {0}: {1}'.format(script_name, e))
    
    def _log_batch_invocation(self, script_name, env_vars, args):
        """Log batch script invocation details for debugging."""
        # Check for potentially problematic empty variables
        empty_vars = [k for k, v in env_vars.items() if not v]
        if empty_vars:
            self._record_notice('WARNING', 'Batch {0}: Empty environment variables: {1}'.format(
                script_name, ', '.join(empty_vars)))
        
        # Log at INFO level for normal operation tracking
        self._record_notice('INFO', 'Invoking batch: {0} with args: {1}'.format(
            script_name, args if args else '(none)'))

    def _make_absolute(self, path_value):
        """Convert relative path to absolute using repo_root."""
        if os.path.isabs(path_value):
            return path_value
        return os.path.abspath(os.path.join(self.repo_root, path_value))

    def _launch_viewer(self, path):
        """Launch default text viewer for a file."""
        if os.name != 'nt':
            print('File: {0}'.format(path))
            return
        try:
            subprocess.Popen(['notepad.exe', path])
        except Exception:
            subprocess.Popen(['write.exe', path])

    # ------------------------------------------------------------------ #
    # Console rendering helpers (legacy ASCII parity)
    # ------------------------------------------------------------------ #
    def _print_legacy_banner(self, title, width=39):
        line = '=' * width
        print(line)
        print(title.center(width))
        print(line)
        print('')

    def _print_welcome_block(self):
        width = 62
        separator = '-' * width
        welcome = './/*  Welcome to MediCafe  *\\\\.'
        print(separator)
        print(welcome.center(width))
        print(separator)
        print('')

    def _print_version_details(self):
        # BUG clear_console() 
        print('Version: {0}'.format(self.medicafe_version or 'unknown'))
        if self.update_available_version:
            print('[UPDATE AVAILABLE] {0}'.format(self.update_available_version))
        # Only show WARNING and ERROR notices - INFO messages go to log file only
        warning_notices = [(level, msg) for level, msg in self.startup_notices if level in ('WARNING', 'ERROR')]
        if warning_notices:
            print('')
            for level, msg in warning_notices:
                print('[{0}] {1}'.format(level, msg))
            print('-' * 60)
        print('')

    def _print_main_menu_options(self):
        options = [
            ('1', 'Update MediCafe'),
            ('2', 'Download Email de Carol'),
            ('3', 'MediLink Claims'),
            ('4', '[United] Claims Status'),
            ('5', '[United] Deductible'),
            ('6', 'Run MediBot'),
            ('7', 'Troubleshooting'),
            ('8', 'Exit'),
        ]
        print('Please select an option:')
        print('')
        for number, label in options:
            print(' {0}. {1}'.format(number, label))
            print('')

    def _get_menu_choice(self):
        if self.session.auto_menu_choice:
            choice = self.session.auto_menu_choice
            source = self.session.auto_menu_source or 'CLI'
            print('[AUTO source={0}] Using menu choice {1}'.format(source, choice))
            self.session.auto_menu_choice = None
            self.session.auto_menu_source = None
            return choice
        return self._prompt('Enter your choice: ')

    def _print_troubleshooting_group(self, heading, lines):
        print(heading)
        for entry in lines:
            print('  {0}'.format(entry))
        print('')


def main():
    """Main entry point for launcher."""
    # Log launcher initiation as early as possible
    try:
        from MediCafe.MediLink_ConfigLoader import log as config_log
        config_log("MediCafe launcher starting", level="INFO")
    except Exception:
        # If logging initialization fails, continue anyway
        pass
    
    parser = build_arg_parser()
    try:
        args, unknown = parser.parse_known_args(sys.argv[1:])
    except LauncherArgumentError as err:
        print('')
        print('[LAUNCHER] Invalid option: {0}'.format(err))
        print('Please review the supported flags below and try again.')
        print('')
        parser.print_help()
        return 2
    if unknown:
        print('')
        print('[LAUNCHER] Ignoring unsupported option(s): {0}'.format(', '.join(unknown)))
        print('         Use --help for the list of accepted flags.')
        print('')
    session = SessionConfig(args)
    orchestrator = MediCafeOrchestrator(session)
    orchestrator.run()


if __name__ == '__main__':
    main()
