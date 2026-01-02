# =============================================================================
# Docstring
# =============================================================================

"""
Process Run Command
===================

Execute command in subprocess.

Examples
--------
>>> from rite.system.process import process_run
>>> code, out, err = process_run(["ls", "-la"], Path.cwd())

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


def process_run(
    cmd: list[str], cwd: Path | str | None = None, check: bool = False
) -> tuple[int, str, str]:
    """
    Run command in subprocess and return result.

    Args:
        cmd: Command as list of strings.
        cwd: Working directory. Defaults to current.
        check: Raise exception on non-zero exit.

    Returns:
        Tuple of (return_code, stdout, stderr).

    Raises:
        CalledProcessError: If check=True and command fails.

    Examples:
        >>> process_run(["echo", "hello"])
        (0, 'hello', '')
        >>> process_run(["ls"], Path("/tmp"))
        (0, '...', '')

    Notes:
        Uses Popen for subprocess execution.
        Output is text mode with UTF-8 encoding.
    """
    work_dir = str(cwd) if cwd else None

    p = subprocess.Popen(
        cmd,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    out, err = p.communicate()

    if check and p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, out, err)

    return p.returncode, out.strip(), err.strip()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["process_run"]
