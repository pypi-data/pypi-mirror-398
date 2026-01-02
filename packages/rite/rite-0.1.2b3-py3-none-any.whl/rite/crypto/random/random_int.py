# =============================================================================
# Docstring
# =============================================================================

"""
Random Integer Generation
=========================

Generate cryptographically secure random integers.

Examples
--------
>>> from rite.crypto.random import random_int
>>> 0 <= random_int(0, 100) <= 100
True
>>> random_int(1, 6) in range(1, 7)
True

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


def random_int(a: int, b: int) -> int:
    """
    Generate cryptographically secure random integer in range [a, b].

    Args:
        a: Lower bound (inclusive).
        b: Upper bound (inclusive).

    Returns:
        Random integer between a and b (inclusive).

    Examples:
        >>> n = random_int(1, 10)
        >>> 1 <= n <= 10
        True
        >>> random_int(0, 0)
        0
        >>> n = random_int(100, 200)
        >>> 100 <= n <= 200
        True
    """
    return secrets.randbelow(b - a + 1) + a


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["random_int"]
