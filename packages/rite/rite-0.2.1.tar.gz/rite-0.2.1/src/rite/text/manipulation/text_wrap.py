# =============================================================================
# Docstring
# =============================================================================

"""
Text Wrap
=========

Wrap text to specified width.

Examples
--------
>>> from rite.text.manipulation import text_wrap
>>> text_wrap("Hello World", 5)
['Hello', 'World']

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import textwrap

# =============================================================================
# Functions
# =============================================================================


def text_wrap(text: str, width: int = 70) -> list[str]:
    """
    Wrap text to specified width.

    Args:
        text: Text to wrap.
        width: Maximum line width.

    Returns:
        List of wrapped lines.

    Examples:
        >>> text_wrap("Hello World", 5)
        ['Hello', 'World']
        >>> text_wrap("A long sentence", 10)
        ['A long', 'sentence']

    Notes:
        Uses textwrap.wrap() from stdlib.
    """
    return textwrap.wrap(text, width=width)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_wrap"]
