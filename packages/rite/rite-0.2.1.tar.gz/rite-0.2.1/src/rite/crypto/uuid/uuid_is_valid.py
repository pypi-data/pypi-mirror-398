# =============================================================================
# Docstring
# =============================================================================

"""
UUID Validation
===============

Validate UUID strings.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from uuid import UUID

# =============================================================================
# Functions
# =============================================================================


def is_valid_uuid(
    uuid_to_test: str,
    version: int = 4,
) -> bool:
    """
    Check if uuid_to_test is a valid UUID.

    Args:
        uuid_to_test: String to validate as UUID
        version: UUID version to check (1, 2, 3, or 4)

    Returns:
        True if valid UUID, False otherwise

    Example:
        >>> is_valid_uuid('550e8400-e29b-41d4-a716-446655440000')
        True
        >>> is_valid_uuid('invalid')
        False
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "is_valid_uuid",
]
