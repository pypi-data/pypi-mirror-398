# =============================================================================
# Docstring
# =============================================================================

"""
Shell Escape
============

Escape shell argument.

Examples
--------
>>> from rite.system.shell import shell_escape
>>> shell_escape("file name.txt")
"'file name.txt'"

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from shlex import quote

# =============================================================================
# Functions
# =============================================================================


def shell_escape(arg: str) -> str:
    """
    Escape shell argument for safe usage.

    Args:
        arg: Argument to escape.

    Returns:
        Escaped argument string.

    Examples:
        >>> shell_escape("file name.txt")
        "'file name.txt'"
        >>> shell_escape("simple")
        'simple'

    Notes:
        Uses shlex.quote for proper escaping.
        Safe for shell command construction.
    """
    return quote(arg)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["shell_escape"]
