"""
Lightweight Certificate Authority helper for MediLink Gmail HTTPS server.

Provides idempotent helpers for creating a local root CA, issuing managed
server certificates, and surfacing status metadata for diagnostics/UI layers.

Python 3.4.4 compatible – avoids pathlib/f-strings.
"""

from __future__ import print_function

import os
import shutil
import subprocess
import tempfile
import time

try:
    from MediCafe.core_utils import get_shared_config_loader
    _config_loader = get_shared_config_loader()
    if _config_loader:
        _central_log = _config_loader.log
    else:
        _central_log = None
except Exception:
    _central_log = None

try:
    from MediLink.gmail_http_utils import get_certificate_fingerprint as _get_fingerprint
except Exception:
    _get_fingerprint = None


class CertificateAuthorityError(Exception):
    """Raised when managed CA operations fail."""


def _log(message, level="INFO", log_fn=None):
    fn = log_fn or _central_log
    if fn:
        try:
            fn(message, level=level)
            return
        except Exception:
            pass
    try:
        print("[{}] {}".format(level, message))
    except Exception:
        pass


def resolve_default_ca_dir(local_storage_path=None):
    """
    Resolve a writable directory for storing CA artifacts.

    Preference order:
        1. %APPDATA%/MediLink/ca
        2. %LOCALAPPDATA%/MediLink/ca
        3. <local_storage_path>/ca (if provided)
        4. Current working directory ./ca
        5. System temp directory /tmp/medilink_ca
    """
    candidates = []
    appdata = os.environ.get('APPDATA')
    if appdata:
        candidates.append(os.path.join(appdata, 'MediLink', 'ca'))
    local_appdata = os.environ.get('LOCALAPPDATA')
    if local_appdata:
        candidates.append(os.path.join(local_appdata, 'MediLink', 'ca'))
    if local_storage_path:
        candidates.append(os.path.join(local_storage_path, 'ca'))
    candidates.append(os.path.join(os.getcwd(), 'ca'))
    candidates.append(os.path.join(tempfile.gettempdir(), 'medilink_ca'))

    for path in candidates:
        if not path:
            continue
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            return path
        except Exception:
            continue
    # Fallback – temp dir should always be available
    fallback = os.path.join(tempfile.gettempdir(), 'medilink_ca_fallback')
    if not os.path.exists(fallback):
        os.makedirs(fallback)
    return fallback


def create_profile(profile_name,
                   storage_root,
                   server_cert_path,
                   server_key_path,
                   openssl_config=None,
                   san_list=None,
                   root_subject=None,
                   server_subject=None,
                   csr_path=None):
    """Return a profile dict capturing all CA paths/settings."""
    profile_dir = os.path.join(storage_root, profile_name or 'default')
    san_values = list(san_list or ['127.0.0.1', 'localhost'])
    profile = {
        'name': profile_name or 'default',
        'storage_root': storage_root,
        'profile_dir': profile_dir,
        'root_key_path': os.path.join(profile_dir, 'myroot.key'),
        'root_cert_path': os.path.join(profile_dir, 'myroot.crt'),
        'serial_path': os.path.join(profile_dir, 'myroot.srl'),
        'server_cert_path': server_cert_path,
        'server_key_path': server_key_path,
        'server_csr_path': csr_path or (server_cert_path + '.csr'),
        'openssl_config': openssl_config,
        'san_list': san_values,
        'root_subject': root_subject or '/CN=MediLink Local Root CA',
        'server_subject': server_subject or '/CN=127.0.0.1',
        'root_valid_days': 3650,
        'root_key_bits': 2048,
        'server_key_bits': 2048,
        'server_valid_days': 365,
        'server_validity_margin_seconds': 86400,
        'openssl_bin': 'openssl',
    }
    return profile


