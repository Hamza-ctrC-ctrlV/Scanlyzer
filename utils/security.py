"""
Security Utilities

Provides functions to prevent SSRF and validate user inputs.
"""

import ipaddress
import os
import socket
from urllib.parse import urlparse


def is_safe_url(url: str) -> bool:
    """
    Validate that a URL is safe to fetch (prevents SSRF).
    
    Checks:
    1. Scheme is http or https
    2. Hostname resolves to a public, non-reserved IP address.
    
    Returns True if safe, False if potentially malicious or internal.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False

        # Evaluate debug mode once (not per-IP)
        is_debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")

        # Get all IPs for the hostname (handles both IPv4 and IPv6)
        addr_info = socket.getaddrinfo(hostname, None)
        
        for result in addr_info:
            ip_str = result[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            
            # Check if IP is in private/local/reserved ranges
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
                if is_debug and (ip_obj.is_loopback or ip_obj.is_private):
                    continue  # Allow localhost/private IPs in debug mode for testing
                return False
                
        return True
    except socket.gaierror:
        # Hostname doesn't resolve
        return False
    except ValueError:
        # Invalid IP format or parsing error
        return False
    except Exception:
        # Any other error during validation, fail safe
        return False
