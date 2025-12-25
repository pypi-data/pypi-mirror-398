"""
partitions_functions.py

Provides:
  - GraphKeys: standardized keys for graph metadata
  - Partition: mutable partition with move & aggregate operations
  - freeze_sets: convert iterable of sets into hashable frozensets
  - argmax: argmax over a list with an objective
  - cut_size_singleton: fast cut-size when one side is a single node
  - node_weight_total: total node weight for a node or set
  - ensure_edge_weights: ensure every edge has a weight attribute

Implementation notes
--------------------
* `GraphKeys` centralizes the internal attribute names used to store weights,
  node memberships in aggregate graphs, and back-references to parent graphs.
* `Partition` is a lightweight, mutable partition:
    - O(1) updates to the node→block lookup on moves.
    - Keeps per-community degree sums (under the chosen weight key).
    - Can build an aggregated (coarsened) graph and "flatten" back to the base.
* Helper utilities offer small, focused functionality (hashable set wrappers,
  safe `argmax`, fast cut-size, total node weight, and normalized edge weights).
"""

from __future__ import annotations

import logging
from collections.abc import Collection, Iterable, Iterator, Set
from copy import deepcopy
from typing import Callable, Dict, Generic, Optional, TypeVar, Union, cast

import networkx as nx
from networkx.algorithms.community import community_utils

# Logger for this module (configured at package level by the caller).
logger = logging.getLogger("domino.partitions")

# Generic type variables
T = TypeVar("T")  # node data type (hashable)
T_co = TypeVar("T_co", covariant=True)

# NodeData: either a single node identifier or a (possibly nested) collection of them
NodeData = Union[T, Collection["NodeData[T]"]]


class GraphKeys:
    """
    Standardized keys for storing metadata on graphs and nodes:
      - WEIGHT: edge or node weight attribute
      - NODES: in aggregated graph, holds set of original nodes
      - PARENT_GRAPH / PARENT_PARTITION: backrefs for aggregate graphs

    Using interned/private-like names avoids clashes with user attributes
    and allows internal code to be explicit about where such data lives.
    """

    WEIGHT = "__da_ll_w__"
    NODES = "__da_ll_n__"
    PARENT_GRAPH = "__da_ll_ppg__"
    PARENT_PARTITION = "__da_ll_pp__"


