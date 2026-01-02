# =============================================================================
# Docstring
# =============================================================================

"""
Buffer Collections Module
==========================

Provides various buffer data structures for specialized data storage patterns.

Classes:
--------
- CircularBuffer: Ring buffer with automatic overwriting
- RingBuffer: Alias for CircularBuffer
- BoundedBuffer: Size-limited buffer with overflow protection
- SlidingWindow: Moving window over a data stream

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .bounded_buffer import BoundedBuffer

# Import | Local
from .circular_buffer import CircularBuffer
from .ring_buffer import RingBuffer
from .sliding_window import SlidingWindow

# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "CircularBuffer",
    "RingBuffer",
    "BoundedBuffer",
    "SlidingWindow",
]
