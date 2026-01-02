# =============================================================================
# Docstring
# =============================================================================

"""
Random String Generator
=======================

Generate secure random strings.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import secrets
import string

# =============================================================================
# Functions
# =============================================================================


def random_string(
    length: int = 16,
    charset: str = string.ascii_letters + string.digits,
) -> str:
    """
    Generate a secure random string.

    Args:
        length: Length of the random string
        charset: Character set to use for generation

    Returns:
        Secure random string

    Example:
        >>> len(random_string(20))
        20
    """
    return "".join(secrets.choice(charset) for _ in range(length))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "random_string",
]
