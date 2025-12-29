import errno
import json
import os
import ssl
import subprocess
import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# Try to import centralized logging
try:
    from MediCafe.core_utils import get_shared_config_loader
    _config_loader = get_shared_config_loader()
    if _config_loader:
        _central_log = _config_loader.log
    else:
        _central_log = None
except ImportError:
    _central_log = None


def _is_expected_disconnect(error):
    """
    Return True for socket errors that occur when a browser drops the TLS
    connection before completing the HTTP request (e.g., WinError 10053).
    """
    expected_errno_names = [
        'ECONNRESET',
        'ECONNABORTED',
        'ETIMEDOUT',
        'EPIPE',
        'ESHUTDOWN',
    ]
    expected_errnos = {getattr(errno, name, None) for name in expected_errno_names}
    expected_errnos.discard(None)
    expected_winerrors = {10053, 10054, 10060}
    err_no = getattr(error, 'errno', None)
    win_err = getattr(error, 'winerror', None)
    if err_no in expected_errnos or win_err in expected_winerrors:
        return True
    error_text = str(error).lower()
    return any(token in error_text for token in ('connection reset', 'connection aborted', 'broken pipe'))


def generate_self_signed_cert(openssl_cnf_path, cert_file, key_file, log, subprocess_module, cert_days=365):
    log("Checking if certificate file exists: " + cert_file)
    log("Checking if key file exists: " + key_file)

    cert_needs_regeneration = True
    if os.path.exists(cert_file):
        # #region agent log
        try:
            cert_text = subprocess.check_output(['openssl', 'x509', '-in', cert_file, '-text', '-noout']).decode('utf-8', errors='ignore')
            with open(r'g:\My Drive\Codes\MediCafe\.cursor\debug.log', 'a') as f:
                import json as _json
                import time as _time
                f.write(_json.dumps({"sessionId":"debug-session", "runId":"run12", "hypothesisId":"G", "location":"gmail_http_utils.py:generate_self_signed_cert", "message":"Existing certificate found", "data":{"text": cert_text}, "timestamp":int(_time.time()*1000)}) + "\n")
        except Exception as e:
            pass
        # #endregion
        try:
            check_cmd = ['openssl', 'x509', '-in', cert_file, '-checkend', '86400', '-noout']
            result = subprocess_module.call(check_cmd)
            if result == 0:
                log("Certificate is still valid")
                cert_needs_regeneration = False
            else:
                log("Certificate is expired or will expire soon")
                try:
                    if os.path.exists(cert_file):
                        os.remove(cert_file)
                        log("Deleted expired certificate file: {}".format(cert_file))
                    if os.path.exists(key_file):
                        os.remove(key_file)
                        log("Deleted expired key file: {}".format(key_file))
                except (IOError, OSError) as e:
                    log("Error deleting expired certificate files: {}".format(e))
        except (IOError, OSError, subprocess.CalledProcessError) as e:
            log("Error checking certificate expiration: {}".format(e))

    if cert_needs_regeneration:
        log("Generating self-signed SSL certificate...")
        cmd = [
            'openssl', 'req', '-config', openssl_cnf_path, '-nodes', '-new', '-x509',
            '-keyout', key_file,
            '-out', cert_file,
            '-days', str(cert_days),
            '-sha256',
            '-subj', '/CN=127.0.0.1'
        ]
        try:
            log("Running command: " + ' '.join(cmd))
            result = subprocess_module.call(cmd)
            log("Command finished with result: " + str(result))
            if result != 0:
                raise RuntimeError("Failed to generate self-signed certificate")
            
            # INSTRUMENTATION POINT: After certificate generation, log the full certificate text
            # (subject, issuer, SAN entries, extensions) to verify it was created correctly.

            verify_cmd = ['openssl', 'x509', '-in', cert_file, '-text', '-noout']
            verify_result = subprocess_module.call(verify_cmd)
            if verify_result != 0:
                raise RuntimeError("Generated certificate verification failed")
            log("Self-signed SSL certificate generated and verified successfully.")
        except (IOError, OSError, subprocess.CalledProcessError, RuntimeError) as e:
            log("Error generating self-signed certificate: {}".format(e))
            raise


