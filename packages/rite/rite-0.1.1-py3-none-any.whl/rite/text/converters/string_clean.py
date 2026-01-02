# =============================================================================
# Docstring
# =============================================================================

"""
String Cleaning
===============

Clean and normalize string values.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def string_clean(val: str | None) -> str | None:
    """
    Trim string; treat empty, 'none' and 'null' as None.

    Args:
        val: Input string value

    Returns:
        Cleaned string or None

    Example:
        >>> string_clean("  hello  ")
        'hello'
        >>> string_clean("none")
        None
    """
    if val is None:
        return None
    v = val.strip()
    if v == "" or v.lower() in {"none", "null"}:
        return None
    return v


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "string_clean",
]
