# =============================================================================
# Docstring
# =============================================================================

"""
Add Slug Prefix Function
=========================

Add a prefix to a slug.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def add_slug_prefix(slug: str, prefix: str, delimiter: str = "-") -> str:
    """
    Add a prefix to a slug.

    Args:
        slug: The original slug.
        prefix: The prefix to add.
        delimiter: The delimiter used in the slug (default: "-").

    Returns:
        The slug with the prefix added.

    Example:
        >>> add_slug_prefix("world", "hello")
        'hello-world'
        >>> add_slug_prefix("world", "hello", delimiter="_")
        'hello_world'
    """
    return f"{prefix}{delimiter}{slug}" if prefix else slug


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "add_slug_prefix",
]