def get_certificate_fingerprint(cert_path, log=None):
    """Get certificate fingerprint in SHA-256 and SHA-1 formats.
    
    Extracts fingerprints using OpenSSL for display in certificate info pages.
    Useful for users to verify the certificate matches what their browser shows
    when adding a certificate exception (especially Firefox 52/XP).
    
    Args:
        cert_path: Path to certificate file
        log: Optional logging function (uses _central_log if available, else no-op)
    
    Returns:
        dict with keys:
            - 'sha256': SHA-256 fingerprint (hex, no colons)
            - 'sha1': SHA-1 fingerprint (hex, no colons)
            - 'sha256_colon': SHA-256 fingerprint (colon-separated, uppercase)
            - 'sha1_colon': SHA-1 fingerprint (colon-separated, uppercase)
        Values are None if extraction fails for that format.
    """
    fingerprint = {
        'sha256': None,
        'sha1': None,
        'sha256_colon': None,
        'sha1_colon': None
    }
    
    # Use provided log function or fallback to central log or no-op
    log_fn = log if log else (_central_log if _central_log else lambda msg, level="INFO": None)
    
    try:
        if not os.path.exists(cert_path):
            return fingerprint
        
        # Get SHA-256 fingerprint
        try:
            cmd = ['openssl', 'x509', '-in', cert_path, '-fingerprint', '-sha256', '-noout']
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            result_str = result.decode('utf-8', errors='ignore')
            if 'SHA256 Fingerprint=' in result_str:
                fp_raw = result_str.split('SHA256 Fingerprint=')[1].strip()
                fingerprint['sha256'] = fp_raw.replace(':', '').lower()
                fingerprint['sha256_colon'] = fp_raw.upper()
        except (OSError, subprocess.CalledProcessError, ValueError) as e:
            log_fn("Error extracting SHA-256 fingerprint: {}".format(e), level="DEBUG")
        
        # Get SHA-1 fingerprint (for Firefox 52 compatibility - older browsers may show SHA-1)
        try:
            cmd = ['openssl', 'x509', '-in', cert_path, '-fingerprint', '-sha1', '-noout']
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            result_str = result.decode('utf-8', errors='ignore')
            if 'SHA1 Fingerprint=' in result_str:
                fp_raw = result_str.split('SHA1 Fingerprint=')[1].strip()
                fingerprint['sha1'] = fp_raw.replace(':', '').lower()
                fingerprint['sha1_colon'] = fp_raw.upper()
        except (OSError, subprocess.CalledProcessError, ValueError) as e:
            log_fn("Error extracting SHA-1 fingerprint: {}".format(e), level="DEBUG")
            
    except Exception as e:
        log_fn("Error extracting certificate fingerprint: {}".format(e), level="DEBUG")
    
    return fingerprint


