# =============================================================================
# Docstring
# =============================================================================

"""
Shell Join
==========

Join command arguments into shell string.

Examples
--------
>>> from rite.system.shell import shell_join
>>> shell_join(["ls", "-la", "file name.txt"])
"ls -la 'file name.txt'"

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from shlex import join

# =============================================================================
# Functions
# =============================================================================


def shell_join(args: list[str]) -> str:
    """
    Join command arguments into shell string.

    Args:
        args: List of command arguments.

    Returns:
        Shell command string.

    Examples:
        >>> shell_join(["ls", "-la"])
        'ls -la'
        >>> shell_join(["echo", "hello world"])
        "echo 'hello world'"

    Notes:
        Uses shlex.join for proper escaping.
        Python 3.8+ required for shlex.join.
    """
    return join(args)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["shell_join"]