class Partition(Generic[T_co]):
    """
    Represents a partition of a graph's nodes into communities.

    Supports moving nodes between communities, equality testing,
    iteration, and building an aggregate (coarsened) graph.

    The class stores:
      • `G`: reference to the (possibly aggregated) graph.
      • `_blocks`: list of sets of node ids (index ≡ community id).
      • `_node2block`: map node → current community index.
      • `_block_degree_sums`: sum of (weighted) degrees per community.
      • `_weight_key`: the edge attribute used as weight (see GraphKeys.WEIGHT).
    """

    def __init__(
        self,
        G: nx.Graph,
        blocks: list[set[T_co]],
        node2block: Dict[T_co, int],
        block_degree_sums: list[int],
        weight_key: Optional[str] = GraphKeys.WEIGHT,
    ) -> None:
        # Graph reference and total edge weight (cached for possible clients)
        self.G: nx.Graph = G
        self.total_edge_weight = G.size(weight=weight_key)

        # List of community sets; index into this list = community ID
        self._blocks: list[set[T_co]] = blocks
        # Map node -> its community ID (index in _blocks)
        self._node2block: Dict[T_co, int] = node2block
        # Precomputed sum of degrees per community
        self._block_degree_sums: list[int] = block_degree_sums
        # Edge weight attribute name
        self._weight_key: Optional[str] = weight_key

    # ---- Constructors / validators ----
    @classmethod
    def from_partition(
        cls,
        G: nx.Graph,
        P: Collection[Collection[T_co]] | Partition[T_co],
        weight: Optional[str] = None,
    ) -> Partition[T_co]:
        """
        Build a Partition from a collection of communities or another Partition.

        The input is validated to be a true partition of G's nodes; if not,
        an AssertionError is raised.

        Parameters
        ----------
        G : nx.Graph
            Graph whose nodes are to be partitioned.
        P : collection of collections | Partition
            A valid cover/partition of `G`'s nodes (or a Partition on G).
        weight : str | None
            Edge weight attribute to use for degree sums (copied verbatim).

        Returns
        -------
        Partition
            A new Partition attached to G and carrying the provided blocks.
        """
        if not Partition.is_partition(G, P):
            raise AssertionError("Input is not a valid partition of G")

        blocks = [set(c) for c in P]  # type: ignore
        node2block = {v: idx for idx, com in enumerate(blocks) for v in com}
        block_degree_sums = [
            sum(deg for _, deg in G.degree(com, weight=weight)) for com in blocks
        ]
        return cls(G, blocks, node2block, block_degree_sums, weight)

    @classmethod
    def singleton_partition(
        cls, G: nx.Graph, weight: Optional[str] = None
    ) -> Partition[T_co]:
        """
        Create a partition where each node is its own community.

        This is the standard starting point for Leiden-like refinements.

        Parameters
        ----------
        G : nx.Graph
            Graph whose nodes are to be partitioned.
        weight : str | None
            Edge weight attribute for degree accounting.

        Returns
        -------
        Partition
            Partition with one node per block.
        """
        nodes = list(G.nodes)
        blocks = [{v} for v in nodes]
        node2block = {v: i for i, v in enumerate(nodes)}
        block_degree_sums = [G.degree(v, weight=weight) for v in nodes]
        return cls(G, blocks, node2block, block_degree_sums, weight)

    @staticmethod
    def is_partition(
        G: nx.Graph, P: Collection[Collection[T_co]] | Partition[T_co]
    ) -> bool:
        """
        Check if P is a valid partition of G's nodes.

        If `P` is already a Partition bound to `G`, we accept it.
        Otherwise we defer to NetworkX's `community_utils.is_partition`.
        """
        if isinstance(P, Partition) and P.G is G:
            return True
        return community_utils.is_partition(G, P)  # type: ignore

    # ---- Dunder basics ----
    def __copy__(self) -> Partition[T_co]:
        """
        Shallow copy: copies internal sets and lookups.

        Note that sets are duplicated (deepcopied) to avoid aliasing, but the
        graph reference is shared (as intended for a lightweight view).
        """
        cls = self.__class__
        new = cls.__new__(cls)
        new.G = self.G
        new.total_edge_weight = self.total_edge_weight
        new._blocks = deepcopy(self._blocks)
        new._node2block = self._node2block.copy()
        new._block_degree_sums = self._block_degree_sums.copy()
        new._weight_key = self._weight_key
        return new

    def __eq__(self, other: object) -> bool:
        """
        Two partitions are equal if they have the same community sets and weight key.

        Equality ignores ordering *within* communities (they are sets) and
        community ordering (list equality on the list of sets suffices here,
        given how we construct/update partitions).
        """
        if not isinstance(other, Partition):
            return False
        return self._blocks == other._blocks and self._weight_key == other._weight_key

    def __iter__(self) -> Iterator[set[T_co]]:
        return iter(self._blocks)

    def __len__(self) -> int:
        return len(self._blocks)

    # ---- Operations ----
    def move_node(self, node: T_co, target_block: Set[T_co]) -> Partition[T_co]:
        """
        Move `node` into `target_block` (or create a new block if target empty).

        The method updates:
          • the source/target community membership sets,
          • the per-community degree sums, and
          • the node→community lookup (`_node2block`).

        Empty communities are removed to keep the representation compact.

        Returns
        -------
        Partition
            The mutated Partition (fluent API).
        """
        source_idx = self._node2block[node]
        # Identify target index
        if target_block:
            # pick any member of target to find its index
            el = next(iter(target_block))
            target_idx = self._node2block[el]
        else:
            # new community at the end
            target_idx = len(self._blocks)
            self._blocks.append(set())
            self._block_degree_sums.append(0)
        # Move node between blocks
        self._blocks[source_idx].discard(node)
        self._blocks[target_idx].add(node)
        # Update degree sums
        deg_v = self.G.degree(node, weight=self._weight_key)
        self._block_degree_sums[source_idx] -= deg_v
        self._block_degree_sums[target_idx] += deg_v
        # Update node->community map
        self._node2block[node] = target_idx
        # Drop empty community if needed
        if not self._blocks[source_idx]:
            self._blocks.pop(source_idx)
            self._block_degree_sums.pop(source_idx)
            # rebuild lookup since indices shifted
            self._node2block = {
                n: (idx if idx < source_idx else idx - 1)
                for n, idx in self._node2block.items()
            }
        return self

    @staticmethod
    def __find_original_graph(G: nx.Graph) -> nx.Graph:
        """
        Recursively find the original (non-aggregate) graph
        by following the PARENT_GRAPH references.
        """
        if GraphKeys.PARENT_GRAPH in G.graph:
            return Partition.__find_original_graph(G.graph[GraphKeys.PARENT_GRAPH])
        else:
            return G

    def flatten(self) -> Partition[T_co]:
        """
        On an aggregated graph, produce a partition of the original base graph.
        Otherwise returns self.

        The procedure follows the `GraphKeys.PARENT_GRAPH` links to collect
        the original nodes represented by each supernode, preserving the
        block structure. Community memberships are carried back exactly.
        """
        if GraphKeys.PARENT_GRAPH not in self.G.graph:
            return self

        def collect(G, nodes):
            # recursively collect
            if GraphKeys.PARENT_PARTITION not in G.graph:
                return list(nodes)
            parent = G.graph[GraphKeys.PARENT_GRAPH]
            result: list = []
            for n in nodes:
                children = G.nodes[n][GraphKeys.NODES]
                result += collect(parent, children)
            return result

        original = Partition.__find_original_graph(self.G)
        blocks = [collect(self.G, C) for C in self._blocks]
        return Partition.from_partition(original, blocks, weight=self._weight_key)

    def aggregate_graph(self) -> nx.Graph:
        """
        Build the coarse-grained graph of communities:
        - Each community becomes one node (with GraphKeys.NODES set of original members).
        - Edge weights are sum of inter-community weights.

        Determinism note:
          The aggregation result is independent of edge iteration order, since
          weights are summed. The node indices in the aggregate are the block
          indices in `_blocks` (stable under our updates).
        """
        H = nx.Graph(
            **{GraphKeys.PARENT_GRAPH: self.G, GraphKeys.PARENT_PARTITION: self}
        )
        # add supernodes
        for idx, C in enumerate(self._blocks):
            w = sum(self.G.nodes[v].get(self._weight_key, 1) for v in C)
            H.add_node(idx, **{GraphKeys.WEIGHT: w, GraphKeys.NODES: frozenset(C)})
        # add weighted edges
        for u, v, w in self.G.edges(data=self._weight_key, default=1):
            cu, cv = self._node2block[u], self._node2block[v]
            prev = H.get_edge_data(cu, cv, {GraphKeys.WEIGHT: 0})[GraphKeys.WEIGHT]
            H.add_edge(cu, cv, **{GraphKeys.WEIGHT: prev + w})
        return H

    # ---- Convenience ----
    def community_of(self, node: T_co) -> set[T_co]:
        """
        Return the community set containing `node`.
        """
        return self._blocks[self._node2block[node]]

    def adjacent_communities(self, node: T_co) -> set[frozenset[T_co]]:
        """
        Return communities of `node` and its neighbors as frozensets.

        Returning frozensets makes the candidates hashable and safe to compare,
        without exposing internal `_blocks` for mutation.
        """
        ids = {self._node2block[u] for u in self.G[node]} | {self._node2block[node]}
        return {frozenset(self._blocks[i]) for i in ids}

    def adjacent_block_ids(self, node: T_co) -> list[int]:
        """
        Fast variant: return block IDs for node's community and neighbors' communities.

        This avoids constructing frozensets when only block indices are needed,
        saving allocations in tight inner loops.
        """
        ids = {self._node2block[node]}
        for u in self.G[node]:
            ids.add(self._node2block[u])
        return list(ids)

    def community_degree_sum(self, node: T_co) -> int:
        """
        Sum of degrees of all nodes in node's community.

        Useful for local heuristics or diagnostics without recomputing from scratch.
        """
        return self._block_degree_sums[self._node2block[node]]


