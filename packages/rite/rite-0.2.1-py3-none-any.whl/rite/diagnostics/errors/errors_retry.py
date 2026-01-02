# =============================================================================
# Docstring
# =============================================================================

"""
Retry Decorator
===============

Decorator to retry function calls on failure.

Examples
--------
>>> from rite.diagnostics.errors import errors_retry
>>> @errors_retry(max_attempts=3, delay=1.0)
... def unstable_function():
...     pass

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import wraps
import time
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def errors_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry function on failure.

    Args:
        max_attempts: Maximum retry attempts.
        delay: Initial delay between retries (seconds).
        backoff: Multiplier for delay on each retry.
        exceptions: Tuple of exceptions to catch.

    Returns:
        Decorated function with retry logic.

    Examples:
        >>> @errors_retry(max_attempts=3)
        ... def flaky_api_call():
        ...     pass
        >>> @errors_retry(max_attempts=5, delay=0.5, backoff=1.5)
        ... def database_query():
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    continue

            # All attempts failed
            raise last_exception  # type: ignore

        return wrapper

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["errors_retry"]