def create_ssl_context_for_server(cert_file, key_file, log=None):
    """
    Create an SSL context optimized for compatibility with older browsers
    including Firefox 52 ESR on Windows XP.
    
    Python 3.4.4 compatible - uses ssl.wrap_socket fallback if needed.
    
    Args:
        cert_file: Path to certificate file
        key_file: Path to private key file
        log: Optional logging function
        
    Returns:
        ssl.SSLContext or None (use wrap_socket fallback)
    """
    # Try to create an SSLContext with explicit protocol support
    # This is preferred over wrap_socket for better control
    context = None
    
    try:
        # Python 3.4+ should have SSLContext
        if hasattr(ssl, 'SSLContext'):
            # Use PROTOCOL_TLS if available (Python 3.6+), otherwise TLS v1
            protocol = "UNKNOWN"
            if hasattr(ssl, 'PROTOCOL_TLS'):
                context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                protocol = "PROTOCOL_TLS"
            elif hasattr(ssl, 'PROTOCOL_SSLv23'):
                # SSLv23 actually means "negotiate highest available" and includes TLS
                context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                protocol = "PROTOCOL_SSLv23"
            
            # Use a modern cipher string to ensure compatibility with modern browsers
            # while still allowing some older ones if needed.
            # This is a balanced string that favors modern GCM and ChaCha ciphers.
            try:
                context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
            except Exception as cipher_err:
                if log:
                    log("Warning: Could not set modern cipher string: {}. Using defaults.".format(cipher_err))
            
            # INSTRUMENTATION POINT: Log SSLContext creation details (protocol, OpenSSL version, cipher list)
            # to debug TLS handshake failures and protocol negotiation issues.
            if context:
                # Load certificate and key
                # INSTRUMENTATION POINT: Log certificate details (subject, issuer, SAN) when loading into SSLContext.
                # This helps verify the correct certificate is being used for the server.
                context.load_cert_chain(cert_file, key_file)
                
                # Enable TLS 1.0, 1.1, 1.2 for Windows XP Firefox 52 ESR compatibility
                # Disable SSLv2 and SSLv3 (insecure)
                if hasattr(ssl, 'OP_NO_SSLv2'):
                    context.options |= ssl.OP_NO_SSLv2
                if hasattr(ssl, 'OP_NO_SSLv3'):
                    context.options |= ssl.OP_NO_SSLv3
                
                # Allow TLS 1.0 and 1.1 for older Firefox (don't disable them)
                # These are needed for Firefox 52 ESR on Windows XP
                
                if log:
                    log("SSL context created with TLS support for XP compatibility")
                    
    except Exception as e:
        if log:
            log("Could not create SSLContext, will use wrap_socket fallback: {}".format(e))
        context = None
    
    return context


def wrap_socket_for_server(socket, cert_file, key_file, log=None):
    """
    Wrap a socket with SSL for the HTTPS server.
    Tries SSLContext first for better control, falls back to wrap_socket.
    
    Args:
        socket: The socket to wrap
        cert_file: Path to certificate file
        key_file: Path to private key file
        log: Optional logging function
        
    Returns:
        SSL-wrapped socket
    """
    context = create_ssl_context_for_server(cert_file, key_file, log)
    
    if context:
        # Use context.wrap_socket for better control
        return context.wrap_socket(socket, server_side=True)
    else:
        # Fallback to deprecated ssl.wrap_socket for Python 3.4.4 compatibility
        if log:
            log("Using ssl.wrap_socket fallback (deprecated but compatible)")
        return ssl.wrap_socket(socket, certfile=cert_file, keyfile=key_file, server_side=True)


def start_https_server(port, handler_cls, cert_file, key_file, log):
    """
    Start the HTTPS server with SSL socket wrapping.
    Uses XP-compatible TLS configuration.
    """
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, handler_cls)
    log("Attempting to wrap socket with SSL. cert_file=" + cert_file + ", key_file=" + key_file)
    httpd.socket = wrap_socket_for_server(httpd.socket, cert_file, key_file, log)
    log("Starting HTTPS server on port {}".format(port))
    httpd.serve_forever()
    return httpd


def inspect_token(access_token, log, delete_token_file_fn=None, stop_server_fn=None):
    # Import the constant from oauth_utils
    try:
        from MediLink.gmail_oauth_utils import GOOGLE_TOKENINFO_URL
        info_url = GOOGLE_TOKENINFO_URL + "?access_token={}".format(access_token)
    except ImportError:
        # Fallback to hardcoded URL if import fails
        info_url = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}".format(access_token)
    try:
        response = requests.get(info_url)
        log("Token info: Status code {}, Body: {}".format(response.status_code, response.text), level="DEBUG")
        if response.status_code == 200:
            return response.json()
        else:
            log("Failed to inspect token. Status code: {}, Body: {}".format(response.status_code, response.text))
            if response.status_code == 400 and "invalid_token" in response.text:
                # Token is invalid (revoked/expired). Clear cache and let caller trigger re-auth.
                log("Access token is invalid. Clearing token cache and keeping server running for re-auth.")
                if delete_token_file_fn:
                    delete_token_file_fn()
                return None
            return None
    except (requests.exceptions.RequestException, ValueError) as e:
        log("Exception during token inspection: {}".format(e))
        return None


