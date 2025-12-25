"""
leiden_engine.py

This module provides the class LeidenEngine including:
- run: main entry point
- _move_nodes: greedy node movement
- _refine and _merge_within_subset: splitting communities
and the function
- merge_communities: optional merger of small communities
- macro_merge_partition: optional macro-level community merging
"""

from __future__ import annotations

import logging
import math
import random
from collections import deque
from collections.abc import Set
from copy import copy as _shallow_copy
from copy import deepcopy
from typing import Dict, Optional, TypeVar, Union

import networkx as nx
import numpy as np
from networkx import Graph

# Reproducibility & logging helpers (placed under utils/)
from ..utils.repro import coerce_random_state, configure_logging
from .partitions_functions import (
    GraphKeys as Keys,
)
from .partitions_functions import (
    Partition,
    cut_size_singleton,
    ensure_edge_weights,
    node_weight_total,
)
from .scoring import CommunityQuality

T = TypeVar("T")
logger = logging.getLogger("domino.leiden")


class LeidenEngine:
    """
    Static driver for Leiden-style refinement with a pluggable quality function.

    Notes on determinism:
    ---------------------
    The only stochastic operations inside Leiden are:
        (i)   the shuffle of the node visitation order in `_move_nodes`
        (ii)  the soft-probabilistic target choice in `_merge_within_subset`
    We replace uses of the *global* RNG with a local, user-provided
    `random.Random` instance to ensure runs are reproducible when a seed is set.
    """

    @staticmethod
    def run(
        G: Graph,
        quality: CommunityQuality[T],
        initial: Optional[Partition[T]] = None,
        theta: float = 0.0,
        gamma: float = 0.0,
        weight: Optional[str] = None,
        random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
        verbose: int | bool = False,
    ) -> Partition[T]:
        """
        Execute one full Leiden optimization with refinement and aggregation
        until the partition stabilizes.

        Parameters
        ----------
        G : Graph
            Input (possibly weighted) graph.
        quality : CommunityQuality
            Objective to maximize. Higher is better.
        initial : Partition | None
            Initial partition; if None, uses singletons.
        theta : float
            Softness parameter controlling the stochastic choice among multiple
            non-worse merge targets during the refinement step.

            Important: theta does NOT allow moves that decrease the quality function.
            It only affects tie-breaking between candidate targets with Δquality >= 0.
            As theta → 0, the selection becomes deterministic (argmax over Δquality).
            Larger values of theta increase exploration among similarly improving moves,
            while preserving monotonic improvement of the objective.
        gamma : float
            Cut-resolution parameter used for selecting eligible merge targets.
        weight : str | None
            Edge attribute name carrying weights; if None, defaults to 1.
        random_state : int | np.random.Generator | random.Random | None
            Seed or RNG to make randomized steps reproducible. If None,
            the package utility resolves a deterministic default as documented.
        verbose : bool | int
            If truthy, configure package logger to INFO; else WARNING.

        Returns
        -------
        Partition
            A flattened partition of the original graph.
        """
        # Configure package-wide logging level once per call.
        configure_logging(verbose, logger_name="domino")

        # Resolve numpy/python RNGs. We use only the Python RNG in this module,
        # but we keep the numpy RNG here for API symmetry and future use.
        np_rng, py_rng = coerce_random_state(random_state)

        # Ensure every edge has a numeric weight under a standard key.
        G = ensure_edge_weights(G, weight)

        # Initialize the working partition.
        if initial is not None:
            part = Partition.from_partition(G, initial, Keys.WEIGHT)
        else:
            part = Partition.singleton_partition(G, Keys.WEIGHT)

        # Main outer loop: move nodes → refine within communities → aggregate.
        prev = None
        while True:
            # Greedy node movement on the current graph, with deterministic shuffle.
            part = LeidenEngine._move_nodes(G, part, quality, py_rng)

            # Stopping condition: no change or reached trivial partition.
            if len(part) == G.order() or part == prev:
                return part.flatten()

            prev = part

            # Refinement within communities, then build a coarsened graph.
            refined = LeidenEngine._refine(G, part, quality, theta, gamma, py_rng)
            G = refined.aggregate_graph()

            # Lift previous partition to the aggregated graph.
            mapping: Dict[int, Set[T]] = {cid: set() for cid in range(len(part))}
            for supernode, data in G.nodes(data=Keys.NODES):
                orig = next(iter(data))
                cid = part._node2block[orig]
                mapping[cid].add(supernode)
            new_blocks = list(mapping.values())
            part = Partition.from_partition(G, new_blocks, Keys.WEIGHT)

    @staticmethod
    def _move_nodes(G, part, quality, py_rng: random.Random):
        """
        Greedy local moves: visit nodes in a randomized (but seeded) order and
        move each to the best adjacent community (including the option of a new
        singleton community) if it improves the quality score.

        Parameters
        ----------
        G : Graph
            Current graph at this aggregation level.
        part : Partition
            Mutable partition on G.
        quality : CommunityQuality
            Objective to evaluate moves.
        py_rng : random.Random
            Deterministic RNG for shuffling the visitation order.
        """
        order = list(G.nodes)
        # Deterministic shuffle using the provided RNG rather than the global one.
        py_rng.shuffle(order)

        queue = deque(order)
        in_q = {v: True for v in order}

        if hasattr(quality, "prepare"):
            quality.prepare(G, part)

        while queue:
            v = queue.popleft()
            in_q[v] = False

            # Candidate targets: communities adjacent to v (by block id) plus "new" (empty set).
            cand_ids = part.adjacent_block_ids(v)
            candidates = [part._blocks[cid] for cid in cand_ids] + [set()]
            best_comm = None
            best_delta = 0.0

            for C in candidates:
                if hasattr(quality, "delta"):
                    dq = quality.delta(part, v, C)
                else:
                    # Fallback: compute score difference by copying and moving.
                    old_score = quality(part)
                    P_new = _shallow_copy(part)
                    P_new.move_node(v, C)
                    dq = quality(P_new) - old_score
                if dq > best_delta:
                    best_delta = dq
                    best_comm = C

            if best_comm is not None and best_delta > 0:
                if hasattr(quality, "apply_move"):
                    quality.apply_move(part, v, best_comm)
                part.move_node(v, best_comm)

                # Re-queue neighbors whose best target may have changed.
                for u in G[v]:
                    if u in best_comm:
                        continue
                    if not in_q.get(u, False):
                        queue.append(u)
                        in_q[u] = True

        return part

    @staticmethod
    def _refine(
        G: Graph,
        part: Partition[T],
        quality: CommunityQuality[T],
        theta: float,
        gamma: float,
        py_rng: random.Random,
    ) -> Partition[T]:
        """
        Refine each community independently by allowing a node to merge with
        other communities within the same subset when such a merge is acceptable
        (cut constraint) and beneficial according to the quality function.

        Parameters
        ----------
        G : Graph
            Current (possibly aggregated) graph.
        part : Partition
            Current partition on G.
        quality : CommunityQuality
            Objective to maximize.
        theta : float
            Stochastic tie-breaking parameter used only in the refinement step.

            The refinement procedure never accepts quality-decreasing moves:
            theta only affects the selection among candidate targets with Δquality >= 0.
            As theta → 0 the selection becomes deterministic (argmax).
        gamma : float
            Cut-resolution threshold; if zero, the cut constraint is disabled.
        py_rng : random.Random
            RNG used for the soft selection step (see `_merge_within_subset`).
        """
        if hasattr(quality, "prepare"):
            quality.prepare(G, part)

        refined = Partition.singleton_partition(G, Keys.WEIGHT)
        for block in part:
            refined = LeidenEngine._merge_within_subset(
                G, refined, quality, theta, gamma, block, py_rng
            )
        return refined

    @staticmethod
    def _merge_within_subset(
        G: Graph,
        part: Partition[T],
        quality: CommunityQuality[T],
        theta: float,
        gamma: float,
        subset: Set[T],
        py_rng: random.Random,
    ) -> Partition[T]:
        """
        Within a given subset (a community of the previous level), consider moving
        eligible singletons into neighboring communities of the subset. The choice
        among non-worse targets is made stochastically with weights derived from
        the Δquality values, controlled by `theta`.

        Parameters
        ----------
        G : Graph
            Current graph.
        part : Partition
            Partition to modify (on G).
        quality : CommunityQuality
            Objective to evaluate moves.
        theta : float
            Softness parameter for the softmax-based selection among candidate
            targets with non-negative improvement (Δquality >= 0).

            Important: theta does NOT enable downhill moves. It only randomizes
            tie-breaking among non-worse targets. As theta → 0, the selection
            becomes deterministic (argmax over Δquality).
        gamma : float
            Cut-resolution parameter; nodes/targets not satisfying the cut
            constraint are filtered out when gamma>0.
        subset : set
            The subset (community) in which we attempt merges.
        py_rng : random.Random
            RNG for the weighted random choice of targets.
        """
        subset_set = set(subset)
        total_size = node_weight_total(G, subset_set)
        use_cut = gamma > 0.0

        eligible = []
        for v in subset_set:
            # Only consider nodes that are singletons in the current partition.
            if len(part.community_of(v)) != 1:
                continue
            if not use_cut:
                eligible.append(v)
            else:
                bndry = cut_size_singleton(G, v, subset_set - {v}, weight=Keys.WEIGHT)
                if bndry >= gamma * node_weight_total(G, v) * (
                    total_size - node_weight_total(G, v)
                ):
                    eligible.append(v)

        if not eligible:
            return part

        for v in eligible:
            # Candidate target communities are those adjacent to v and contained in the subset.
            cand_sets = []
            for C in part.adjacent_communities(v):
                if len(C) == 1 and v in C:
                    continue
                if C.issubset(subset_set):
                    cand_sets.append(C)

            if not cand_sets:
                continue

            if use_cut:
                ok_targets = []
                for C in cand_sets:
                    cut_CS = nx.cut_size(G, C, subset_set - set(C), weight=Keys.WEIGHT)
                    if cut_CS >= gamma * node_weight_total(G, C) * (
                        total_size - node_weight_total(G, C)
                    ):
                        ok_targets.append(C)
                cand_sets = ok_targets
                if not cand_sets:
                    continue

            # Evaluate Δquality for all candidate targets and keep non-worse ones.
            improvements = [(C, quality.delta(part, v, C)) for C in cand_sets]
            improvements = [(C, dq) for (C, dq) in improvements if dq >= 0.0]
            if not improvements:
                continue

            # Softmax over (non-negative) Δq with numerical stabilization by max subtraction.
            max_dq = max(dq for (_, dq) in improvements)
            weights = []
            for _, dq in improvements:
                x = (dq - max_dq) / max(theta, 1e-12)
                # Guard the exp to avoid over/underflow.
                x = 700.0 if x > 700.0 else (-700.0 if x < -700.0 else x)
                weights.append(math.e**x)

            # Deterministic selection using the provided RNG:
            # If all weights vanish, fall back to strict argmax.
            chosen = (
                max(improvements, key=lambda t: t[1])[0]
                if sum(weights) <= 0.0
                else py_rng.choices(
                    [c for (c, _) in improvements], weights=weights, k=1
                )[0]
            )

            if hasattr(quality, "apply_move"):
                quality.apply_move(part, v, chosen)
            part.move_node(v, chosen)

        return part


