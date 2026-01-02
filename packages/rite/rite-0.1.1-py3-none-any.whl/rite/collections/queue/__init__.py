

# =============================================================================
# Docstring
# =============================================================================

"""
Queue Collections Module
=========================

Provides specialized queue implementations.

Classes:
--------
- PriorityQueue: Priority-based queue
- DequeWrapper: Enhanced deque wrapper
- CircularQueue: Circular queue implementation

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

from .circular_queue import CircularQueue
from .deque_wrapper import DequeWrapper

# Import | Local
from .priority_queue import PriorityQueue

# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "PriorityQueue",
    "DequeWrapper",
    "CircularQueue",
]
