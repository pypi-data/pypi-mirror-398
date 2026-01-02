# =============================================================================
# Docstring
# =============================================================================

"""
UUID Hexadecimal Generation
===========================

Generate random UUIDs as hexadecimal strings.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import uuid

# =============================================================================
# Functions
# =============================================================================


def uuid_hex() -> str:
    """
    Generate a random UUID and return it as a 32-character hexadecimal string.

    Returns:
        UUID as a 32-character hexadecimal string (no hyphens)

    Example:
        >>> len(uuid_hex())
        32
    """
    return uuid.uuid4().hex


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "uuid_hex",
]