def merge_communities(
    part: Partition[T], comm_idx_a: int, comm_idx_b: int
) -> Partition[T]:
    """
    Create a new partition by merging community `comm_idx_b` into `comm_idx_a`.
    This helper is deterministic (no RNG involved).
    """
    new_part = deepcopy(part)
    set_a = new_part._blocks[comm_idx_a]
    set_b = new_part._blocks[comm_idx_b]
    for node in list(set_b):
        new_part.move_node(node, set_a)
    return new_part


def macro_merge_partition(
    part: Partition[T], quality_fn: CommunityQuality[T], max_checks: int = 1000
) -> Partition[T]:
    """
    Greedy macro-level merging across communities: try pairs (i, j) in order
    and accept the first merge that strictly improves the quality. Repeat
    until no improvement or `max_checks` scored candidates are examined.

    Determinism note:
        The traversal order is fixed (nested for-loops over indices), so
        behavior is deterministic by construction.
    """
    current = part
    best_score = quality_fn(current)
    checks = 0
    improved = True

    while improved and checks < max_checks:
        improved = False
        num_comms = len(current._blocks)
        for i in range(num_comms):
            for j in range(i + 1, num_comms):
                if checks >= max_checks:
                    break
                candidate = merge_communities(current, i, j)
                score = quality_fn(candidate)
                checks += 1
                if score > best_score:
                    current = candidate
                    best_score = score
                    improved = True
                    break
            if improved:
                break
    return current
