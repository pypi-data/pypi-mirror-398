# =============================================================================
# Docstring
# =============================================================================

"""
Random Bytes Generation
=======================

Generate cryptographically secure random bytes.

Examples
--------
>>> from rite.crypto.random import random_bytes
>>> len(random_bytes(16))
16
>>> len(random_bytes(32))
32

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


def random_bytes(nbytes: int = 32) -> bytes:
    """
    Generate cryptographically secure random bytes.

    Args:
        nbytes: Number of random bytes to generate.

    Returns:
        Random bytes of specified length.

    Examples:
        >>> len(random_bytes())
        32
        >>> len(random_bytes(16))
        16
        >>> isinstance(random_bytes(8), bytes)
        True
    """
    return secrets.token_bytes(nbytes)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["random_bytes"]
