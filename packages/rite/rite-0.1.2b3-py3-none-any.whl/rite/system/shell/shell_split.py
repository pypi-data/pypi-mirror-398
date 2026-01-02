# =============================================================================
# Docstring
# =============================================================================

"""
Shell Split
===========

Split shell command string.

Examples
--------
>>> from rite.system.shell import shell_split
>>> shell_split("ls -la '/tmp/file name.txt'")
['ls', '-la', '/tmp/file name.txt']

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from shlex import split

# =============================================================================
# Functions
# =============================================================================


def shell_split(cmd: str) -> list[str]:
    """
    Split shell command string into arguments.

    Args:
        cmd: Command string to split.

    Returns:
        List of command arguments.

    Examples:
        >>> shell_split("ls -la")
        ['ls', '-la']
        >>> shell_split("echo 'hello world'")
        ['echo', 'hello world']

    Notes:
        Uses shlex.split for proper parsing.
        Handles quoted arguments correctly.
    """
    return split(cmd)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["shell_split"]
