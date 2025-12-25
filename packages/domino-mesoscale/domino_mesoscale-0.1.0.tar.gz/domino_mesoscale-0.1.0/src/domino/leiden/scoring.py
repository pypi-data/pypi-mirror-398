"""
scoring.py

Abstract interface for community quality functions.

Implementations must define:
  • __call__(part) -> float       # higher is better

Optionally override (for speed):
  • delta(part, node, target_block) -> float
     # default: copy part, move node, recompute score difference

Optional hooks recognized by the Leiden engine (not required here):
  • prepare(G, part) -> None
      Called at the start of a phase; implementations may precompute caches.
  • apply_move(part, node, target_block) -> None
      Called just before a move is applied; can update internal caches.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Set as SetABC
from copy import copy as shallow_copy
from typing import Generic, TypeVar

from .partitions_functions import Partition

# Module logger (configure level/handlers at package entry).
logger = logging.getLogger("domino.scoring")

T = TypeVar("T")


class CommunityQuality(ABC, Generic[T]):
    """
    Base class for community quality metrics.

    Required:
      - __call__(part): return a *scalar* quality score (higher is better).

    Optional (but recommended for performance):
      - delta(part, node, target_block): score change if `node` is moved
        into `target_block`. Positive ⇒ improvement.
        The default implementation is correct but re-evaluates the full score.

    Notes for implementers
    ----------------------
    * Keep __call__ *pure* with respect to `part` (no mutation).
    * If you maintain internal caches, consider supporting the optional hooks
      `prepare(G, part)` and `apply_move(part, node, target_block)`. The
      Leiden engine will call them if present (detected via hasattr).
    * Avoid global state; if you need verbosity, use the module logger.
    """

    @abstractmethod
    def __call__(self, part: Partition[T]) -> float:
        """
        Evaluate the current partition's quality on its graph.

        Parameters
        ----------
        part : Partition
            Partition of nodes to evaluate.

        Returns
        -------
        float
            Quality score. Higher means a better partition under this metric.
        """
        raise NotImplementedError

    def delta(self, part: Partition[T], node: T, target_block: SetABC[T]) -> float:
        """
        Score delta from moving `node` into `target_block`.

        Default implementation is correct but slower:
        it copies the partition, applies the move, and diffs scores.

        Implementations can (and should) override for O(1)/O(deg) deltas.

        Parameters
        ----------
        part : Partition
            Current partition (not mutated).
        node : hashable
            Node to move.
        target_block : set
            Community (set of nodes) to move `node` into. Empty set means
            "create a new community".

        Returns
        -------
        float
            Δscore = quality(after) − quality(before).
        """
        # Full recomputation baseline (kept for correctness and simplicity).
        before = self(part)

        # Shallow copy is supported by Partition.__copy__ and duplicates the
        # internal sets/indices while sharing the graph reference (cheap).
        after_part = shallow_copy(part)
        after_part.move_node(node, target_block)

        after = self(after_part)
        delta_val = after - before

        # Emit debug diagnostics if the logger is set to DEBUG by the caller.
        logger.debug(
            "delta: node=%r, target_size=%d, before=%.6f, after=%.6f, Δ=%.6f",
            node,
            len(target_block),
            before,
            after,
            delta_val,
        )
        return delta_val
