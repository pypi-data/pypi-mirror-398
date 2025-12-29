#!/usr/bin/env python
# update_medicafe.py
# Script Version: 2.0.2 (clean 3-try updater)
# Target environment: Windows XP SP3 + Python 3.4.4 (ASCII-only)

import sys, os, time, subprocess, platform, threading

try:
    import requests
except Exception:
    requests = None

try:
    import pkg_resources
except Exception:
    pkg_resources = None


SCRIPT_NAME = "update_medicafe.py"
SCRIPT_VERSION = "2.0.2"
PACKAGE_NAME = "medicafe"


# ---------- UI helpers (ASCII-only) ----------
def _line(char, width):
    try:
        return char * width
    except Exception:
        return char * 60


def print_banner(title):
    width = 60
    print(_line("=", width))
    print(title)
    print(_line("=", width))


def print_section(title):
    width = 60
    print("\n" + _line("-", width))
    print(title)
    print(_line("-", width))


def print_status(kind, message):
    label = "[{}]".format(kind)
    print("{} {}".format(label, message))


# ---------- Version utilities ----------
def compare_versions(version1, version2):
    try:
        v1_parts = list(map(int, version1.split(".")))
        v2_parts = list(map(int, version2.split(".")))
        return (v1_parts > v2_parts) - (v1_parts < v2_parts)
    except Exception:
        # Fall back to string compare if unexpected formats
        return (version1 > version2) - (version1 < version2)


def get_installed_version(package):
    proc = None
    try:
        proc = subprocess.Popen([sys.executable, '-m', 'pip', 'show', package],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode == 0:
            for line in out.decode().splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    finally:
        # Ensure subprocess is properly closed
        if proc:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=1)
                    except Exception:
                        proc.kill()
                        proc.wait()
            except Exception:
                pass

    if pkg_resources:
        try:
            return pkg_resources.get_distribution(package).version
        except Exception:
            return None
    return None


def get_latest_version(package, retries):
    # Check internet connectivity before attempting to fetch from PyPI
    if not check_internet_connection():
        print_status('WARNING', 'No internet connection available. Cannot check for latest version.')
        return None
    
    if not requests:
        # Fallback: try pip index if requests missing (first run)
        proc = None
        try:
            proc = subprocess.Popen([sys.executable, '-m', 'pip', 'index', 'versions', package],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode == 0:
                # Parse a line like: Available versions: 1.2.3, 1.2.2, ... (take first)
                for line in out.decode(errors='ignore').splitlines():
                    if 'Available versions:' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            versions = [v.strip() for v in parts[1].split(',') if v.strip()]
                            if versions:
                                return versions[0]
        except Exception:
            pass
        finally:
            # Ensure subprocess is properly closed
            if proc:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        try:
                            proc.wait(timeout=1)
                        except Exception:
                            proc.kill()
                            proc.wait()
                except Exception:
                    pass
        return None

    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'User-Agent': 'MediCafe-Updater/2.0.0'
    }

    last = None
    for attempt in range(1, retries + 1):
        resp = None
        try:
            url = "https://pypi.org/pypi/{}/json?t={}".format(package, int(time.time()))
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            latest = data.get('info', {}).get('version')
            if not latest:
                raise Exception("Malformed PyPI response")

            # Pragmatic double-fetch-if-equal to mitigate CDN staleness
            if last and latest == last:
                if resp:
                    resp.close()  # Explicitly close connection
                return latest
            last = latest
            if attempt == retries:
                if resp:
                    resp.close()  # Explicitly close connection
                return latest
            # If we just fetched same as before and it's equal to current installed, refetch once more quickly
            if resp:
                resp.close()  # Explicitly close connection
            time.sleep(1)
        except Exception:
            if resp:
                try:
                    resp.close()  # Explicitly close connection even on error
                except Exception:
                    pass
            if attempt == retries:
                return None
            time.sleep(1)

    return last


