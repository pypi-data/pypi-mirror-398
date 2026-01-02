# =============================================================================
# Docstring
# =============================================================================

"""
Object Pool Pattern
===================

Implementation of the Object Pool design pattern for resource management.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from typing import Any

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Classes
# =============================================================================


class ObjectPool:
    """
    ObjectPool Class
    ================

    A generic object pool for managing reusable objects.

    Parameters
    ----------
    factory : Callable[[], Any]
        Factory function to create new objects.
    max_size : int
        Maximum number of objects in the pool.
    reset_func : Callable[[Any], None] | None
        Optional function to reset objects before reuse.

    """

    def __init__(
        self,
        factory: Callable[[], Any],
        max_size: int = 10,
        reset: Callable[[Any], None] | None = None,
    ) -> None:
        """
        Initialize an object pool.

        Args:
        ----
            factory: Function to create new objects.
            max_size: Maximum pool size.
            reset_func: Optional function to reset objects.

        """
        if max_size < 1:
            raise ValueError("max_size must be at least 1")

        self.factory = factory
        self.max_size = max_size
        self.reset_func = reset
        self._available: list[Any] = []
        self._in_use: set[Any] = set()

    def acquire(self) -> Any:
        """
        Acquire an object from the pool.

        Returns:
        -------
            Any: An object from the pool or newly created.

        """
        if self._available:
            obj = self._available.pop()
        else:
            obj = self.factory()

        self._in_use.add(obj)
        return obj

    def release(self, obj: Any) -> None:
        """
        Release an object back to the pool.

        Args:
        ----
            obj: The object to release.

        Raises:
        ------
            ValueError: If object was not acquired from this pool.

        """
        if obj not in self._in_use:
            raise ValueError("Object was not acquired from this pool")

        self._in_use.remove(obj)

        if len(self._available) < self.max_size:
            if self.reset_func:
                self.reset_func(obj)
            self._available.append(obj)

    def clear(self) -> None:
        """Clear all available objects from the pool."""
        self._available.clear()

    def size(self) -> int:
        """
        Get total number of objects managed by pool.

        Returns:
        -------
            int: Total objects (available + in use).

        """
        return len(self._available) + len(self._in_use)

    def available_count(self) -> int:
        """
        Get number of available objects.

        Returns:
        -------
            int: Number of available objects.

        """
        return len(self._available)

    def in_use_count(self) -> int:
        """
        Get number of objects currently in use.

        Returns:
        -------
            int: Number of in-use objects.

        """
        return len(self._in_use)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ObjectPool(max_size={self.max_size}, "
            f"available={len(self._available)}, "
            f"in_use={len(self._in_use)})"
        )


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "ObjectPool",
]
