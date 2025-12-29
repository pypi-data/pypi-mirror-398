# MediCafe/network_route_helpers.py
"""
Route mismatch remediation helpers for MediCafe.
Keeps XP/DNS-specific logic out of core request handling paths.

COMPATIBILITY: Python 3.4.4 and Windows XP compatible
"""

import os
import json
import platform

try:
    from MediCafe.core_utils import get_shared_config_loader, run_cmd  # type: ignore
    MediLink_ConfigLoader = get_shared_config_loader()
except ImportError:
    try:
        from .core_utils import get_shared_config_loader, run_cmd  # type: ignore
        MediLink_ConfigLoader = get_shared_config_loader()
    except ImportError:
        run_cmd = None  # type: ignore
        try:
            from MediCafe.MediLink_ConfigLoader import MediLink_ConfigLoader  # type: ignore
        except ImportError:
            MediLink_ConfigLoader = None  # type: ignore

ROUTE_404_HINT = "Hint: verify endpoint configuration and rerun after DNS flush (ipconfig /flushdns on Windows XP)."


def handle_route_mismatch_404(status_code, response_content, method, url, console_flag=False):
    """
    Run lightweight remediation when we see 404 'no route matched' behaviour.
    Performs multiple XP-compatible network stack remediations:
    - DNS cache flush (ipconfig /flushdns) - immediate effect, safe
    - Winsock catalog reset (netsh winsock reset) - requires reboot to take effect
    - TCP/IP stack reset (netsh int ip reset) - requires reboot to take effect
    
    Note: Winsock and TCP/IP resets will not help the immediate retry but may
    resolve underlying network stack corruption after system reboot.

    Returns:
        bool: True if the caller should retry the request, False otherwise.
    """
    if not MediLink_ConfigLoader:
        return False
    if not _is_route_mismatch_404(status_code, response_content):
        return False

    log = MediLink_ConfigLoader.log
    log(
        "Detected 404 'no route matched' for {} {}. Evaluating network stack remediation.".format(method, url),
        level="WARNING",
        console_output=console_flag
    )

    if not _is_windows_host():
        log(
            "Network remediation automation skipped: host OS is not Windows.",
            level="INFO",
            console_output=console_flag
        )
        return True

    if not _is_windows_xp_family():
        log(
            "Network remediation automation skipped: host release {} is outside Windows XP/2003 lineage.".format(_get_platform_release()),
            level="INFO",
            console_output=console_flag
        )
        return True

    if run_cmd is None:
        log(
            "Network remediation automation skipped: command runner unavailable in this runtime.",
            level="WARNING",
            console_output=console_flag
        )
        return True

    # Define remediation steps: DNS flush (immediate), then stack resets (require reboot)
    remediation_steps = [
        ('DNS cache flush', ['ipconfig', '/flushdns'], True),  # immediate effect
        ('Winsock catalog reset', ['netsh', 'winsock', 'reset'], False),  # requires reboot
        ('TCP/IP stack reset', ['netsh', 'int', 'ip', 'reset'], False)  # requires reboot
    ]
    
    dns_flush_succeeded = False
    stack_resets_attempted = False
    
    for step_name, cmd, is_immediate in remediation_steps:
        rc, stdout_text, stderr_text = run_cmd(cmd)
        stdout_sanitized = _sanitize_log(stdout_text)
        stderr_sanitized = _sanitize_log(stderr_text)
        
        if rc == 0:
            log(
                "{} completed successfully. stdout: {}".format(step_name, stdout_sanitized or "<<empty>>"),
                level="WARNING",
                console_output=console_flag
            )
            if is_immediate:
                dns_flush_succeeded = True
            else:
                stack_resets_attempted = True
        else:
            # Log as WARNING for stack resets (may require admin), ERROR only for DNS flush
            log_level = "WARNING" if not is_immediate else "ERROR"
            log(
                "{} returned {}. stdout: {} stderr: {}".format(
                    step_name,
                    rc,
                    stdout_sanitized or "<<empty>>",
                    stderr_sanitized or "<<empty>>"
                ),
                level=log_level,
                console_output=console_flag
            )
            # Track attempt even if it failed (for informational messages)
            if not is_immediate:
                stack_resets_attempted = True
    
    # Provide appropriate guidance based on results
    if dns_flush_succeeded:
        log(
            "DNS cache flushed. Retry the provider call to confirm route restoration.",
            level="INFO",
            console_output=console_flag
        )
    
    if stack_resets_attempted:
        log(
            "Network stack resets completed. Note: Winsock and TCP/IP resets require a system reboot to take full effect.",
            level="INFO",
            console_output=console_flag
        )
        log(
            "If DNS flush does not resolve the issue, reboot the system to activate the stack resets.",
            level="INFO",
            console_output=console_flag
        )

    return True


def _is_route_mismatch_404(status_code, response_content):
    try:
        if int(status_code) != 404:
            return False
    except Exception:
        return False
    body_text = _normalize_text(response_content)
    if not body_text:
        return False
    if "no route matched" in body_text:
        return True
    return "no route" in body_text and "matched" in body_text


def _normalize_text(value):
    try:
        if isinstance(value, (dict, list)):
            return json.dumps(value).lower()
    except Exception:
        pass
    try:
        return str(value).strip().lower()
    except Exception:
        return ""


def _is_windows_host():
    try:
        system_name = platform.system()
        if system_name:
            return system_name.lower().startswith('win')
    except Exception:
        pass
    return os.name == 'nt'


def _get_platform_release():
    try:
        release = platform.release()
    except Exception:
        release = ''
    try:
        version = platform.version()
    except Exception:
        version = ''
    if release and version:
        return "{} ({})".format(release, version)
    return release or version or "unknown"


def _is_windows_xp_family():
    if not _is_windows_host():
        return False
    release = ''
    version = ''
    try:
        release = (platform.release() or '').lower()
    except Exception:
        release = ''
    try:
        version = (platform.version() or '').lower()
    except Exception:
        version = ''
    if any(token in release for token in ('xp', '5.1', '5.2', '2003')):
        return True
    if version.startswith('5.1') or version.startswith('5.2'):
        return True
    return False


def _sanitize_log(value, limit=300):
    text = _normalize_text(value)
    if not text:
        return ''
    text = text.replace('\r', ' ').replace('\n', ' ')
    if len(text) > limit:
        text = text[:limit] + '...'
    return text


__all__ = (
    'handle_route_mismatch_404',
    'ROUTE_404_HINT',
)
