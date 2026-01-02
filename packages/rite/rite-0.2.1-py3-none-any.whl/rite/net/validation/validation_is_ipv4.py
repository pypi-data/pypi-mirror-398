# =============================================================================
# Docstring
# =============================================================================

"""
IP Address Validator
====================

Validate IPv4 address format.

Examples
--------
>>> from rite.net.validation import validation_is_ipv4
>>> validation_is_ipv4("192.168.1.1")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import ipaddress

# =============================================================================
# Functions
# =============================================================================


def validation_is_ipv4(ip: str) -> bool:
    """
    Validate IPv4 address format.

    Args:
        ip: IP address string.

    Returns:
        True if valid IPv4 address.

    Examples:
        >>> validation_is_ipv4("192.168.1.1")
        True
        >>> validation_is_ipv4("256.1.1.1")
        False
        >>> validation_is_ipv4("not an ip")
        False

    Notes:
        Uses ipaddress module from standard library.
        Validates format only.
    """
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
        return False


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["validation_is_ipv4"]
