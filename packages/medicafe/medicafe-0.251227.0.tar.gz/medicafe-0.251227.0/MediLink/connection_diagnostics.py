# connection_diagnostics.py
# Lightweight diagnostics for MediLink HTTPS server connectivity issues
# Extends existing functionality rather than duplicating it
# Python 3.4.4 + Windows XP compatible

import os
import sys
import socket
import subprocess
from datetime import datetime

# Try to import centralized logging
try:
    from MediCafe.core_utils import get_shared_config_loader
    _config_loader = get_shared_config_loader()
    if _config_loader:
        _log = _config_loader.log
    else:
        _log = None
except ImportError:
    _log = None


def _safe_log(message, level="INFO"):
    """Safe logging that falls back to print if logger unavailable."""
    if _log:
        try:
            _log(message, level=level)
        except Exception:
            print("[{}] {}".format(level, message))
    else:
        print("[{}] {}".format(level, message))


def _parse_cert_expiry(not_after_str):
    """
    Parse certificate expiration date and calculate days remaining.
    
    Shared helper to avoid duplicate expiration checking logic.
    
    Args:
        not_after_str: Certificate notAfter string (e.g., "Dec 31 23:59:59 2025 GMT")
        
    Returns:
        dict with 'expiry_date', 'days_remaining', 'is_expired', 'expires_soon' (< 7 days)
        Returns None if parsing fails.
    """
    if not not_after_str:
        return None
    
    try:
        expiry = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
        days_remaining = (expiry - datetime.utcnow()).days
        
        return {
            'expiry_date': expiry,
            'days_remaining': days_remaining,
            'is_expired': days_remaining < 0,
            'expires_soon': 0 <= days_remaining < 7,
            'not_after_str': not_after_str
        }
    except ValueError:
        return None


def detect_available_tls_versions():
    """
    Detect which TLS protocol versions are available in this Python/OpenSSL build.
    
    Shared helper to avoid duplicate TLS detection logic.
    
    Returns:
        list of available TLS version strings (e.g., ['TLSv1', 'TLSv1.1', 'TLSv1.2'])
    """
    import ssl
    tls_versions = []
    for name, attr in [('TLSv1', 'PROTOCOL_TLSv1'), ('TLSv1.1', 'PROTOCOL_TLSv1_1'), 
                       ('TLSv1.2', 'PROTOCOL_TLSv1_2'), ('TLSv1.3', 'PROTOCOL_TLSv1_3')]:
        if hasattr(ssl, attr):
            tls_versions.append(name)
    return tls_versions


def is_windows_xp(os_name=None, os_version=None):
    """
    Check if running on Windows XP.
    
    Shared helper to avoid duplicate XP detection logic.
    
    Args:
        os_name: OS name (defaults to platform.system())
        os_version: OS version (defaults to platform.release())
        
    Returns:
        bool: True if running on Windows XP (version 5.x)
    """
    import platform
    if os_name is None:
        os_name = platform.system()
    if os_version is None:
        os_version = platform.release()
    return os_name == 'Windows' and os_version.startswith('5.')


