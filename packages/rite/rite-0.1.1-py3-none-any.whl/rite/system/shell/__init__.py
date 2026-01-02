# =============================================================================
# Docstring
# =============================================================================

"""
Shell Module
============

Shell command utilities.

This submodule provides utilities for safely handling shell commands,
arguments, and escaping.

Examples
--------
>>> from rite.system.shell import shell_escape, shell_split
>>> shell_escape("file name.txt")
"'file name.txt'"
>>> shell_split("ls -la '/tmp/file.txt'")
['ls', '-la', '/tmp/file.txt']

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .shell_escape import shell_escape
from .shell_join import shell_join
from .shell_split import shell_split

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "shell_escape",
    "shell_split",
    "shell_join",
]
