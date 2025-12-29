# MediLink_IP_utils.py
"""
IP address utility functions for OPTUMEDI endpoint validation.
Detects private and public IP addresses for validation against allowed static IPs.

COMPATIBILITY: Python 3.4.4 and Windows XP compatible
"""
import socket
import subprocess
import time

# Cache IP addresses for performance (avoid repeated lookups in same session)
_IP_CACHE = {
    'private': None,
    'public': None,
    'cache_time': None
}
_CACHE_TTL = 300  # Cache for 5 minutes


def get_private_ip_addresses():
    """
    Get all private/local IP addresses from network adapters.
    Filters out loopback addresses (127.x.x.x).
    
    Returns:
        list: List of private IP address strings (IPv4 only)
    
    COMPATIBILITY: Python 3.4.4 and Windows XP compatible
    """
    global _IP_CACHE
    
    # Check cache first
    if _IP_CACHE['private'] is not None and _IP_CACHE['cache_time'] is not None:
        if time.time() - _IP_CACHE['cache_time'] < _CACHE_TTL:
            return _IP_CACHE['private']
    
    private_ips = []
    
    try:
        # Method 1: Use socket.gethostbyname_ex() - gets all IPs for hostname
        hostname = socket.gethostname()
        # gethostbyname_ex returns (hostname, aliaslist, ipaddrlist)
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        
        for ip in ip_list:
            # Filter out loopback addresses and only include IPv4
            if ip and not ip.startswith('127.'):
                try:
                    # Validate it's a valid IPv4 address
                    socket.inet_aton(ip)
                    private_ips.append(ip)
                except (socket.error, OSError):
                    # Skip invalid IPs
                    pass
    except (socket.error, OSError) as e:
        # If hostname resolution fails, try alternative methods
        pass
    
    # Method 2: Try connecting to external address to get local IP
    # This gets the IP that would be used for outbound connections
    if not private_ips:
        test_socket = None
        try:
            # Connect to a remote address (doesn't actually connect, just determines route)
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Use a non-routable address to avoid actual connection
            test_socket.connect(("8.8.8.8", 80))
            local_ip = test_socket.getsockname()[0]
            if local_ip and not local_ip.startswith('127.'):
                private_ips.append(local_ip)
        except (socket.error, OSError):
            # Connection failed - ignore and continue
            pass
        finally:
            # Ensure socket is closed even if an error occurs
            if test_socket:
                try:
                    test_socket.close()
                except Exception:
                    pass
    
    # Cache the result
    _IP_CACHE['private'] = private_ips
    _IP_CACHE['cache_time'] = time.time()
    
    return private_ips


def get_public_ip_address(timeout=5):
    """
    Get the public IP address (as seen by remote servers).
    Queries external services with timeout and graceful failure handling.
    
    Args:
        timeout: Timeout in seconds for the request (default: 5)
    
    Returns:
        str or None: Public IP address string, or None if detection fails
    
    COMPATIBILITY: Python 3.4.4 and Windows XP compatible
    """
    global _IP_CACHE
    
    # Check cache first
    if _IP_CACHE['public'] is not None and _IP_CACHE['cache_time'] is not None:
        if time.time() - _IP_CACHE['cache_time'] < _CACHE_TTL:
            return _IP_CACHE['public']
    
    public_ip = None
    
    # List of public IP services to try (in order)
    ip_services = [
        ('http://api.ipify.org?format=text', False),  # HTTP (no SSL)
        ('http://icanhazip.com', False),  # HTTP fallback
        ('https://api.ipify.org?format=text', True),  # HTTPS if available
    ]
    
    for service_url, use_ssl in ip_services:
        try:
            # Python 3.4.4 compatible urllib usage
            from urllib.request import urlopen, Request
            from urllib.error import URLError
            
            # Create request with timeout
            req = Request(service_url)
            req.add_header('User-Agent', 'MediLink/1.0')
            
            # Use socket timeout for Python 3.4.4 compatibility
            if use_ssl:
                # For HTTPS, may need SSL context (but skip if not available)
                try:
                    import ssl
                    # Create unverified context for XP compatibility
                    context = ssl._create_unverified_context()
                    response = urlopen(req, timeout=timeout, context=context)
                except (AttributeError, ImportError, URLError):
                    # SSL not available or failed, skip this service
                    continue
            else:
                # HTTP request - simpler
                response = urlopen(req, timeout=timeout)
            
            # Read response (should be just the IP address as text)
            ip_text = response.read().decode('utf-8', errors='ignore').strip()
            response.close()
            
            # Validate it looks like an IP address
            if ip_text and len(ip_text) < 16:  # IPv4 addresses are max 15 chars
                try:
                    # Validate format
                    socket.inet_aton(ip_text)
                    public_ip = ip_text
                    break  # Success, exit loop
                except (socket.error, OSError):
                    # Invalid IP format, try next service
                    continue
                    
        except (URLError, socket.timeout, socket.error, OSError):
            # Network error, timeout, or connection failure - try next service
            continue
        except Exception:
            # Any other error - try next service
            continue
    
    # Cache the result (even if None)
    _IP_CACHE['public'] = public_ip
    if _IP_CACHE['cache_time'] is None:
        _IP_CACHE['cache_time'] = time.time()
    
    return public_ip


def validate_ip_against_allowed(ip_address, allowed_ips):
    """
    Check if an IP address matches any in the allowed list.
    Uses exact string matching.
    
    Args:
        ip_address: IP address string to check (or None)
        allowed_ips: List of allowed IP address strings
    
    Returns:
        bool: True if IP matches any allowed IP, False otherwise
    """
    if not ip_address or not allowed_ips:
        return False
    
    # Exact string match (case-insensitive for consistency)
    ip_address = ip_address.strip().lower()
    allowed_ips_lower = [ip.strip().lower() for ip in allowed_ips if ip]
    
    return ip_address in allowed_ips_lower


def clear_ip_cache():
    """
    Clear the IP address cache.
    Useful for testing or forcing fresh IP detection.
    """
    global _IP_CACHE
    _IP_CACHE = {
        'private': None,
        'public': None,
        'cache_time': None
    }