def ensure_managed_certificate(profile, log=None, subprocess_module=subprocess):
    """
    Ensure root CA assets and the downstream server certificate are present/valid.

    Returns a status dict suitable for diagnostics payloads.
    """
    if not profile:
        raise CertificateAuthorityError("Profile is required for managed certificate flow")

    log_fn = lambda msg, level="INFO": _log(msg, level, log)

    ensure_root(profile, log=log_fn, subprocess_module=subprocess_module)
    issue_server_cert(profile, log=log_fn, subprocess_module=subprocess_module)
    return describe_status(profile, log=log_fn)


def ensure_root(profile, log=None, subprocess_module=subprocess):
    """Create root key/cert if missing or nearing expiry."""
    log_fn = lambda msg, level="INFO": _log(msg, level, log)
    _ensure_directory(profile.get('profile_dir'), log_fn)

    root_cert = profile.get('root_cert_path')
    root_key = profile.get('root_key_path')
    openssl_bin = profile.get('openssl_bin') or 'openssl'
    margin = profile.get('root_validity_margin_seconds', 604800)  # default 7 days

    if root_cert and os.path.exists(root_cert):
        if _is_cert_valid(root_cert, margin, subprocess_module, openssl_bin, log_fn):
            return
        log_fn("Root certificate near expiry or invalid; regenerating.", level="WARNING")

    root_key_bits = profile.get('root_key_bits', 2048)
    root_days = profile.get('root_valid_days', 3650)
    root_subject = profile.get('root_subject') or '/CN=MediLink Local Root CA'

    # Ensure subject starts with at least one slash for OpenSSL
    if root_subject and not root_subject.startswith('/'):
        root_subject = '/' + root_subject

    _run_cmd(
        [openssl_bin, 'genrsa', '-out', root_key, str(root_key_bits)],
        subprocess_module,
        log_fn,
        "Generating CA root key"
    )

    # CRITICAL ISSUE: Root certificate must have CA:TRUE and keyCertSign extensions
    # Problem: `openssl req -x509` does NOT support the `-extfile` flag (only `openssl x509` does).
    # Attempted solution: Two-step process:
    #   1. Generate initial certificate with `req -x509` (without extensions)
    #   2. Use `x509` command to copy and add CA extensions via `-extfile`
    # 
    # CURRENT STATUS: This approach may still not work correctly. The `x509` command with `-extfile`
    # might not properly apply extensions when copying an existing certificate. The root cert
    # verification below may still show CA:FALSE even after this two-step process.
    #
    # FUTURE DEBUGGING: If root cert still shows CA:FALSE after generation:
    #   - Check if `openssl x509 -in <temp> -out <final> -extensions v3_ca -extfile <ext>` actually applies extensions
    #   - Consider using `openssl ca` command instead (requires more setup but more reliable)
    #   - Alternative: Generate cert with a custom openssl.cnf that has x509_extensions = v3_ca in [req] section
    #   - Verify OpenSSL version: older versions may have different behavior with extension handling
    #
    # INSTRUMENTATION POINT: Log the exact OpenSSL commands executed and their output.
    # Also log the verification results (has_ca_true, has_key_cert_sign) to confirm extensions were applied.
    temp_cert = root_cert + '.tmp'
    cmd = [
        openssl_bin, 'req', '-x509', '-new', '-sha256',
        '-days', str(root_days),
        '-key', root_key,
        '-out', temp_cert,
        '-subj', root_subject
    ]
    
    openssl_cnf = profile.get('openssl_config')
    if openssl_cnf and os.path.exists(openssl_cnf):
        cmd.extend(['-config', openssl_cnf])
    else:
        # On Windows, many OpenSSL builds expect a config even if not strictly used for all fields
        possible_cnfs = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openssl.cnf'),
            'C:\\OpenSSL-Win32\\bin\\openssl.cnf',
            'C:\\OpenSSL-Win64\\bin\\openssl.cnf',
            'C:\\Program Files\\OpenSSL-Win64\\bin\\openssl.cnf'
        ]
        for cnf in possible_cnfs:
            if os.path.exists(cnf):
                cmd.extend(['-config', cnf])
                break
    
    _run_cmd(cmd, subprocess_module, log_fn, "Generating initial root certificate")
    
    # Create extension file with CA:TRUE and keyCertSign
    # These extensions are REQUIRED for the root cert to be recognized as a valid CA by browsers
    ext_file = None
    try:
        import tempfile
        ext_fd, ext_file = tempfile.mkstemp(suffix='.cnf', text=True)
        ext_content = '[ v3_ca ]\nbasicConstraints = critical,CA:TRUE\nkeyUsage = critical, cA, keyCertSign\nsubjectKeyIdentifier = hash\nauthorityKeyIdentifier = keyid:always,issuer:always\n'
        with os.fdopen(ext_fd, 'w') as f:
            f.write(ext_content)
    except Exception as ext_err:
        log_fn("Failed to create root CA extension file: {}. Root cert may be invalid.".format(ext_err), level="WARNING")
        ext_file = None
    
    if ext_file:
        # Attempt to add extensions using x509 command
        # NOTE: This may not work as expected - x509 might not apply extensions when copying
        ext_cmd = [
            openssl_bin, 'x509', '-in', temp_cert,
            '-out', root_cert,
            '-extensions', 'v3_ca',
            '-extfile', ext_file
        ]
        _run_cmd(ext_cmd, subprocess_module, log_fn, "Adding CA extensions to root certificate")
        # Clean up temp cert
        if os.path.exists(temp_cert):
            try:
                os.unlink(temp_cert)
            except Exception:
                pass
        # Clean up extension file
        if os.path.exists(ext_file):
            try:
                os.unlink(ext_file)
            except Exception:
                pass
    else:
        # Fallback: just rename temp cert if extension file creation failed
        if os.path.exists(temp_cert):
            try:
                if os.path.exists(root_cert):
                    os.unlink(root_cert)
                os.rename(temp_cert, root_cert)
            except Exception as rename_err:
                log_fn("Failed to rename temp cert: {}".format(rename_err), level="WARNING")
    
    # Verify the root certificate was created with correct extensions
    # INSTRUMENTATION POINT: This verification is critical - log the full OpenSSL output
    # and the boolean flags (has_ca_true, has_key_cert_sign) to confirm extensions were applied.
    # If verification fails, the root cert will be rejected by browsers even if installed.
    if root_cert and os.path.exists(root_cert):
        try:
            import subprocess as _sp
            verify_cmd = [openssl_bin, 'x509', '-in', root_cert, '-text', '-noout']
            verify_output = _sp.check_output(verify_cmd, stderr=_sp.PIPE).decode('utf-8', errors='ignore')
            has_ca_true = 'CA:TRUE' in verify_output
            has_key_cert_sign = 'keyCertSign' in verify_output or 'Certificate Sign' in verify_output
            if not has_ca_true or not has_key_cert_sign:
                log_fn("WARNING: Root certificate missing CA extensions! CA:TRUE={}, keyCertSign={}".format(has_ca_true, has_key_cert_sign), level="WARNING")
        except Exception as verify_err:
            log_fn("Could not verify root certificate extensions: {}".format(verify_err), level="WARNING")