class SSLRequestHandler(BaseHTTPRequestHandler):
    """
    Enhanced RequestHandler that suppresses expected SSL certificate warnings.
    Python 3.4.4 compatible.
    """
    def setup(self):
        """Perform SSL handshake in the thread before setting up the regular handler."""
        # Check if server is in HTTP mode (no SSL)
        server = self.server
        use_http = getattr(server, 'use_http', False)
        
        if use_http:
            # HTTP mode: skip SSL wrapping, call parent setup directly
            BaseHTTPRequestHandler.setup(self)
            return
        
        # HTTPS mode: proceed with SSL wrapping
        # The base setup() assigns self.request to self.connection
        # We need to wrap self.request (the raw socket) with SSL
        raw_sock = self.request
        # Set handshake timeout
        raw_sock.settimeout(30.0)
        
        try:
            # INSTRUMENTATION POINT: Log TLS handshake start (client address, server context availability).
            # This is critical for debugging SSLV3_ALERT_CERTIFICATE_UNKNOWN errors.
            
            # Access the server's context if available
            context = getattr(server, 'context', None)
            
            if context:
                ssl_sock = context.wrap_socket(raw_sock, server_side=True)
            else:
                # Fallback to server's cert/key paths
                cert = getattr(server, 'cert_file', 'server.cert')
                key = getattr(server, 'key_file', 'server.key')
                import ssl
                ssl_sock = ssl.wrap_socket(raw_sock, certfile=cert, keyfile=key, server_side=True)
            
            # Successful handshake - update self.request
            self.request = ssl_sock
            # Call parent setup with the wrapped socket
            BaseHTTPRequestHandler.setup(self)
            
            # INSTRUMENTATION POINT: Log successful handshake details (negotiated cipher, TLS version).
            # Compare successful vs failed handshakes to identify certificate/trust issues.
            
        except Exception as e:
            # INSTRUMENTATION POINT: Log handshake failures with full traceback and error details.
            # Common errors: SSLV3_ALERT_CERTIFICATE_UNKNOWN (certificate trust issue),
            # SSL: CERTIFICATE_VERIFY_FAILED (certificate validation failure).
            # Silently close if handshake fails to prevent crashes
            try:
                raw_sock.close()
            except: pass
            # Raise to abort this request thread
            raise

    def handle_one_request(self):
        """Override to catch SSL errors and suppress expected certificate warnings"""
        # INSTRUMENTATION POINT: Log request handling start (client address, negotiated cipher/TLS version).
        # This helps correlate handshake success with request processing.
        try:
            super().handle_one_request()
        except ssl.SSLError as e:
            # INSTRUMENTATION POINT: Log SSLError details (errno, library, reason) to identify specific SSL issues.
            # Some errors are expected (certificate warnings) but others indicate real problems.
            # SSL errors are expected with self-signed certs when client accepts warning
            error_str = str(e).lower()
            if "unknown ca" in error_str or "certificate" in error_str:
                # Expected SSL warning - client can accept and proceed
                # Don't log expected certificate warnings as they are normal behavior
                pass
            else:
                # Unexpected SSL error - log at WARNING level
                if _central_log:
                    _central_log("Unexpected SSL error in request handler: {}".format(e), level="WARNING")
        except OSError as e:
            # INSTRUMENTATION POINT: Log OSError details (errno, winerror) to identify connection issues.
            # Common causes: client disconnect, network errors, socket closure.
            if _is_expected_disconnect(e):
                # Browser closed the socket before sending a full request; keep server alive.
                self.close_connection = True
                if _central_log:
                    _central_log("Client disconnected during TLS negotiation: {}".format(e), level="DEBUG")
            else:
                raise
        except Exception as e:
            # INSTRUMENTATION POINT: Log unexpected exceptions with full traceback to catch edge cases.
            # Log unexpected exceptions at ERROR level before re-raising
            # This helps diagnose server crashes
            if _central_log:
                import traceback
                try:
                    tb_str = traceback.format_exc()
                    _central_log("Unexpected exception in handle_one_request: {} - Traceback: {}".format(e, tb_str), level="ERROR")
                except Exception:
                    _central_log("Unexpected exception in handle_one_request: {}".format(e), level="ERROR")
            # Re-raise non-SSL exceptions so they can be captured upstream
            raise
        except Exception as e:
            # Log unexpected exceptions at ERROR level before re-raising
            # This helps diagnose server crashes
            if _central_log:
                import traceback
                try:
                    tb_str = traceback.format_exc()
                    _central_log("Unexpected exception in handle_one_request: {} - Traceback: {}".format(e, tb_str), level="ERROR")
                except Exception:
                    _central_log("Unexpected exception in handle_one_request: {}".format(e), level="ERROR")
            # Re-raise non-SSL exceptions so they can be captured upstream
            raise


