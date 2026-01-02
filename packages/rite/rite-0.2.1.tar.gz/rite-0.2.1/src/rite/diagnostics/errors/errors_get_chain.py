# =============================================================================
# Docstring
# =============================================================================

"""
Exception Chain
===============

Get exception chain (cause hierarchy).

Examples
--------
>>> from rite.diagnostics.errors import errors_get_chain
>>> try:
...     try:
...         1 / 0
...     except ZeroDivisionError as e:
...         raise ValueError("Wrapped") from e
... except ValueError as e:
...     chain = errors_get_chain(e)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def errors_get_chain(exception: BaseException) -> list[BaseException]:
    """
    Get exception chain (cause hierarchy).

    Args:
        exception: Exception to get chain for.

    Returns:
        List of exceptions from root cause to final exception.

    Examples:
        >>> try:
        ...     try:
        ...         raise ValueError("root")
        ...     except ValueError as e:
        ...         raise KeyError("wrapped") from e
        ... except KeyError as e:
        ...     chain = errors_get_chain(e)
        ...     len(chain)
        2
    """
    chain: list[BaseException] = []
    current: BaseException | None = exception

    while current:
        chain.append(current)
        current = current.__cause__ or current.__context__

    return list(reversed(chain))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["errors_get_chain"]
