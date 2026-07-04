"""URL validation. Protects the provider layer from SSRF-style abuse:
a pasted URL must be http(s) and must NOT resolve to a private/loopback host
before we ever fetch it.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}


def is_valid_url(url: str) -> bool:
    """Basic structural check (scheme + host). Does not touch the network."""
    if not url:
        return False
    try:
        parts = urlparse(url.strip())
    except ValueError:
        return False
    return parts.scheme in ALLOWED_SCHEMES and bool(parts.hostname)


def is_safe_to_fetch(url: str) -> bool:
    """Structural check PLUS DNS resolution; rejects private/internal targets.

    Call this before any outbound request in the providers layer.
    """
    if not is_valid_url(url):
        return False
    host = urlparse(url.strip()).hostname
    assert host is not None
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for *_, sockaddr in infos:
        try:
            ip = ipaddress.ip_address(sockaddr[0])
        except ValueError:
            return False
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False
    return True