# ---------- Helpers ----------


def freeze_sets(set_list: Iterable[Set[T_co]]) -> set[frozenset[T_co]]:
    """
    Convert list of sets into a set of frozensets (hashable communities).

    This is handy when storing/using communities as dictionary keys or inside
    sets, while preserving value semantics for membership.
    """
    return {frozenset(s) for s in set_list}


def argmax(
    objective_function: Callable[[T_co], float], parameters: list[T_co]
) -> tuple[T_co, float, int]:
    """
    Return (best_param, best_value, index) maximizing objective_function over parameters.

    Raises
    ------
    ValueError
        If `parameters` is empty (guard against undefined behavior).
    """
    if not parameters:
        raise ValueError("parameters must be non-empty")
    best = parameters[0]
    best_val = objective_function(best)
    best_idx = 0
    for i, p in enumerate(parameters[1:], 1):
        val = objective_function(p)
        if val > best_val:
            best, best_val, best_idx = p, val, i
    return best, best_val, best_idx


def cut_size_singleton(
    G: nx.Graph, v: T, D: Set[T], weight: Optional[str] = None
) -> float:
    """
    Fast cut-size of ({v}, D): sum of weights of edges from v into D.

    This helper runs in O(deg(v)) time by scanning only `v`'s adjacency list,
    rather than materializing any subgraph.
    """
    total = 0.0
    for u in G[v]:
        if u in D:
            total += G[v][u].get(weight, 1)
    return total


