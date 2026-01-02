# =============================================================================
# Docstring
# =============================================================================

"""
Port Validator
==============

Validate port number.

Examples
--------
>>> from rite.net.validation import validation_is_port
>>> validation_is_port(8080)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def validation_is_port(port: int) -> bool:
    """
    Validate port number.

    Args:
        port: Port number to validate.

    Returns:
        True if valid port (1-65535).

    Examples:
        >>> validation_is_port(80)
        True
        >>> validation_is_port(8080)
        True
        >>> validation_is_port(0)
        False
        >>> validation_is_port(70000)
        False

    Notes:
        Valid range: 1-65535.
        Well-known ports: 0-1023.
    """
    return 1 <= port <= 65535


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["validation_is_port"]
