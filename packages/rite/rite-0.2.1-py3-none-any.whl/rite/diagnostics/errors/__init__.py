# =============================================================================
# Docstring
# =============================================================================

"""
Error Handling Module
=====================

Error handling utilities with retry, catching, and formatting.

This submodule provides utilities for handling errors gracefully:
retry decorators, exception context managers, traceback formatting,
and exception chain analysis.

Examples
--------
>>> from rite.diagnostics.errors import errors_retry, errors_catch
>>> @errors_retry(max_attempts=3)
... def flaky_function():
...     pass
>>> with errors_catch():
...     risky_operation()

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .errors_catch import errors_catch
from .errors_format_traceback import errors_format_traceback
from .errors_get_chain import errors_get_chain
from .errors_retry import errors_retry

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "errors_retry",
    "errors_catch",
    "errors_format_traceback",
    "errors_get_chain",
]