def node_weight_total(G: nx.Graph, N: NodeData[T]) -> int:
    """
    Total node weight for a single node or a collection of nodes.

    Assumes nodes carry GraphKeys.WEIGHT as weight attribute; if missing,
    defaults to 1. For collections, the function is applied recursively.

    Returns
    -------
    int
        Sum of node weights across the input set/element.
    """
    if not isinstance(N, Iterable):
        return cast(int, G.nodes[N].get(GraphKeys.WEIGHT, 1))
    return sum(node_weight_total(G, n) for n in N)


def ensure_edge_weights(G: nx.Graph, weight: Optional[str]) -> nx.Graph:
    """
    Ensure every edge in G has an attribute GraphKeys.WEIGHT.

    If `weight` is provided, copy that attribute into GraphKeys.WEIGHT.
    Otherwise, default every edge weight to 1.

    Notes
    -----
    * This function *mutates* `G` in place and also returns it for convenience.
    * Using a dedicated internal key (GraphKeys.WEIGHT) avoids accidental
      interference with user-supplied attribute names.

    Parameters
    ----------
    G : nx.Graph
        Graph to normalize.
    weight : str | None
        Existing attribute name to read from; if None, use default 1.

    Returns
    -------
    nx.Graph
        The same graph `G`, with GraphKeys.WEIGHT set on all edges.
    """
    # The `data=weight, default=1` pattern yields either the existing value
    # under `weight` or 1 when the attribute is missing. We then mirror that
    # value into the internal, standardized key.
    for u, v, d in G.edges(data=weight, default=1):
        if weight is None and d != 1:
            # This branch is rare; if the caller passed weight=None but
            # NetworkX yields something other than 1, we still mirror it.
            logger.debug(
                "ensure_edge_weights: copying edge (%r,%r) value=%r into %s",
                u,
                v,
                d,
                GraphKeys.WEIGHT,
            )
        G.edges[u, v][GraphKeys.WEIGHT] = d
    return G