def create_test_ssl_context():
    """
    Create an SSL context for self-tests that accepts self-signed certificates.
    
    Shared helper to avoid duplicate context creation in self-test functions.
    
    Returns:
        ssl.SSLContext configured for testing (no hostname check, no cert verify)
    """
    import ssl
    # Use SSLv23 (which negotiates highest available) or PROTOCOL_TLS
    if hasattr(ssl, 'PROTOCOL_SSLv23'):
        ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    elif hasattr(ssl, 'PROTOCOL_TLS'):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
    else:
        # Fallback for very old Python
        ctx = ssl.SSLContext()
    
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class ConnectionDiagnostics:
    """
    Lightweight diagnostics for HTTPS server connectivity.
    Uses existing functions from MediLink modules where available.
    """
    
    def __init__(self, cert_file='server.cert', key_file='server.key', server_port=8000,
                 os_name=None, os_version=None):
        """
        Initialize diagnostics.
        
        Args:
            cert_file: Path to certificate file
            key_file: Path to private key file
            server_port: Server port number
            os_name: OS name (pass from existing module-level var to avoid duplication)
            os_version: OS version (pass from existing module-level var to avoid duplication)
        """
        self.cert_file = cert_file
        self.key_file = key_file
        self.server_port = server_port
        
        # Use passed values or detect if not provided
        import platform
        self.os_name = os_name or platform.system()
        self.os_version = os_version or platform.release()
        
        self.issues = []
        self.warnings = []
        self.fixes_attempted = []
        self.fixes_successful = []
        self.environment = {}
        self._cert_fix_requires_restart = False  # Track if certificate fix requires restart (preserved across re-runs)
        
    def run_full_diagnostics(self, cert_summary_fn=None):
        """
        Run all diagnostic checks.
        
        Args:
            cert_summary_fn: Optional function to get certificate summary 
                           (use existing get_certificate_summary from MediLink_Gmail)
        """
        # Preserve fix information if already set (from attempt_auto_fixes)
        # This allows re-running diagnostics after fixes while keeping fix history
        preserve_fixes = bool(self.fixes_attempted or self.fixes_successful)
        saved_fixes_attempted = list(self.fixes_attempted) if preserve_fixes else []
        saved_fixes_successful = list(self.fixes_successful) if preserve_fixes else []
        
        self.issues = []
        self.warnings = []
        self.fixes_attempted = []
        self.fixes_successful = []
        
        # Check server running state once and cache for use in certificate checks
        # This avoids redundant port checks (previously done 3 times)
        self._server_running_cache = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # Quick check, don't block
            result = sock.connect_ex(('127.0.0.1', self.server_port))
            sock.close()
            self._server_running_cache = (result == 0)
        except Exception:
            pass  # Assume server not running if check fails
        
        # Build environment info
        self._build_environment_info()
        
        # Run checks
        self._check_certificate_files()
        self._check_certificate_with_summary(cert_summary_fn)
        self._check_port_availability()
        self._check_openssl_availability()
        
        # Add platform-specific warnings
        self._add_platform_warnings()
        
        # Restore fix information if it was preserved (fixes were applied before this run)
        if preserve_fixes:
            self.fixes_attempted = saved_fixes_attempted
            self.fixes_successful = saved_fixes_successful
        
        return self._build_report()
    
    def _build_environment_info(self):
        """Build environment info using available data."""
        import ssl
        
        self.environment = {
            'os_name': self.os_name,
            'os_version': self.os_version,
            'os_full': '{} {}'.format(self.os_name, self.os_version),
            'python_version_info': sys.version_info[:3],
            'ssl_version': getattr(ssl, 'OPENSSL_VERSION', 'Unknown'),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        # Use shared helpers to avoid duplication
        self.environment['is_windows_xp'] = is_windows_xp(self.os_name, self.os_version)
        self.environment['tls_versions'] = detect_available_tls_versions()
    
    def _check_certificate_files(self):
        """Check if certificate files exist."""
        # Use cached server running state (checked once in run_full_diagnostics)
        server_running = getattr(self, '_server_running_cache', False)
        
        if not os.path.exists(self.cert_file):
            self.issues.append({
                'type': 'critical',
                'category': 'certificate',
                'message': 'Certificate file not found: {}'.format(self.cert_file),
                'suggestion': 'Certificate will be auto-generated on server start.',
                'auto_fix': 'generate_certificate',
                'requires_server_restart': server_running  # True if server already running, False if not started yet
            })
        
        if not os.path.exists(self.key_file):
            self.issues.append({
                'type': 'critical',
                'category': 'certificate',
                'message': 'Private key file not found: {}'.format(self.key_file),
                'suggestion': 'Key will be auto-generated with certificate.',
                'auto_fix': 'generate_certificate',
                'requires_server_restart': server_running  # True if server already running, False if not started yet
            })
    
    def _check_certificate_with_summary(self, cert_summary_fn=None):
        """
        Check certificate using existing summary function if provided.
        
        Args:
            cert_summary_fn: Function that returns certificate summary dict
                           (e.g., get_certificate_summary from MediLink_Gmail)
        """
        if not os.path.exists(self.cert_file):
            return
        
        # Use cached server running state (checked once in run_full_diagnostics)
        server_running = getattr(self, '_server_running_cache', False)
        
        cert_info = None
        if cert_summary_fn:
            try:
                cert_info = cert_summary_fn(self.cert_file)
            except Exception as e:
                _safe_log("Error calling cert_summary_fn: {}".format(e), level="DEBUG")
        
        if cert_info:
            # Check for errors from the summary function
            if cert_info.get('error'):
                self.issues.append({
                    'type': 'critical',
                    'category': 'certificate',
                    'message': 'Certificate decode error: {}'.format(cert_info['error']),
                    'detail': 'Certificate file exists but cannot be decoded: {}'.format(cert_info['error']),
                    'suggestion': 'Certificate will be regenerated automatically.',
                    'auto_fix': 'regenerate_certificate',
                    'requires_server_restart': server_running  # True if server already running, False if not started yet
                })
            
            # Check expiration if available (uses shared helper)
            not_after = cert_info.get('notAfter')
            expiry_info = _parse_cert_expiry(not_after)
            if expiry_info:
                if expiry_info['is_expired']:
                    self.issues.append({
                        'type': 'critical',
                        'category': 'certificate_expiry',
                        'message': 'Certificate has expired',
                        'detail': 'Expired on: {}'.format(not_after),
                        'suggestion': 'Certificate will be regenerated automatically.',
                        'auto_fix': 'regenerate_certificate',
                        'requires_server_restart': server_running  # True if server already running, False if not started yet
                    })
                elif expiry_info['expires_soon']:
                    self.warnings.append({
                        'type': 'warning',
                        'category': 'certificate_expiry',
                        'message': 'Certificate expires in {} days'.format(expiry_info['days_remaining']),
                        'suggestion': 'Consider regenerating the certificate soon.'
                    })
    
    def _check_port_availability(self):
        """Check if the server port is available or in use."""
        # Use cached server running state (checked once in run_full_diagnostics)
        # to avoid redundant port checks
        server_running = getattr(self, '_server_running_cache', False)
        
        if server_running:
            self.warnings.append({
                'type': 'info',
                'category': 'port',
                'message': 'Port {} is in use'.format(self.server_port),
                'suggestion': 'This could be the server already running.'
            })
    
    def _check_openssl_availability(self):
        """Check if openssl command is available."""
        try:
            process = subprocess.Popen(
                ['openssl', 'version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                version = stdout.decode('utf-8', errors='replace').strip()
                self.environment['openssl_cmd_version'] = version
            else:
                self.warnings.append({
                    'type': 'warning',
                    'category': 'openssl',
                    'message': 'OpenSSL command not working properly',
                    'suggestion': 'Ensure OpenSSL is installed and in PATH.'
                })
        except Exception as e:
            self.warnings.append({
                'type': 'warning',
                'category': 'openssl',
                'message': 'Cannot execute openssl: {}'.format(e),
                'suggestion': 'Install OpenSSL or add it to PATH.'
            })
    
    def _add_platform_warnings(self):
        """Add platform-specific warnings and notes."""
        if self.environment.get('is_windows_xp'):
            self.warnings.append({
                'type': 'info',
                'category': 'platform',
                'message': 'Running on Windows XP',
                'suggestion': 'Firefox 52 ESR is the last version supporting XP. Certificate exceptions may need re-adding after browser restart.'
            })
        
        if self.os_name == 'Windows':
            self.warnings.append({
                'type': 'info',
                'category': 'firewall',
                'message': 'Windows Firewall may block connections',
                'suggestion': 'Allow Python through Windows Firewall if prompted.'
            })
    
    def attempt_auto_fixes(self, generate_cert_fn=None, openssl_cnf='openssl.cnf'):
        """
        Attempt automatic fixes for detected issues.
        
        Args:
            generate_cert_fn: Function to generate certificates 
                            (use generate_self_signed_cert from gmail_http_utils)
            openssl_cnf: Path to OpenSSL config file
        """
        fixes_needed = set()
        # Save requires_server_restart info before fixes (will be lost when issues are cleared on re-run)
        cert_requires_restart = False
        for issue in self.issues:
            auto_fix = issue.get('auto_fix')
            if auto_fix:
                fixes_needed.add(auto_fix)
                # Track if any certificate fix requires restart
                if auto_fix in ('generate_certificate', 'regenerate_certificate'):
                    if issue.get('requires_server_restart', False):
                        cert_requires_restart = True
        
        # Store this info for use in _build_report (issues may be cleared on re-run)
        self._cert_fix_requires_restart = cert_requires_restart
        
        for fix in fixes_needed:
            self.fixes_attempted.append(fix)
            
            if fix in ('generate_certificate', 'regenerate_certificate'):
                if generate_cert_fn:
                    success = self._fix_regenerate_certificate(generate_cert_fn, openssl_cnf)
                    if success:
                        self.fixes_successful.append(fix)
                else:
                    _safe_log("No certificate generation function provided", level="WARNING")
        
        return len(self.fixes_successful) > 0
    
    def _fix_regenerate_certificate(self, generate_cert_fn, openssl_cnf):
        """Regenerate SSL certificate using provided function."""
        _safe_log("Attempting to regenerate SSL certificate...", level="INFO")
        
        try:
            # Delete old files
            for f in [self.cert_file, self.key_file]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        _safe_log("Could not remove {}: {}".format(f, e), level="WARNING")
            
            # Use the provided generation function
            generate_cert_fn(openssl_cnf, self.cert_file, self.key_file, _safe_log, subprocess)
            _safe_log("Certificate regenerated successfully.", level="INFO")
            return True
            
        except Exception as e:
            _safe_log("Failed to regenerate certificate: {}".format(e), level="ERROR")
            return False
    
    def _build_report(self):
        """Build diagnostic report."""
        critical_count = len([i for i in self.issues if i.get('type') == 'critical'])
        
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'environment': self.environment,
            'issues': self.issues,
            'warnings': self.warnings,
            'fixes_attempted': self.fixes_attempted,
            'fixes_successful': self.fixes_successful,
            'summary': {
                'critical_issues': critical_count,
                'warnings': len(self.warnings),
                'can_start_server': critical_count == 0
            }
        }
        
        # Add user action guidance if certificate was auto-fixed
        if self.fixes_successful:
            cert_fixes = [f for f in self.fixes_successful if f in ('generate_certificate', 'regenerate_certificate')]
            if cert_fixes:
                # Use saved requires_restart info (from before fixes were applied)
                # because self.issues may be cleared/re-populated after re-running diagnostics
                if hasattr(self, '_cert_fix_requires_restart'):
                    requires_restart = self._cert_fix_requires_restart
                else:
                    # Fallback: check current issues if saved info not available (shouldn't happen normally)
                    cert_issues = [i for i in self.issues if i.get('auto_fix') in ('generate_certificate', 'regenerate_certificate')]
                    requires_restart = any(i.get('requires_server_restart', False) for i in cert_issues) if cert_issues else False
                
                report['user_action_required'] = {
                    'action': 'restart_server',
                    'message': 'Certificate has been regenerated automatically.',
                    'requires_restart': requires_restart,
                    'next_steps': [
                        'Close the current MediLink server (if running)',
                        'Restart the MediLink application',
                        'Update Firefox certificate exception if needed (navigate to https://127.0.0.1:{} to add exception)'.format(self.server_port)
                    ]
                }
        
        return report


def run_diagnostics(cert_file='server.cert', key_file='server.key', server_port=8000,
                   os_name=None, os_version=None, cert_summary_fn=None,
                   auto_fix=False, generate_cert_fn=None, openssl_cnf='openssl.cnf'):
    """
    Convenience function to run diagnostics.
    
    Args:
        cert_file: Path to certificate file
        key_file: Path to private key file
        server_port: Server port number
        os_name: OS name (from existing module variable)
        os_version: OS version (from existing module variable)
        cert_summary_fn: Function to get certificate summary (existing get_certificate_summary)
        auto_fix: Whether to attempt automatic fixes
        generate_cert_fn: Function to generate certificates (existing generate_self_signed_cert)
        openssl_cnf: Path to OpenSSL config
    """
    diag = ConnectionDiagnostics(cert_file, key_file, server_port, os_name, os_version)
    report = diag.run_full_diagnostics(cert_summary_fn)
    
    if auto_fix and report['summary']['critical_issues'] > 0 and generate_cert_fn:
        _safe_log("Attempting automatic fixes...", level="INFO")
        diag.attempt_auto_fixes(generate_cert_fn, openssl_cnf)
        report = diag.run_full_diagnostics(cert_summary_fn)
    
    return report


def get_firefox_xp_compatibility_notes():
    """Return Firefox on Windows XP compatibility notes."""
    return {
        'title': 'Firefox on Windows XP Compatibility',
        'notes': [
            'Firefox 52 ESR is the last version supporting Windows XP.',
            'TLS 1.2 requires Firefox 24+ or IE 11.',
            'Certificate exceptions may need re-adding after browser restart.',
            '',
            'If you see "Unable to Connect":',
            '1. Open https://127.0.0.1:8000 directly in Firefox',
            '2. Click "Advanced" then "Add Exception"',
            '3. Return to the webapp and retry',
            '',
            'To clear old certificate exceptions:',
            '1. Firefox Options > Privacy & Security > Certificates',
            '2. View Certificates > Servers tab',
            '3. Remove any 127.0.0.1 entries',
        ]
    }


# Browser error code hints - maps Firefox/browser error codes to solutions
BROWSER_DIAGNOSTIC_HINTS = {
    'sec_error_unknown_issuer': {
        'meaning': 'Browser does not trust the certificate issuer (self-signed)',
        'solution': 'Add a certificate exception',
        'steps': ['Click "Advanced"', 'Click "Add Exception"', 'Confirm the exception']
    },
    'ssl_error_rx_record_too_long': {
        'meaning': 'TLS version mismatch or server misconfiguration',
        'solution': 'Restart the server',
        'steps': ['Check if server is running', 'Restart MediLink application']
    },
    'pr_connect_reset_error': {
        'meaning': 'Server closed connection unexpectedly',
        'solution': 'Check server status',
        'steps': ['Verify Python server is running', 'Check for error messages', 'Restart if needed']
    },
    'pr_end_of_file_error': {
        'meaning': 'Server closed connection during handshake',
        'solution': 'Check certificate files',
        'steps': ['Verify certificate exists', 'Restart server to regenerate if needed']
    },
    'mozilla_pkix_error_self_signed_cert': {
        'meaning': 'Certificate is self-signed (expected for local server)',
        'solution': 'Accept the certificate',
        'steps': ['This is normal', 'Add exception to proceed']
    }
}


# =============================================================================
# SELF-TESTS
# =============================================================================
# These tests can be run to verify server connectivity and SSL configuration.
# They are designed to be safe to call while the server is running.

def selftest_tls_handshake(port=8000, timeout=5):
    """
    Self-test: Attempt a TLS handshake with the local HTTPS server.
    
    This test verifies that:
    1. The server is listening on the specified port
    2. TLS handshake can complete successfully
    3. The negotiated TLS version is acceptable
    
    Args:
        port: Server port to test (default 8000)
        timeout: Connection timeout in seconds
        
    Returns:
        dict with 'success', 'tls_version', 'error', 'suggestion' keys
    """
    import ssl
    
    result = {
        'test': 'tls_handshake',
        'success': False,
        'tls_version': None,
        'cipher': None,
        'error': None,
        'suggestion': None
    }
    
    sock = None
    ssl_sock = None
    
    try:
        # Create a context that accepts self-signed certs (uses shared helper)
        ctx = create_test_ssl_context()
        
        # Attempt connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(('127.0.0.1', port))
        
        # Wrap with SSL
        ssl_sock = ctx.wrap_socket(sock, server_hostname='127.0.0.1')
        
        # Get negotiated parameters
        result['tls_version'] = ssl_sock.version()
        result['cipher'] = ssl_sock.cipher()
        result['success'] = True
        
    except socket.timeout:
        result['error'] = 'Connection timed out'
        result['suggestion'] = 'Server may not be running or firewall is blocking'
    except ConnectionRefusedError:
        result['error'] = 'Connection refused'
        result['suggestion'] = 'Server is not running on port {}'.format(port)
    except ssl.SSLError as e:
        result['error'] = 'SSL error: {}'.format(str(e))
        # Provide specific suggestions based on error
        error_str = str(e).lower()
        if 'certificate' in error_str:
            result['suggestion'] = 'Certificate issue - try regenerating the certificate'
        elif 'handshake' in error_str:
            result['suggestion'] = 'TLS handshake failed - check TLS version compatibility'
        else:
            result['suggestion'] = 'Check server SSL configuration'
    except Exception as e:
        result['error'] = '{}: {}'.format(type(e).__name__, str(e))
        result['suggestion'] = 'Unexpected error - check server logs'
    finally:
        # Ensure sockets are closed to prevent resource leaks
        if ssl_sock:
            try:
                ssl_sock.close()
            except Exception:
                pass
        elif sock:
            try:
                sock.close()
            except Exception:
                pass
    
    return result


def selftest_http_request(port=8000, path='/_health', timeout=5):
    """
    Self-test: Make an HTTPS request to the server and verify response.
    
    This test verifies that:
    1. TLS connection succeeds
    2. HTTP request/response cycle completes
    3. Server returns expected status code
    
    Args:
        port: Server port to test
        path: HTTP path to request (default /_health)
        timeout: Request timeout in seconds
        
    Returns:
        dict with test results
    """
    import ssl
    
    result = {
        'test': 'http_request',
        'path': path,
        'success': False,
        'status_code': None,
        'response_preview': None,
        'error': None,
        'suggestion': None
    }
    
    sock = None
    ssl_sock = None
    
    try:
        # Create SSL context (uses shared helper)
        ctx = create_test_ssl_context()
        
        # Connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(('127.0.0.1', port))
        ssl_sock = ctx.wrap_socket(sock, server_hostname='127.0.0.1')
        
        # Send HTTP request
        request = 'GET {} HTTP/1.1\r\nHost: 127.0.0.1:{}\r\nConnection: close\r\n\r\n'.format(path, port)
        ssl_sock.sendall(request.encode('utf-8'))
        
        # Read response
        response = b''
        while True:
            chunk = ssl_sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if len(response) > 8192:  # Limit response size
                break
        
        # Parse response
        response_str = response.decode('utf-8', errors='replace')
        lines = response_str.split('\r\n')
        if lines:
            status_line = lines[0]
            if ' ' in status_line:
                parts = status_line.split(' ', 2)
                if len(parts) >= 2:
                    try:
                        result['status_code'] = int(parts[1])
                    except ValueError:
                        pass
        
        # Get response body preview
        if '\r\n\r\n' in response_str:
            body = response_str.split('\r\n\r\n', 1)[1]
            result['response_preview'] = body[:200] if len(body) > 200 else body
        
        result['success'] = result['status_code'] == 200
        
        if not result['success']:
            result['suggestion'] = 'Server returned non-200 status'
            
    except Exception as e:
        result['error'] = '{}: {}'.format(type(e).__name__, str(e))
        result['suggestion'] = 'Request failed - check server status'
    finally:
        # Ensure sockets are closed to prevent resource leaks
        if ssl_sock:
            try:
                ssl_sock.close()
            except Exception:
                pass
        elif sock:
            try:
                sock.close()
            except Exception:
                pass
    
    return result


def selftest_cors_headers(port=8000, timeout=5):
    """
    Self-test: Verify CORS and PNA headers are present in response.
    
    This test checks for the headers required for cross-origin requests
    from webapp.html to the local HTTPS server, including the critical
    Access-Control-Allow-Private-Network header for modern browsers.
    
    Args:
        port: Server port to test
        timeout: Request timeout in seconds
        
    Returns:
        dict with test results and header analysis
    """
    import ssl
    
    result = {
        'test': 'cors_headers',
        'success': False,
        'headers_found': {},
        'headers_missing': [],
        'error': None,
        'suggestion': None
    }
    
    required_headers = {
        'access-control-allow-origin': '*',
        'access-control-allow-methods': None,  # Any value is OK
        'access-control-allow-private-network': 'true',  # Critical for PNA
    }
    
    sock = None
    ssl_sock = None
    
    try:
        # Create SSL context (uses shared helper)
        ctx = create_test_ssl_context()
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(('127.0.0.1', port))
        ssl_sock = ctx.wrap_socket(sock, server_hostname='127.0.0.1')
        
        # Send OPTIONS preflight request
        request = 'OPTIONS /_health HTTP/1.1\r\nHost: 127.0.0.1:{}\r\nOrigin: https://script.google.com\r\nAccess-Control-Request-Method: GET\r\nConnection: close\r\n\r\n'.format(port)
        ssl_sock.sendall(request.encode('utf-8'))
        
        response = b''
        while True:
            chunk = ssl_sock.recv(4096)
            if not chunk:
                break
            response += chunk
        
        # Parse headers
        response_str = response.decode('utf-8', errors='replace')
        header_section = response_str.split('\r\n\r\n')[0] if '\r\n\r\n' in response_str else response_str
        
        for line in header_section.split('\r\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result['headers_found'][key.strip().lower()] = value.strip()
        
        # Check required headers
        for header, expected_value in required_headers.items():
            if header not in result['headers_found']:
                result['headers_missing'].append(header)
            elif expected_value and result['headers_found'][header] != expected_value:
                result['headers_missing'].append('{} (wrong value)'.format(header))
        
        result['success'] = len(result['headers_missing']) == 0
        
        if not result['success']:
            result['suggestion'] = 'Missing CORS headers: {}'.format(', '.join(result['headers_missing']))
            
    except Exception as e:
        result['error'] = '{}: {}'.format(type(e).__name__, str(e))
        result['suggestion'] = 'Could not verify headers - check server status'
    finally:
        # Ensure sockets are closed to prevent resource leaks
        if ssl_sock:
            try:
                ssl_sock.close()
            except Exception:
                pass
        elif sock:
            try:
                sock.close()
            except Exception:
                pass
    
    return result


def selftest_certificate_validity(cert_file='server.cert'):
    """
    Self-test: Check certificate file exists and is valid.
    
    Args:
        cert_file: Path to certificate file
        
    Returns:
        dict with test results
    """
    import ssl
    
    result = {
        'test': 'certificate_validity',
        'success': False,
        'exists': False,
        'readable': False,
        'decodable': False,
        'subject': None,
        'expires': None,
        'days_remaining': None,
        'error': None,
        'suggestion': None
    }
    
    try:
        if not os.path.exists(cert_file):
            result['error'] = 'Certificate file not found'
            result['suggestion'] = 'Certificate will be generated on server start'
            return result
        
        result['exists'] = True
        
        # Try to read and decode
        ssl_impl = getattr(ssl, '_ssl', None)
        if ssl_impl and hasattr(ssl_impl, '_test_decode_cert'):
            cert_dict = ssl._ssl._test_decode_cert(cert_file)
            result['decodable'] = True
            result['readable'] = True
            
            # Extract subject
            subject = cert_dict.get('subject', ())
            if subject:
                # Handle nested tuple structure
                subject_parts = []
                for item in subject:
                    if isinstance(item, tuple) and len(item) > 0:
                        inner = item[0]
                        if isinstance(inner, tuple) and len(inner) == 2:
                            subject_parts.append('{}={}'.format(inner[0], inner[1]))
                result['subject'] = ', '.join(subject_parts) if subject_parts else 'Unknown'
            
            # Check expiration (uses shared helper to avoid duplication)
            not_after = cert_dict.get('notAfter')
            expiry_info = _parse_cert_expiry(not_after)
            if expiry_info:
                result['expires'] = not_after
                result['days_remaining'] = expiry_info['days_remaining']
                
                if expiry_info['is_expired']:
                    result['error'] = 'Certificate has expired'
                    result['suggestion'] = 'Delete certificate files and restart server to regenerate'
                elif expiry_info['expires_soon']:
                    result['suggestion'] = 'Certificate expires soon - consider regenerating'
            
            result['success'] = result['days_remaining'] is None or result['days_remaining'] >= 0
        else:
            result['error'] = 'Cannot decode certificate (ssl._ssl._test_decode_cert not available)'
            result['suggestion'] = 'Certificate may still be valid - check with openssl command'
            result['readable'] = True
            result['success'] = True  # Assume OK if we can't verify
            
    except Exception as e:
        result['error'] = '{}: {}'.format(type(e).__name__, str(e))
        result['suggestion'] = 'Certificate may be corrupted - try deleting and regenerating'
    
    return result


def run_all_selftests(port=8000, cert_file='server.cert', include_network=True):
    """
    Run all self-tests and return consolidated results.
    
    Args:
        port: Server port to test
        cert_file: Path to certificate file
        include_network: Whether to include network tests (requires server to be running)
        
    Returns:
        dict with all test results and summary
    """
    results = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tests': {},
        'summary': {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'all_passed': False
        }
    }
    
    # Always run certificate test
    results['tests']['certificate'] = selftest_certificate_validity(cert_file)
    
    # Run network tests if requested
    if include_network:
        results['tests']['tls_handshake'] = selftest_tls_handshake(port)
        results['tests']['http_request'] = selftest_http_request(port)
        results['tests']['cors_headers'] = selftest_cors_headers(port)
    
    # Calculate summary
    for test_name, test_result in results['tests'].items():
        results['summary']['total'] += 1
        if test_result.get('success'):
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1
    
    results['summary']['all_passed'] = results['summary']['failed'] == 0
    
    return results


# =============================================================================
# OPEN QUESTIONS AND REMAINING INVESTIGATION AREAS
# =============================================================================
#
# The following questions remain open regarding Firefox/HTTPS/XP connectivity:
#
# 1. TLS VERSION NEGOTIATION
#    - Does Firefox 52 ESR on XP negotiate TLS 1.0, 1.1, or 1.2?
#    - Is Python's ssl.wrap_socket() defaulting to a TLS version Firefox can use?
#    - Does the OpenSSL version on XP support TLS 1.2?
#    
#    TO INVESTIGATE: Run selftest_tls_handshake() and check 'tls_version' field.
#    User can also run: openssl s_client -connect 127.0.0.1:8000 -tls1
#
# 2. CERTIFICATE TRUST PERSISTENCE
#    - Firefox stores certificate exceptions in cert_override.txt
#    - On XP, this may be in: %APPDATA%\Mozilla\Firefox\Profiles\<profile>\cert_override.txt
#    - If cert is regenerated, the exception becomes invalid
#    
#    TO INVESTIGATE: Check if cert_override.txt has an entry for 127.0.0.1:8000
#
# 3. PRIVATE NETWORK ACCESS (PNA) BROWSER SUPPORT
#    - PNA requires Access-Control-Allow-Private-Network: true header
#    - This is a Chrome 94+ / Firefox 87+ feature
#    - Firefox 52 ESR (last XP version) may not require this header
#    
#    TO INVESTIGATE: Test with and without PNA header on actual Firefox 52 ESR
#
# 4. WINDOWS XP FIREWALL
#    - Windows XP Firewall may block Python even for localhost connections
#    - User may need to add exception for python.exe
#    
#    TO INVESTIGATE: Check firewall settings, try disabling temporarily
#
# 5. ANTIVIRUS SOFTWARE
#    - Some AV software on XP intercepts HTTPS connections
#    - This can cause certificate mismatch errors
#    
#    TO INVESTIGATE: Temporarily disable AV and test
#
# 6. LOCALHOST vs 127.0.0.1
#    - Some Firefox versions treat localhost and 127.0.0.1 differently
#    - Certificate should have both in SAN (checked: openssl.cnf has both)
#    
#    TO INVESTIGATE: Try both https://localhost:8000 and https://127.0.0.1:8000
#
# 7. HTTP/2 or KEEP-ALIVE ISSUES
#    - Older Firefox may have issues with certain HTTP features
#    - Server sends Connection: keep-alive which should be fine
#    
#    TO INVESTIGATE: Check Firefox network console for connection reuse issues
#
# 8. CONTENT SECURITY POLICY (CSP)
#    - webapp.html may have CSP headers that block connections
#    - This would appear in browser console as CSP violation
#    
#    TO INVESTIGATE: Check browser console for CSP errors
#
