# =============================================================================
# Docstring
# =============================================================================

"""
Command Argument Escaping
=========================

Escape command line arguments for safe shell usage.

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


def get_escaped_command_arg(arg: str) -> str:
    """Escapes a command line argument to make it safe for shell usage.

    Args:
        arg: The argument to escape.

    Returns:
        str: The escaped argument.

    """
    return quote(arg)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "get_escaped_command_arg",
]