def check_internet_connection(max_retries=3, initial_delay=1):
    """
    Checks if there is an active internet connection with automatic retry logic.
    This function uses the central implementation from MediCafe.core_utils
    to ensure consistent behavior across all modules.
    
    Falls back to a simple connectivity check if MediCafe.core_utils is not available
    (e.g., during first-run scenarios or when running independently).
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1)
    
    Returns: Boolean indicating internet connectivity status.
    """
    try:
        from MediCafe.core_utils import check_internet_connection as central_check
        return central_check(max_retries=max_retries, initial_delay=initial_delay)
    except ImportError:
        # Fallback for independent execution when MediCafe may not be installed yet
        # Use simple connectivity check as last resort
        if requests:
            for attempt in range(max_retries):
                resp = None
                try:
                    resp = requests.get("http://www.google.com", timeout=5, allow_redirects=False)
                    resp.close()  # Explicitly close connection
                    return True
                except Exception:
                    if resp:
                        try:
                            resp.close()  # Explicitly close connection even on error
                        except Exception:
                            pass
                    if attempt < max_retries - 1:
                        time.sleep(initial_delay * (attempt + 1))
        else:
            # Fallback to ping if requests not available
            for attempt in range(max_retries):
                ping_process = None
                try:
                    ping_process = subprocess.Popen(
                        ["ping", "-n", "1", "8.8.8.8"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    ping_output, _ = ping_process.communicate()
                    if "Reply from" in ping_output.decode(errors='ignore'):
                        return True
                except Exception:
                    pass
                finally:
                    # Ensure subprocess is properly closed
                    if ping_process:
                        try:
                            ping_process.terminate()
                            ping_process.wait(timeout=1)
                        except Exception:
                            try:
                                ping_process.kill()
                            except Exception:
                                pass
                if attempt < max_retries - 1:
                    time.sleep(initial_delay * (attempt + 1))
        return False


# ---------- Upgrade logic (3 attempts, minimal delays) ----------
def _should_show_pip_line(text_line):
    try:
        # Show only useful progress lines to avoid noisy output
        line = text_line.strip().lower()
        keywords = [
            'collecting', 'downloading', 'installing', 'building',
            'successfully installed', 'successfully built',
            'requirement already satisfied', 'uninstalling', 'preparing',
            'error', 'warning'
        ]
        for kw in keywords:
            if kw in line:
                return True
    except Exception:
        pass
    return False


def _start_heartbeat(label):
    # Prints a simple heartbeat every 10 seconds while a subprocess runs
    stop_event = threading.Event()
    start_ts = time.time()

    def _runner():
        last_emitted = -1
        while not stop_event.is_set():
            try:
                elapsed = int(time.time() - start_ts)
                if elapsed >= 10 and elapsed // 10 != last_emitted:
                    last_emitted = elapsed // 10
                    print_status('INFO', '{}... {}s elapsed'.format(label, elapsed))
                    try:
                        sys.stdout.flush()
                    except Exception:
                        pass
            except Exception:
                # Never fail due to heartbeat issues
                pass
            time.sleep(1)

    t = threading.Thread(target=_runner)
    t.daemon = True
    t.start()
    return stop_event


def run_pip_install(args):
    # Stream stdout live (stderr merged) with periodic heartbeat
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception:
        # Fallback to legacy behavior if streaming spawn fails for any reason
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        try:
            return proc.returncode, out.decode(errors='ignore'), err.decode(errors='ignore')
        except Exception:
            return proc.returncode, '', ''

    heartbeat = _start_heartbeat('Installer running')
    out_lines = []
    try:
        while True:
            chunk = proc.stdout.readline()
            if not chunk:
                if proc.poll() is not None:
                    break
                # Small sleep to avoid tight loop if no data
                time.sleep(0.1)
                continue
            try:
                text = chunk.decode(errors='ignore').replace('\r', '')
            except Exception:
                text = ''
            out_lines.append(text)
            if _should_show_pip_line(text):
                try:
                    # Print selected progress lines immediately
                    print(text.strip())
                    sys.stdout.flush()
                except Exception:
                    pass
    finally:
        try:
            heartbeat.set()
        except Exception:
            pass
        # Ensure subprocess is properly closed
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
                    proc.wait()
        except Exception:
            pass
        # Close stdout to release resources
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass

    # With stderr merged into stdout, return empty err string
    return proc.returncode, ''.join(out_lines), ''


def verify_post_install(package, expected_version):
    # Try quick reads with minimal backoff to avoid unnecessary slowness
    for attempt in range(1, 6):  # Increased to 5 attempts
        installed = get_installed_version(package)
        if installed:
            if expected_version is None:
                return True, installed
            # Re-fetch latest once to avoid stale latest
            latest_again = get_latest_version(package, retries=1) or expected_version
            if compare_versions(installed, latest_again) >= 0:
                return True, installed
        else:
            print_status('INFO', 'Verification attempt {}: No version detected yet'.format(attempt))
        time.sleep(2)  # Increased to 2 seconds for better propagation on slow systems
    # Final re-fetch for robustness
    installed = get_installed_version(package)
    if expected_version is None and installed:
        return True, installed
    latest_again = get_latest_version(package, retries=1) or expected_version
    if installed and compare_versions(installed, latest_again) >= 0:
        return True, installed
    return False, installed


def upgrade_package(package):
    # Check internet connectivity before attempting package upgrade
    if not check_internet_connection():
        print_status('ERROR', 'No internet connection available. Cannot upgrade package without internet access.')
        return False
    
    # Default to using existing system packages: skip dependencies first
    # Light strategies: --no-deps to avoid heavy reinstall of dependencies
    light_strategies = [
        ['install', '--upgrade', '--no-deps', package + '[binary]', '--no-cache-dir', '--disable-pip-version-check'],
        ['install', '--upgrade', '--no-deps', package, '--no-cache-dir', '--disable-pip-version-check']
    ]

    # Heavy strategies: allow dependencies as a last resort
    heavy_strategies = [
        ['install', '--upgrade', package + '[binary]', '--no-cache-dir', '--disable-pip-version-check'],
        ['install', '--upgrade', package, '--no-cache-dir', '--disable-pip-version-check'],
        ['install', '--upgrade', '--force-reinstall', package + '[binary]', '--no-cache-dir', '--disable-pip-version-check'],
        ['install', '--upgrade', '--force-reinstall', '--ignore-installed', '--user', package + '[binary]', '--no-cache-dir', '--disable-pip-version-check']
    ]

    latest_before = get_latest_version(package, retries=2)
    if not latest_before:
        print_status('WARNING', 'Unable to determine latest version from PyPI; proceeding with blind install')

    print_status('INFO', 'Using existing system packages when possible (skipping dependencies)')

    for idx, parts in enumerate(light_strategies):
        attempt = idx + 1
        print_section("Light attempt {}".format(attempt))
        cmd = [sys.executable, '-m', 'pip'] + parts
        print_status('INFO', 'Running: {} -m pip {}'.format(sys.executable, ' '.join(parts)))
        code, out, err = run_pip_install(cmd)
        if code == 0:
            ok, installed = verify_post_install(package, latest_before)
            if ok:
                print_status('SUCCESS', 'Installed version: {}'.format(installed))
                return True
            else:
                print_status('WARNING', 'Install returned success but version not updated yet{}'.format(
                    '' if not installed else ' (detected {})'.format(installed)))
        else:
            # Show error output concisely; if stderr empty (merged), show tail of stdout
            if err:
                print(err.strip())
            elif out:
                try:
                    lines = out.strip().splitlines()
                    tail = '\n'.join(lines[-15:])
                    if tail:
                        print(tail)
                except Exception:
                    pass
            print_status('WARNING', 'pip returned non-zero exit code ({})'.format(code))

    # If we reached here, light attempts did not succeed conclusively
    # Check command-line flags for non-interactive approval
    auto_yes = False
    for arg in sys.argv[1:]:
        if arg.strip().lower() in ('--aggressive', '--yes-deps', '--full-deps'):
            auto_yes = True
            break

    proceed_heavy = auto_yes
    if not proceed_heavy:
        print_section('Confirmation required')
        print_status('INFO', 'Light update did not complete. A full dependency reinstall may take a long time.')
        print_status('INFO', 'Proceeding will uninstall/reinstall related packages as needed (e.g., requests, lxml, msal).')
        try:
            answer = input('Proceed with full dependency update? (y/N): ').strip().lower()
        except Exception:
            answer = ''
        proceed_heavy = (answer == 'y' or answer == 'yes')

    if not proceed_heavy:
        print_status('INFO', 'User declined full dependency update. Keeping existing dependencies.')
        return False

    print_section('Full dependency update')
    print_status('INFO', 'Running heavy update with dependencies (this may take several minutes)')

    for idx, parts in enumerate(heavy_strategies):
        attempt = idx + 1
        print_section('Heavy attempt {}'.format(attempt))
        cmd = [sys.executable, '-m', 'pip'] + parts
        print_status('INFO', 'Running: {} -m pip {}'.format(sys.executable, ' '.join(parts)))
        code, out, err = run_pip_install(cmd)
        if code == 0:
            ok, installed = verify_post_install(package, latest_before)
            if ok:
                print_status('SUCCESS', 'Installed version: {}'.format(installed))
                return True
            else:
                print_status('WARNING', 'Install returned success but version not updated yet{}'.format(
                    '' if not installed else ' (detected {})'.format(installed)))
        else:
            combined = err or out
            if combined:
                try:
                    lines3 = combined.strip().splitlines()
                    tail3 = '\n'.join(lines3[-15:])
                    if tail3:
                        print(tail3)
                except Exception:
                    pass
            print_status('WARNING', 'pip returned non-zero exit code ({})'.format(code))

    return False


def _is_importable(module_name, submodule_name):
    proc = None
    try:
        code = 'import ' + module_name + '\nfrom ' + module_name + ' import ' + submodule_name
        proc = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        return proc.returncode == 0
    except Exception:
        return False
    finally:
        # Ensure subprocess is properly closed
        if proc:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=1)
                    except Exception:
                        proc.kill()
                        proc.wait()
            except Exception:
                pass


def ensure_lxml_available():
    if _is_importable('lxml', 'etree'):
        return True
    print_section('lxml check')
    print_status('INFO', 'lxml not importable; installing pinned version')
    code, out, err = run_pip_install([sys.executable, '-m', 'pip', 'install', '--upgrade', 'lxml==4.2.0', '--no-cache-dir', '--disable-pip-version-check'])
    if code == 0 and _is_importable('lxml', 'etree'):
        print_status('SUCCESS', 'lxml is now available')
        return True
    if err:
        print(err.strip())
    print_status('ERROR', 'Failed to ensure lxml is available')
    return False


# ---------- Main ----------
def main():
    print_banner("MediCafe Updater ({} v{})".format(SCRIPT_NAME, SCRIPT_VERSION))
    print_status('INFO', 'Python: {}'.format(sys.version.split(" ")[0]))
    print_status('INFO', 'Platform: {}'.format(platform.platform()))

    if not check_internet_connection():
        print_section('Network check')
        print_status('ERROR', 'No internet connection detected')
        sys.exit(1)

    print_section('Environment')
    current = get_installed_version(PACKAGE_NAME)
    if current:
        print_status('INFO', 'Installed {}: {}'.format(PACKAGE_NAME, current))
    else:
        print_status('WARNING', '{} is not currently installed'.format(PACKAGE_NAME))

    latest = get_latest_version(PACKAGE_NAME, retries=3)
    if not latest:
        print_status('WARNING', 'Could not fetch latest version information from PyPI; attempting upgrade anyway')
    else:
        print_status('INFO', 'Latest {} on PyPI: {}'.format(PACKAGE_NAME, latest))

    if current and compare_versions(latest, current) <= 0:
        print_section('Status')
        print_status('SUCCESS', 'Already up to date')
        sys.exit(0)

    print_section('Upgrade')
    print_status('INFO', 'Upgrading {} to {} (up to 3 attempts)'.format(PACKAGE_NAME, latest))
    success = upgrade_package(PACKAGE_NAME)

    print_section('Result')
    final_version = get_installed_version(PACKAGE_NAME)
    if success:
        print_status('SUCCESS', 'Update completed. {} is now at {}'.format(PACKAGE_NAME, final_version or '(unknown)'))
        # Ensure critical binary dependency exists for first-run stability
        ensure_lxml_available()
        print_status('INFO', 'This updater script: v{}'.format(SCRIPT_VERSION))
        sys.exit(0)
    else:
        print_status('ERROR', 'Update failed.')
        if final_version and current and compare_versions(final_version, current) > 0:
            print_status('WARNING', 'Partial success: detected {} after failures'.format(final_version))
        print_status('INFO', 'This updater script: v{}'.format(SCRIPT_VERSION))
        sys.exit(1)


if __name__ == '__main__':
    # Optional quick mode: --check-only prints machine-friendly status
    if len(sys.argv) > 1 and sys.argv[1] == '--check-only':
        if not check_internet_connection():
            print('ERROR')
            sys.exit(1)
        cur = get_installed_version(PACKAGE_NAME)
        lat = get_latest_version(PACKAGE_NAME, retries=2)
        if not cur or not lat:
            print('ERROR')
            sys.exit(1)
        print('UPDATE_AVAILABLE:' + lat if compare_versions(lat, cur) > 0 else 'UP_TO_DATE')
        sys.exit(0)
    main()
