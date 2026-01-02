# =============================================================================
# Docstring
# =============================================================================

"""
HTML Tag Stripper
=================

Strip specific HTML tags.

Examples
--------
>>> from rite.markup.html import html_strip_tags
>>> html_strip_tags("<p>Keep</p><script>Remove</script>", ["script"])
'<p>Keep</p>'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re

# =============================================================================
# Functions
# =============================================================================


def html_strip_tags(html: str, tags: list[str]) -> str:
    """
    Strip specific HTML tags and their content.

    Args:
        html: HTML string.
        tags: List of tag names to strip.

    Returns:
        HTML with specified tags removed.

    Examples:
        >>> html_strip_tags("<div>Keep</div><style>Remove</style>", ["style"])
        '<div>Keep</div>'
        >>> html_strip_tags(
        ...     "<p>Text</p><script>alert()</script>",
        ...     ["script", "style"]
        ... )
        '<p>Text</p>'

    Notes:
        Removes both opening and closing tags plus content.
        Case-insensitive tag matching.
    """
    result = html
    for tag in tags:
        pattern = re.compile(
            rf"<{tag}\b[^>]*>.*?</{tag}>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        result = re.sub(pattern, "", result)
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["html_strip_tags"]
