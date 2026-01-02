# =============================================================================
# Docstring
# =============================================================================

"""
Add Slug Suffix Function
=========================

Add a suffix to a slug.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def add_slug_suffix(slug: str, suffix: str, delimiter: str = "-") -> str:
    """
    Add a suffix to a slug.

    Args:
        slug: The original slug.
        suffix: The suffix to add.
        delimiter: The delimiter used in the slug (default: "-").

    Returns:
        The slug with the suffix added.

    Example:
        >>> add_slug_suffix("hello", "world")
        'hello-world'
        >>> add_slug_suffix("hello", "world", delimiter="_")
        'hello_world'
    """
    return f"{slug}{delimiter}{suffix}" if suffix else slug


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "add_slug_suffix",
]
