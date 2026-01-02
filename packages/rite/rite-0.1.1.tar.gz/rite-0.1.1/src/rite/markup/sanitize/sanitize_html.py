# =============================================================================
# Docstring
# =============================================================================

"""
HTML Sanitizer
==============

Sanitize HTML by removing dangerous elements.

Examples
--------
>>> from rite.markup.sanitize import sanitize_html
>>> sanitize_html("<script>alert('xss')</script><p>Safe</p>")
'<p>Safe</p>'

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


def sanitize_html(html: str, allowed_tags: list[str] | None = None) -> str:
    """
    Sanitize HTML by removing dangerous tags.

    Args:
        html: HTML to sanitize.
        allowed_tags: List of allowed tags (default: p, br, strong, em).

    Returns:
        Sanitized HTML.

    Examples:
        >>> sanitize_html("<p>Safe</p><script>Bad</script>")
        '<p>Safe</p>'
        >>> sanitize_html("<div>Text</div>", ["div"])
        '<div>Text</div>'

    Notes:
        Removes script, iframe, object, embed by default.
        Only allows whitelisted tags.
    """
    if allowed_tags is None:
        allowed_tags = ["p", "br", "strong", "em", "b", "i", "u", "a"]

    # Remove dangerous tags
    dangerous = ["script", "iframe", "object", "embed", "style"]
    result = html
    for tag in dangerous:
        pattern = re.compile(
            rf"<{tag}\b[^>]*>.*?</{tag}>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        result = re.sub(pattern, "", result)

    # Strip all tags except allowed
    if allowed_tags:
        allowed_pattern = "|".join(allowed_tags)
        keep_tags = re.compile(
            rf"</?({allowed_pattern})\b[^>]*>", flags=re.IGNORECASE
        )
        all_tags = re.compile(r"<[^>]+>")

        # Replace disallowed tags with empty string
        def replacer(match: re.Match[str]) -> str:
            if keep_tags.match(match.group(0)):
                return match.group(0)
            return ""

        result = all_tags.sub(replacer, result)

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["sanitize_html"]