def issue_server_cert(profile, log=None, san_list=None, subprocess_module=subprocess):
    """
    Issue or refresh the managed server certificate for the HTTPS listener.
    """
    log_fn = lambda msg, level="INFO": _log(msg, level, log)
    openssl_bin = profile.get('openssl_bin') or 'openssl'

    server_cert = profile.get('server_cert_path')
    server_key = profile.get('server_key_path')
    server_csr = profile.get('server_csr_path') or (server_cert + '.csr')
    server_days = profile.get('server_valid_days', 365)
    margin = profile.get('server_validity_margin_seconds', 86400)

    if server_cert and os.path.exists(server_cert):
        if _is_cert_valid(server_cert, margin, subprocess_module, openssl_bin, log_fn):
            return
        log_fn("Managed server certificate requires renewal.", level="INFO")

    _ensure_parent_directory(server_cert, log_fn)

    if not server_key or not os.path.exists(server_key):
        key_bits = profile.get('server_key_bits', 2048)
        _run_cmd(
            [openssl_bin, 'genrsa', '-out', server_key, str(key_bits)],
            subprocess_module,
            log_fn,
            "Generating server private key"
        )

    server_subject = profile.get('server_subject') or '/CN=127.0.0.1'
    # Ensure subject starts with at least one slash for OpenSSL
    if server_subject and not server_subject.startswith('/'):
        server_subject = '/' + server_subject

    cmd = [
        openssl_bin, 'req', '-new', '-sha256',
        '-key', server_key,
        '-out', server_csr,
        '-subj', server_subject
    ]
    openssl_cnf = profile.get('openssl_config')
    if openssl_cnf and os.path.exists(openssl_cnf):
        cmd.extend(['-config', openssl_cnf])
    else:
        possible_cnfs = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openssl.cnf'),
            'C:\\OpenSSL-Win32\\bin\\openssl.cnf',
            'C:\\OpenSSL-Win64\\bin\\openssl.cnf',
            'C:\\Program Files\\OpenSSL-Win64\\bin\\openssl.cnf'
        ]
        for cnf in possible_cnfs:
            if os.path.exists(cnf):
                cmd.extend(['-config', cnf])
                break
    _run_cmd(cmd, subprocess_module, log_fn, "Creating server CSR")

    san_file = None
    san_values = san_list if san_list is not None else profile.get('san_list')
    try:
        ext_args = []
        if san_values:
            san_file = _write_san_extension_file(san_values)
            if san_file:
                ext_args = ['-extfile', san_file, '-extensions', 'v3_req']

        sign_cmd = [
            openssl_bin, 'x509', '-req',
            '-in', server_csr,
            '-CA', profile.get('root_cert_path'),
            '-CAkey', profile.get('root_key_path'),
            '-out', server_cert,
            '-days', str(server_days),
            '-sha256'
        ]

        serial_path = profile.get('serial_path')
        if serial_path:
            sign_cmd.extend(['-CAserial', serial_path])
            if not os.path.exists(serial_path):
                sign_cmd.append('-CAcreateserial')
        else:
            sign_cmd.append('-CAcreateserial')

        if ext_args:
            sign_cmd.extend(ext_args)

        _run_cmd(sign_cmd, subprocess_module, log_fn, "Signing server certificate with managed root")
    finally:
        if san_file and os.path.exists(san_file):
            try:
                os.unlink(san_file)
            except Exception:
                pass


