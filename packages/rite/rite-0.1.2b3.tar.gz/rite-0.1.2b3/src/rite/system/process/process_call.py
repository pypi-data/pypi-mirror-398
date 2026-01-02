# =============================================================================
# Docstring
# =============================================================================

"""
Process Call
============

Execute command and wait for completion.

Examples
--------
>>> from rite.system.process import process_call
>>> exit_code = process_call(["ls", "-la"])

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path
import subprocess

# =============================================================================
# Functions
# =============================================================================


def process_call(cmd: list[str], cwd: Path | str | None = None) -> int:
    """
    Execute command and return exit code.

    Args:
        cmd: Command as list of strings.
        cwd: Working directory. Defaults to current.

    Returns:
        Command exit code.

    Examples:
        >>> process_call(["echo", "hello"])
        0
        >>> process_call(["false"])
        1

    Notes:
        Does not capture output.
        Output goes to terminal.
    """
    work_dir = str(cwd) if cwd else None
    result: int = subprocess.call(cmd, cwd=work_dir)
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["process_call"]
