# =============================================================================
# Docstring
# =============================================================================

"""
TTL Cache
=========

Time-To-Live (TTL) cache with automatic expiration.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import time
from typing import Any

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Classes
# =============================================================================


class TTLCache:
    """
    TTLCache Class
    ==============

    A cache with Time-To-Live (TTL) expiration for entries.

    Parameters
    ----------
    default_ttl : float
        Default time-to-live in seconds.
    max_size : int | None
        Optional maximum cache size.

    """

    def __init__(
        self,
        default_ttl: float = 300.0,
        max_size: int | None = None,
    ) -> None:
        """
        Initialize a TTL cache.

        Args:
        ----
            default_ttl: Default expiration time in seconds.
            max_size: Optional maximum cache size.

        """
        if default_ttl <= 0:
            raise ValueError("TTL must be positive")

        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: dict[Any, tuple[Any, float]] = {}

    def get(self, key: Any) -> Any | None:
        """
        Get a value from cache if not expired.

        Args:
        ----
            key: The key to look up.

        Returns:
        -------
            Any | None: The value or None if not found/expired.

        """
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if time.time() > expiry:
            # Expired
            del self._cache[key]
            return None

        return value

    def put(self, key: Any, value: Any, ttl: float | None = None) -> None:
        """
        Add or update a key-value pair with TTL.

        Args:
        ----
            key: The key to store.
            value: The value to store.
            ttl: Optional TTL in seconds (uses default if not provided).

        """
        # Clean expired entries if at max size
        if self.max_size and len(self._cache) >= self.max_size:
            self._clean_expired()
            if len(self._cache) >= self.max_size:
                # Still at max, remove oldest
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._cache[key] = (value, expiry)

    def delete(self, key: Any) -> bool:
        """
        Delete a key from cache.

        Args:
        ----
            key: The key to delete.

        Returns:
        -------
            bool: True if key was deleted, False if not found.

        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all items from cache."""
        self._cache.clear()

    def _clean_expired(self) -> None:
        """Remove all expired entries."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        for key in expired_keys:
            del self._cache[key]

    def get_ttl(self, key: Any) -> float | None:
        """
        Get remaining TTL for a key.

        Args:
        ----
            key: The key to check.

        Returns:
        -------
            float | None: Remaining seconds or None if not found/expired.

        """
        if key not in self._cache:
            return None

        _, expiry = self._cache[key]
        remaining = expiry - time.time()
        if remaining <= 0:
            del self._cache[key]
            return None

        return remaining

    def __len__(self) -> int:
        """Return number of items in cache (including expired)."""
        return len(self._cache)

    def __contains__(self, key: Any) -> bool:
        """Check if non-expired key is in cache."""
        return self.get(key) is not None

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"TTLCache(default_ttl={self.default_ttl}, "
            f"size={len(self._cache)})"
        )


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "TTLCache",
]