def set_standard_headers(handler, content_type='application/json'):
    """Set standard HTTP headers: CORS, keep-alive, and content type."""
    # Extract origin for CORS and logging
    origin = handler.headers.get('Origin', '*')
    req_pna = handler.headers.get('Access-Control-Request-Private-Network', 'None')
    
    # INSTRUMENTATION POINT: Log CORS/PNA header values being sent (Origin, Access-Control-Allow-Private-Network).
    # This helps debug "unknown address space" CORS errors from cross-origin requests.
    
    # CORS headers - origin must be explicit or * (explicit preferred for credentials)
    # For Credentials=true, Origin cannot be '*'
    if origin == '*':
        # Fallback to a safe default if no origin provided, though usually browser sends it
        handler.send_header('Access-Control-Allow-Origin', '*')
    else:
        handler.send_header('Access-Control-Allow-Origin', origin)
        handler.send_header('Access-Control-Allow-Credentials', 'true')
    
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Access-Control-Allow-Private-Network')
    
    # Private Network Access (PNA) - required for modern Chrome/Edge to hit local IPs
    handler.send_header('Access-Control-Allow-Private-Network', 'true')
    
    # Preflight caching
    handler.send_header('Access-Control-Max-Age', '1728000')
    
    # Help browser realize headers depend on Origin and PNA state
    handler.send_header('Vary', 'Origin, Access-Control-Request-Private-Network')
    
    # Keep-alive headers
    handler.send_header('Connection', 'keep-alive')
    handler.send_header('Keep-Alive', 'timeout=60')
    
    # Content type
    if content_type:
        handler.send_header('Content-type', content_type)


def send_error_response(handler, status_code, message, log_fn=None, error_details=None):
    """Send a standardized JSON error response with proper exception handling.
    
    Args:
        handler: The HTTP request handler instance
        status_code: HTTP status code (e.g., 400, 500)
        message: Error message to include in response
        log_fn: Optional logging function
        error_details: Optional additional error details for logging
    """
    try:
        handler.send_response(status_code)
        set_standard_headers(handler)
        handler.end_headers()
        error_response = json.dumps({"status": "error", "message": message})
        safe_write_response(handler, error_response.encode('utf-8'))
        if log_fn and error_details:
            log_fn("Sent error response {}: {} - Details: {}".format(status_code, message, error_details), level="ERROR")
    except Exception as e:
        # If we can't send error response, log it but don't crash
        if log_fn:
            try:
                log_fn("Failed to send error response: {}".format(e), level="ERROR")
            except Exception:
                pass


