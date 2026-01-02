# =============================================================================
# Docstring
# =============================================================================

"""
Query String Parser
===================

Parse query string to dictionary.

Examples
--------
>>> from rite.net.url import url_parse_query
>>> url_parse_query("a=1&b=2&c=3")
{'a': ['1'], 'b': ['2'], 'c': ['3']}

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import parse_qs

# =============================================================================
# Functions
# =============================================================================


def url_parse_query(query: str) -> dict[str, list[str]]:
    """
    Parse query string to dictionary.

    Args:
        query: Query string (without ?).

    Returns:
        Dictionary with lists of values.

    Examples:
        >>> url_parse_query("key=value")
        {'key': ['value']}
        >>> url_parse_query("a=1&a=2&b=3")
        {'a': ['1', '2'], 'b': ['3']}

    Notes:
        Uses urllib.parse.parse_qs.
        Values are always lists (multiple values supported).
    """
    return parse_qs(query)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["url_parse_query"]