def export_root(profile, destination_path, log=None):
    """Copy the root certificate to a destination path for Firefox import."""
    log_fn = lambda msg, level="INFO": _log(msg, level, log)
    root_cert = profile.get('root_cert_path')
    if not root_cert or not os.path.exists(root_cert):
        raise CertificateAuthorityError("Root certificate not found; run ensure_root first.")
    _ensure_parent_directory(destination_path, log_fn)
    shutil.copyfile(root_cert, destination_path)
    log_fn("Exported managed root certificate to {}".format(destination_path))


def describe_status(profile, log=None):
    """Return metadata about the managed CA and issued server cert."""
    openssl_bin = profile.get('openssl_bin') or 'openssl'
    status = {
        'profile': profile.get('name', 'default'),
        'storage': profile.get('profile_dir'),
        'root': _collect_cert_details(profile.get('root_cert_path'), openssl_bin),
        'server': _collect_cert_details(profile.get('server_cert_path'), openssl_bin),
        'san': profile.get('san_list') or [],
        'server_cert_path': profile.get('server_cert_path'),
        'root_cert_path': profile.get('root_cert_path'),
        'mode': 'managed_ca'
    }
    if _get_fingerprint and profile.get('server_cert_path'):
        try:
            status['server'].update(_get_fingerprint(profile['server_cert_path']))
        except Exception:
            pass
    return status


