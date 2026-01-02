# =============================================================================
# Docstring
# =============================================================================

"""
Process Check Output
====================

Execute command and return output.

Examples
--------
>>> from rite.system.process import process_check_output
>>> output = process_check_output(["echo", "hello"])

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


def process_check_output(cmd: list[str], cwd: Path | str | None = None) -> str:
    """
    Execute command and return stdout.

    Args:
        cmd: Command as list of strings.
        cwd: Working directory. Defaults to current.

    Returns:
        Command stdout as string.

    Raises:
        CalledProcessError: If command fails.

    Examples:
        >>> process_check_output(["echo", "hello"])
        'hello'

    Notes:
        Raises exception on non-zero exit.
        Uses check_output for subprocess execution.
    """
    work_dir = str(cwd) if cwd else None

    result: str = subprocess.check_output(
        cmd, cwd=work_dir, text=True, stderr=subprocess.PIPE
    ).strip()

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["process_check_output"]
