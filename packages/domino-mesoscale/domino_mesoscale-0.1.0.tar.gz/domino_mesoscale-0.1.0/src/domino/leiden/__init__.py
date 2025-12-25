"""
Leiden Engine, Partition Primitives, and Scoring Interface
==========================================================

Core components used by all pipelines.

Partition model
---------------
Partition(G, blocks, node2block, block_degree_sums, weight_key)
- Mutable partition of graph nodes into communities (sets).
- Key operations:
    move_node(node, target_block)
    aggregate_graph()  # coarsened graph of communities
    flatten()          # lifts a partition on an aggregate graph back to base graph
    community_of(node) -> set
    adjacent_communities(node) -> set[frozenset]
    adjacent_block_ids(node) -> list[int]
- Helpers:
    GraphKeys: standardized graph/node keys:
        WEIGHT, NODES, PARENT_GRAPH, PARENT_PARTITION
    freeze_sets(iterable_of_sets) -> set[frozenset]
    argmax(objective, params) -> (best, value, index)
    cut_size_singleton(G, v, D, weight=None)
    node_weight_total(G, N)  # node or collection
    ensure_edge_weights(G, weight)

Leiden refinement engine
------------------------
LeidenEngine.run(G, quality, *, initial=None, theta=0.0, gamma=0.0, weight=None) -> Partition
- Greedy node moves maximizing a CommunityQuality objective, then refinement on
  each block and aggregation; repeats until stationary; returns a flattened partition.
- Utilities for merges:
    merge_communities(part, i, j) -> Partition   # merge block j into i
    macro_merge_partition(part, quality_fn, max_checks=1000) -> Partition

Quality interface
-----------------
class CommunityQuality:
    __call__(part) -> float                  # higher is better
    delta(part, node, target_block) -> float # optional fast delta; + means improvement

Notes on parameters
-------------------
- theta (float): softmax temperature for stochastic tie-breaking during refinement.
- gamma (float): boundary/cut filter in refinement (gamma=0 disables boundary tests).
"""

from __future__ import annotations

from .leiden_engine import LeidenEngine, macro_merge_partition, merge_communities
from .partitions_functions import (
    GraphKeys,
    Partition,
    argmax,
    cut_size_singleton,
    ensure_edge_weights,
    freeze_sets,
    node_weight_total,
)
from .scoring import CommunityQuality

__all__ = [
    "Partition",
    "GraphKeys",
    "freeze_sets",
    "argmax",
    "node_weight_total",
    "ensure_edge_weights",
    "cut_size_singleton",
    "LeidenEngine",
    "merge_communities",
    "macro_merge_partition",
    "CommunityQuality",
]
