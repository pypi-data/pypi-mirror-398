# =============================================================================
# Docstring
# =============================================================================

"""
Traceback Formatter
===================

Format exception tracebacks for better readability.

Examples
--------
>>> from rite.diagnostics.errors import errors_format_traceback
>>> try:
...     1 / 0
... except Exception as e:
...     print(errors_format_traceback(e))

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import traceback
import types

# =============================================================================
# Functions
# =============================================================================


def errors_format_traceback(
    exception: BaseException, include_locals: bool = False
) -> str:
    """
    Format exception traceback as string.

    Args:
        exception: Exception to format.
        include_locals: If True, include local variables.

    Returns:
        Formatted traceback string.

    Examples:
        >>> try:
        ...     raise ValueError("test error")
        ... except ValueError as e:
        ...     tb = errors_format_traceback(e)
        ...     "ValueError" in tb
        True
    """
    lines = traceback.format_exception(
        type(exception), exception, exception.__traceback__
    )

    if include_locals and exception.__traceback__:
        lines.append("\nLocal variables:\n")
        tb: types.TracebackType | None = exception.__traceback__
        while tb:
            frame = tb.tb_frame
            lines.append(
                f"\n  File {frame.f_code.co_filename}, "
                f"line {tb.tb_lineno}, in {frame.f_code.co_name}\n"
            )
            for key, value in frame.f_locals.items():
                try:
                    lines.append(f"    {key} = {repr(value)}\n")
                except (ValueError, TypeError, RecursionError):
                    lines.append(f"    {key} = <unrepresentable>\n")
            tb = tb.tb_next

    return "".join(lines)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["errors_format_traceback"]