def safe_write_response(handler, data, expected_disconnect_fn=None):
    """Safely write response data, handling client disconnects gracefully.
    
    Args:
        handler: The HTTP request handler instance
        data: Bytes or string to write
        expected_disconnect_fn: Optional function to check if disconnect is expected
    """
    if expected_disconnect_fn is None:
        expected_disconnect_fn = _is_expected_disconnect
    
    try:
        if isinstance(data, str):
            data = data.encode('utf-8')
        handler.wfile.write(data)
    except OSError as e:
        if expected_disconnect_fn(e):
            handler.close_connection = True
        else:
            raise


def log_request_error(error, request_path, method, log_fn, headers=None, include_traceback=True):
    """Log request handler errors with comprehensive diagnostic context.
    
    Args:
        error: The exception that occurred
        request_path: The request path
        method: HTTP method (GET, POST, etc.)
        log_fn: Logging function
        headers: Optional request headers dict
        include_traceback: Whether to include full traceback
    """
    if not log_fn:
        return
    
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Log basic error information
    log_fn("Unexpected error in {} for path {}: {}: {}".format(method, request_path, error_type, error_msg), level="ERROR")
    
    # Include traceback if requested
    if include_traceback:
        try:
            import traceback
            tb_str = traceback.format_exc()
            log_fn("{} error traceback for path {}: {}".format(method, request_path, tb_str), level="ERROR")
        except Exception:
            pass
    
    # Log diagnostic context
    try:
        context_parts = ["Path: {}".format(request_path), "Method: {}".format(method)]
        if headers:
            if hasattr(headers, 'get'):
                content_length = headers.get('Content-Length', 'unknown')
                context_parts.append("Content-Length header: {}".format(content_length))
        log_fn("{} error context - {}".format(method, ", ".join(context_parts)), level="ERROR")
    except Exception:
        pass


def parse_content_length(headers, log_fn=None):
    """Safely parse Content-Length header from request.
    
    Returns:
        int: Content length, or None if missing/invalid
        
    Raises:
        KeyError: If Content-Length header is missing
        ValueError: If Content-Length is not a valid integer
    """
    if 'Content-Length' not in headers:
        raise KeyError("Content-Length header is missing")
    try:
        return int(headers['Content-Length'])
    except ValueError as e:
        if log_fn:
            log_fn("Invalid Content-Length header value: {} - This usually indicates a malformed HTTP request from the client (missing or non-numeric Content-Length header)".format(headers['Content-Length']), level="ERROR")
        raise ValueError("Invalid Content-Length header: {}".format(headers['Content-Length']))


def read_post_data(handler, content_length, expected_disconnect_fn=None, log_fn=None):
    """Safely read POST data from request, handling client disconnects.
    
    Args:
        handler: The HTTP request handler instance
        content_length: Expected content length
        expected_disconnect_fn: Optional function to check if disconnect is expected
        log_fn: Optional logging function
        
    Returns:
        bytes: POST data, or None if client disconnected
    """
    if expected_disconnect_fn is None:
        expected_disconnect_fn = _is_expected_disconnect
    
    try:
        data = handler.rfile.read(content_length)
        return data
    except OSError as e:
        if expected_disconnect_fn(e):
            if log_fn:
                log_fn("Client disconnected while reading POST data", level="DEBUG")
            handler.close_connection = True
            return None
        else:
            raise


def parse_json_data(data, log_fn=None):
    """Safely parse JSON data from POST request body.
    
    Args:
        data: Bytes or string containing JSON
        log_fn: Optional logging function
        
    Returns:
        dict: Parsed JSON data
        
    Raises:
        ValueError: If JSON is invalid
        UnicodeDecodeError: If encoding is invalid
    """
    try:
        if isinstance(data, bytes):
            decoded = data.decode('utf-8')
        else:
            decoded = data
        return json.loads(decoded)
    except (ValueError, UnicodeDecodeError) as e:
        if log_fn:
            log_fn("Invalid JSON or encoding in POST request: {} - This usually indicates corrupted request data, encoding mismatch, or malformed JSON from the client webapp".format(e), level="ERROR")
        raise

