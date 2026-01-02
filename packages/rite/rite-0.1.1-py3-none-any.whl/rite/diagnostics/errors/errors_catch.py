# =============================================================================
# Docstring
# =============================================================================

"""
Exception Context Manager
==========================

Context manager to catch and handle exceptions gracefully.

Examples
--------
>>> from rite.diagnostics.errors import errors_catch
>>> with errors_catch():
...     risky_operation()

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from contextlib import contextmanager
import logging
from typing import Any, Generator

# =============================================================================
# Functions
# =============================================================================


@contextmanager
def errors_catch(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    handler: Callable[[Exception], Any] | None = None,
    reraise: bool = False,
    logger: logging.Logger | None = None,
) -> Generator[None, None, None]:
    """
    Context manager to catch and handle exceptions.

    Args:
        exceptions: Tuple of exceptions to catch.
        handler: Optional handler function called with exception.
        reraise: If True, reraise exception after handling.
        logger: Optional logger to log exceptions.

    Yields:
        None.

    Examples:
        >>> with errors_catch():
        ...     1 / 0
        >>> with errors_catch(handler=lambda e: print(f"Error: {e}")):
        ...     risky_operation()
        >>> with errors_catch((ValueError, KeyError), reraise=True):
        ...     parse_data()
    """
    try:
        yield
    except exceptions as e:
        if logger:
            logger.exception("Exception caught")

        if handler:
            handler(e)

        if reraise:
            raise


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["errors_catch"]
