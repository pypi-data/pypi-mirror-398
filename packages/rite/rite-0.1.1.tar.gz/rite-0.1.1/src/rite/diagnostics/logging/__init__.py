# =============================================================================
# Docstring
# =============================================================================

"""
Logging Module
==============

Logging utilities with file, console, structured, and contextual output.

This submodule provides various logging configurations for different
use cases: file logging with rotation, console logging with colors,
structured JSON logging, and context-aware logging.

Examples
--------
>>> from rite.diagnostics.logging import (
...     logging_to_file,
...     logging_to_console,
...     logging_structured
... )
>>> file_logger = logging_to_file("app", "app.log")
>>> console_logger = logging_to_console("debug", colorize=True)
>>> struct_logger = logging_structured("api")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .logging_structured import logging_structured
from .logging_to_console import logging_to_console
from .logging_to_file import logging_to_file
from .logging_with_context import logging_with_context

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "logging_to_file",
    "logging_to_console",
    "logging_structured",
    "logging_with_context",
]