def _ensure_directory(path, log_fn):
    if not path:
        raise CertificateAuthorityError("Profile directory not provided")
    if not os.path.exists(path):
        os.makedirs(path)
        log_fn("Created CA storage directory at {}".format(path))


def _ensure_parent_directory(path, log_fn):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent)
        log_fn("Created directory {}".format(parent))


def _run_cmd(cmd, subprocess_module, log_fn, description):
    log_fn("{}: {}".format(description, ' '.join(cmd)), level="DEBUG")
    # INSTRUMENTATION POINT: Log all OpenSSL commands executed here to debug certificate generation issues.
    # Log the full command, exit code, and any stderr output to identify command failures.
    result = subprocess_module.call(cmd)
    if result != 0:
        raise CertificateAuthorityError("{} failed with exit code {}".format(description, result))


def _is_cert_valid(cert_path, threshold_seconds, subprocess_module, openssl_bin, log_fn):
    if not cert_path or not os.path.exists(cert_path):
        return False
    try:
        cmd = [openssl_bin, 'x509', '-in', cert_path, '-checkend', str(int(threshold_seconds)), '-noout']
        result = subprocess_module.call(cmd, stdout=subprocess_module.PIPE, stderr=subprocess_module.PIPE)
        return result == 0
    except Exception as exc:
        log_fn("Certificate validation check failed for {}: {}".format(cert_path, exc), level="DEBUG")
        return False


def _write_san_extension_file(san_entries):
    if not san_entries:
        return None
    formatted = []
    for entry in san_entries:
        value = (entry or '').strip()
        if not value:
            continue
        if _looks_like_ip(value):
            formatted.append('IP:{}'.format(value))
        else:
            formatted.append('DNS:{}'.format(value))
    if not formatted:
        return None
    lines = [
        '[v3_req]',
        'subjectAltName = {}'.format(', '.join(formatted)),
        'extendedKeyUsage = serverAuth, clientAuth',
        'keyUsage = digitalSignature, keyEncipherment'
    ]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.cnf')
    tmp.write('\n'.join(lines).encode('utf-8'))
    tmp.close()
    return tmp.name


def _looks_like_ip(value):
    if ':' in value:
        return True  # treat IPv6-ish as IP
    parts = value.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False
    return True


def _collect_cert_details(cert_path, openssl_bin):
    info = {
        'present': bool(cert_path and os.path.exists(cert_path)),
        'subject': None,
        'issuer': None,
        'notBefore': None,
        'notAfter': None,
        'serial': None
    }
    if not info['present']:
        return info
    try:
        cmd = [openssl_bin, 'x509', '-in', cert_path, '-noout', '-subject', '-issuer', '-enddate', '-serial']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        data = output.decode('utf-8', errors='ignore').splitlines()
        for line in data:
            if line.startswith('subject='):
                info['subject'] = line.split('subject=', 1)[1].strip()
            elif line.startswith('issuer='):
                info['issuer'] = line.split('issuer=', 1)[1].strip()
            elif line.startswith('notAfter='):
                info['notAfter'] = line.split('notAfter=', 1)[1].strip()
            elif line.startswith('serial='):
                info['serial'] = line.split('serial=', 1)[1].strip()
        # Approximate notBefore via -dates if needed
        try:
            cmd_dates = [openssl_bin, 'x509', '-in', cert_path, '-noout', '-dates']
            dates_output = subprocess.check_output(cmd_dates, stderr=subprocess.STDOUT)
            for line in dates_output.decode('utf-8', errors='ignore').splitlines():
                if line.startswith('notBefore='):
                    info['notBefore'] = line.split('notBefore=', 1)[1].strip()
                elif line.startswith('notAfter=') and not info['notAfter']:
                    info['notAfter'] = line.split('notAfter=', 1)[1].strip()
        except Exception:
            pass
    except Exception:
        pass
    return info
