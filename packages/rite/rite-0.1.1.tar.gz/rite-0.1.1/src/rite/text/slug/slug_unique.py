# =============================================================================
# Docstring
# =============================================================================

"""
Unique Slug Function
=====================

Generate unique slugs with incremental numbers.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def unique_slug(
    slug: str,
    existing_slugs: set[str] | list[str],
    delimiter: str = "-",
) -> str:
    """
    Generate a unique slug by appending an incremental number.

    If the slug already exists in the set of existing slugs, appends
    an incremental number (starting from 1) until a unique slug is found.

    Args:
        slug: The original slug.
        existing_slugs: A set or list of existing slugs to check against.
        delimiter: The delimiter used in the slug (default: "-").

    Returns:
        A unique slug with an incremental number if needed.

    Example:
        >>> unique_slug("hello-world", {"hello-world"})
        'hello-world-1'
        >>> unique_slug("hello-world", {"hello-world", "hello-world-1"})
        'hello-world-2'
        >>> unique_slug("hello-world", [])
        'hello-world'
    """
    # Convert to set for O(1) lookup
    if isinstance(existing_slugs, list):
        existing_slugs = set(existing_slugs)

    # If slug is unique, return it as is
    if slug not in existing_slugs:
        return slug

    # Generate incremental slug
    counter = 1
    new_slug = f"{slug}{delimiter}{counter}"
    while new_slug in existing_slugs:
        counter += 1
        new_slug = f"{slug}{delimiter}{counter}"

    return new_slug


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "unique_slug",
]
