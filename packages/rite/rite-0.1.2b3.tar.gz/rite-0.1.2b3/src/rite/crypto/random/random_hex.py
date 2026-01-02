# =============================================================================
# Docstring
# =============================================================================

"""
Random Hex String Generation
=============================

Generate cryptographically secure random hex strings.

Examples
--------
>>> from rite.crypto.random import random_hex
>>> len(random_hex(16))
32
>>> len(random_hex(32))
64

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


def random_hex(nbytes: int = 32) -> str:
    """
    Generate cryptographically secure random hex string.

    Args:
        nbytes: Number of random bytes (output is 2x this length).

    Returns:
        Random hexadecimal string.

    Examples:
        >>> len(random_hex())
        64
        >>> len(random_hex(16))
        32
        >>> all(c in '0123456789abcdef' for c in random_hex(8))
        True
    """
    return secrets.token_hex(nbytes)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["random_hex"]
