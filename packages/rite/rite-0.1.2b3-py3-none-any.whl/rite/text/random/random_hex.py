# =============================================================================
# Docstring
# =============================================================================

"""
Random Hexadecimal Generator
=============================

Generate random hexadecimal strings.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import secrets

# =============================================================================
# Functions
# =============================================================================


def random_hex(length: int = 16, uppercase: bool = False) -> str:
    """
    Generate a random hexadecimal string.

    Args:
        length: Length of the random hex string
        uppercase: Use uppercase letters for hex digits

    Returns:
        Random hexadecimal string

    Example:
        >>> len(random_hex(10))
        10
    """
    charset = "0123456789ABCDEF" if uppercase else "0123456789abcdef"
    return "".join(secrets.choice(charset) for _ in range(length))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "random_hex",
]
