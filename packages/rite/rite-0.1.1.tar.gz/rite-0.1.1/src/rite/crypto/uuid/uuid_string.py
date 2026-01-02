# =============================================================================
# Docstring
# =============================================================================

"""
UUID String Generation
=====================

Generate random UUIDs as formatted strings.

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


def uuid_string() -> str:
    """
    Generate a random UUID and return it as a string in standard form.

    Returns:
        UUID as a string in standard form (with hyphens)

    Example:
        >>> '-' in uuid_string()
        True
        >>> len(uuid_string())
        36
    """
    return str(uuid.uuid4())


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "uuid_string",
]
