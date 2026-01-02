# =============================================================================
# Docstring
# =============================================================================

"""
Slugify Function
================

Generate URL-friendly slugs from text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re
import unicodedata

# =============================================================================
# Functions
# =============================================================================


def slugify(
    text: str,
    delimiter: str = "-",
    max_length: int | None = None,
    lowercase: bool = True,
    custom_replacements: dict[str, str] | None = None,
) -> str:
    """
    Generate a URL-friendly slug from text.

    Converts the input text to a URL-friendly slug by:
    - Normalizing Unicode characters
    - Applying custom character replacements (optional)
    - Converting to lowercase (optional)
    - Replacing spaces and special characters with delimiters
    - Truncating to maximum length (optional)

    Args:
        text: The text to convert into a slug.
        delimiter: The delimiter to use for separating words (default: "-").
        max_length: Maximum length of the slug. If None, no limit is applied.
        lowercase: Convert slug to lowercase if True (default: True).
        custom_replacements: Dictionary of custom character replacements.

    Returns:
        A URL-friendly slug.

    Example:
        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("Café au Lait", delimiter="_")
        'cafe_au_lait'
        >>> slugify("Hello World", max_length=8)
        'hello-wo'
        >>> slugify("Hello & World", custom_replacements={"&": "and"})
        'hello-and-world'
    """
    # Apply custom replacements if provided
    if custom_replacements:
        for key, value in custom_replacements.items():
            text = text.replace(key, value)

    # Normalize Unicode characters
    slug = unicodedata.normalize("NFKD", text)

    # Convert to ASCII
    if lowercase:
        slug = slug.encode("ascii", "ignore").decode("ascii").lower()
    else:
        slug = slug.encode("ascii", "ignore").decode("ascii")

    # Replace non-word characters with the delimiter
    slug = re.sub(r"[^\w\s]", delimiter, slug)

    # Replace whitespace and multiple delimiters with single delimiter
    slug = re.sub(r"[\s" + re.escape(delimiter) + r"]+", delimiter, slug)

    # Strip leading/trailing delimiters
    slug = slug.strip(delimiter)

    # Truncate to max_length if specified
    if max_length and len(slug) > max_length:
        slug = slug[:max_length].rstrip(delimiter)

    return slug


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "slugify",
]
