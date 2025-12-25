"""
binary_bic.py

Community detection powered by the Leiden algorithm with BIC minimization.

Models supported
----------------
  • SBM   (Stochastic Block Model)
  • dcSBM (Degree-Corrected Stochastic Block Model)

Usage
-----
Call:
    detect_communities(..., degree_corrected=False)  → SBM BIC
    detect_communities(..., degree_corrected=True)   → dcSBM BIC

This module provides:
  - A BIC-based quality function for SBM and dcSBM.
  - Multi-pass Leiden optimisers for both models.
  - Target-K enforcement via BIC-guided merges and Leiden-based splits.
"""

from __future__ import annotations

import logging
import math
import os
import random
from copy import copy
from typing import Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np
from numba import njit, prange, set_num_threads

from ..ergms_solvers.binary_solvers import solve_dcSBM_iterative, solve_UBCM_iterative
from ..leiden.leiden_engine import (
    LeidenEngine,
    macro_merge_partition,
    merge_communities,
)
from ..leiden.partitions_functions import Partition

# Centralised constants
from ..utils.constants import (
    CHI_CAP,  # cap on χ when a block is fully connected
    EPS,  # small epsilon for safe logs / divisions
    MAX_IT_CHI,  # max Newton steps for block-χ slice
    MAX_IT_DEFAULT,  # default outer-iteration cap for solvers
    PATIENCE_DEFAULT,  # default patience for early-stop in solvers
    TOL_CHI,  # tolerance for block-χ Newton slice
    TOL_DCSBM,  # default tol for dcSBM root-finding
)
from ..utils.repro import configure_logging

# -----------------------------------------------------------------------------
# Module-level logger
# -----------------------------------------------------------------------------
logger = logging.getLogger("domino.bic.binary")

# -----------------------------------------------------------------------------
# Thread control for numba
# -----------------------------------------------------------------------------
N_THREADS = max(1, int(os.getenv("THREADS", os.cpu_count() or 1)))
set_num_threads(N_THREADS)

# =============================================================================
# Helper: Partition → dict
# =============================================================================


def _part2dict(part: Partition) -> Dict[int, int]:
    """
    Convert a Partition into a mapping from node index to community index.

    The community indices follow the iteration order of the blocks in the
    given Partition instance.
    """
    mapping: Dict[int, int] = {}
    for cid, block in enumerate(part):
        for v in block:
            mapping[int(v)] = cid
    return mapping


# =============================================================================
# Target-K enforcement: BIC-guided merging (SBM) and optional splitting
# =============================================================================


@njit(cache=True, fastmath=True)
def _ll_pair_sbm(L_rs: np.int64, M_rs: np.int64) -> float:
    """
    Contribution to the SBM log-likelihood from a single block pair (r,s),
    where L_rs is the number of observed edges and M_rs the number of
    possible dyads in that pair.
    """
    if M_rs <= 0 or L_rs == 0 or L_rs == M_rs:
        return 0.0
    p = L_rs / M_rs
    return L_rs * math.log(p) + (M_rs - L_rs) * math.log(1.0 - p)


@njit(cache=True, fastmath=True)
def _delta_ll_merge_sbm(L: np.ndarray, n: np.ndarray, r: int, s: int) -> float:
    """
    Change in SBM log-likelihood if communities r and s are merged into r.

    Only terms involving r and s are updated, which allows an efficient
    evaluation of the log-likelihood difference.
    """
    B = n.size
    nr, ns = n[r], n[s]

    # Old contributions
    ll_old = 0.0
    # Self terms and between r,s
    ll_old += _ll_pair_sbm(L[r, r], nr * (nr - 1) // 2)
    ll_old += _ll_pair_sbm(L[s, s], ns * (ns - 1) // 2)
    ll_old += _ll_pair_sbm(L[r, s], nr * ns)
    # Interactions with other communities
    for q in range(B):
        if q == r or q == s:
            continue
        ll_old += _ll_pair_sbm(L[r, q], nr * n[q])
        ll_old += _ll_pair_sbm(L[s, q], ns * n[q])

    # New contributions after merging
    nt = nr + ns
    ll_new = 0.0
    # New self term
    lt = L[r, r] + L[s, s] + L[r, s]
    ll_new += _ll_pair_sbm(lt, nt * (nt - 1) // 2)
    # New cross terms
    for q in range(B):
        if q == r or q == s:
            continue
        l_tq = L[r, q] + L[s, q]
        ll_new += _ll_pair_sbm(l_tq, nt * n[q])

    return ll_new - ll_old


@njit(cache=True, fastmath=True)
def _delta_bic_merge_sbm(L: np.ndarray, n: np.ndarray, r: int, s: int, N: int) -> float:
    """
    Variation in BIC when merging communities (r,s) under the vanilla SBM.

    The BIC is:
        BIC = k * log(V) - 2 * logL,
    where k = B(B+1)/2 and V = N(N-1)/2, with B the number of blocks.
    """
    B = n.size
    V = N * (N - 1) / 2.0
    delta_pen = -B * math.log(V)  # k decreases by B after merging
    delta_ll = _delta_ll_merge_sbm(L, n, r, s)
    return delta_pen - 2.0 * delta_ll


def _init_block_stats_from_partition(
    A: np.ndarray, part: Partition
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Construct the block edge-count matrix L and the size vector n
    given a partition and the adjacency matrix A.

    This precomputes:
      - L[r,s] = number of edges between blocks r and s
      - n[r]   = size of block r
    """
    B = len(part)
    L = np.zeros((B, B), dtype=np.int64)
    n = np.zeros(B, dtype=np.int64)

    idxs: List[np.ndarray] = []
    for cid, C in enumerate(part):
        idx = np.fromiter((int(v) for v in C), dtype=np.int64)
        idxs.append(idx)
        n[cid] = idx.size

    for r in range(B):
        idx_r = idxs[r]
        if idx_r.size >= 2:
            sub = A[np.ix_(idx_r, idx_r)]
            L[r, r] = int(np.triu(sub, 1).sum())
        for s in range(r + 1, B):
            idx_s = idxs[s]
            if idx_r.size > 0 and idx_s.size > 0:
                val = int(A[np.ix_(idx_r, idx_s)].sum())
                L[r, s] = val
                L[s, r] = val

    return L, n


def _apply_merge_update_stats(
    L: np.ndarray, n: np.ndarray, r: int, s: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Update the block statistics (L, n) after merging community s into r.

    The function recomputes the row and column corresponding to the merged
    block and removes the entries associated with community s.
    """
    B = n.size

    # New self term
    L_rr_new = L[r, r] + L[s, s] + L[r, s]

    # Update cross terms
    for q in range(B):
        if q == r or q == s:
            continue
        L[r, q] = L[r, q] + L[s, q]
        L[q, r] = L[r, q]
    L[r, r] = L_rr_new

    # Remove row/column s
    L = np.delete(L, s, axis=0)
    L = np.delete(L, s, axis=1)
    n[r] = n[r] + n[s]
    n = np.delete(n, s)

    return L, n


@njit(cache=True, fastmath=True)
def _best_merge_pair_sbm(
    L: np.ndarray, n: np.ndarray, N: int
) -> Tuple[int, int, float]:
    """
    Evaluate ΔBIC for all block pairs (i<j) and return the best (most negative)
    merge candidate.
    """
    B = n.size
    best_i, best_j = -1, -1
    best_delta = 1e300
    for i in range(B - 1):
        for j in range(i + 1, B):
            d = _delta_bic_merge_sbm(L, n, i, j, N)
            if d < best_delta:
                best_delta = d
                best_i, best_j = i, j
    return best_i, best_j, best_delta


def _enforce_target_K_SBM(part: Partition, A: np.ndarray, K_target: int) -> Partition:
    """
    Enforce K_target communities by performing BIC-optimal merges
    under the vanilla SBM.

    If len(part) <= K_target, the partition is returned unchanged.
    Otherwise, communities are greedily merged until exactly K_target
    blocks are left or no valid merge is found.
    """
    part = part.flatten()
    if len(part) <= K_target:
        return part

    N = A.shape[0]
    L, n = _init_block_stats_from_partition(A, part)

    while len(part) > K_target:
        i, j, delta = _best_merge_pair_sbm(L, n, N)
        if i < 0:
            break
        part = merge_communities(part, i, j).flatten()
        L, n = _apply_merge_update_stats(L, n, i, j)

    return part


def _split_largest_community_with_leiden(
    part: Partition,
    G: nx.Graph,
    A: np.ndarray,
    *,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
) -> Partition:
    """
    Split the largest community in 'part' using a single Leiden pass
    on the induced subgraph, with SBM_BIC_Quality as quality function.

    If Leiden does not produce more than one block, a random bipartition
    of the largest community is used as a fallback.
    """
    flat = part.flatten()
    if len(flat) == 0:
        return flat

    sizes = [len(C) for C in flat]
    idx_max = int(np.argmax(sizes))
    largest_block = list(flat)[idx_max]
    if len(largest_block) <= 1:
        return flat

    # Nodes in the largest community (global labels)
    nodes_block = list(largest_block)
    idx = np.array(nodes_block, dtype=int)

    # Induced subgraph (keeps global labels) and corresponding adjacency
    G_sub = G.subgraph(nodes_block)
    A_sub = A[np.ix_(idx, idx)]

    # Local quality on the subgraph: we pass node_index=idx so that
    # the quality function knows how to map row indices to node labels.
    qf_sub = SBM_BIC_Quality(A_sub, node_index=idx)

    # Local Leiden on the induced subgraph (no initial partition)
    part_sub = LeidenEngine.run(
        G_sub,
        qf_sub,
        initial=None,
        theta=theta,
        gamma=gamma,
        random_state=random_state,
        verbose=verbose,
    )
    flat_sub = part_sub.flatten()
    new_blocks = [set(C) for C in flat_sub]

    # Fallback: random bipartition if there is no effective split
    if len(new_blocks) <= 1:
        rng = np.random.default_rng(
            random_state if isinstance(random_state, int) else None
        )
        nodes_block_arr = np.array(nodes_block)
        rng.shuffle(nodes_block_arr)
        mid = len(nodes_block_arr) // 2
        if mid == 0:
            return flat

        C1 = set(nodes_block_arr[:mid])
        C2 = set(nodes_block_arr[mid:])
        new_blocks = [C1, C2]

    # Replace the largest block with its refined sub-blocks
    blocks_global = [set(C) for C in flat]
    blocks_global.pop(idx_max)
    blocks_global.extend(new_blocks)

    new_part = Partition.from_partition(G, blocks_global).flatten()
    return new_part


def _enforce_target_K_exact(
    part: Partition,
    G: nx.Graph,
    A: np.ndarray,
    K_target: int,
    *,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    max_iters: int = 50,
    verbose: int | bool = False,
) -> Partition:
    """
    Heuristically enforce exactly K_target communities by alternating:

      - BIC-guided merges (when B > K_target), via _enforce_target_K_SBM;
      - Leiden-based splits of the largest community (when B < K_target).

    This routine is used as a post-processing step after each Leiden pass
    (for both SBM and dcSBM), so that the working partition stays close
    to the desired block count.
    """
    part = part.flatten()
    N = G.order()
    if K_target <= 0 or K_target > N:
        if verbose:
            logger.warning(
                "_enforce_target_K_exact: invalid K_target=%d for N=%d; leaving partition unchanged.",
                K_target,
                N,
            )
        return part

    for _ in range(max_iters):
        B = len(part)
        if B == K_target:
            return part

        if B > K_target:
            part = _enforce_target_K_SBM(part, A, K_target)
            continue

        # B < K_target: attempt to split the largest community
        prev_B = B
        part = _split_largest_community_with_leiden(
            part,
            G,
            A,
            theta=theta,
            gamma=gamma,
            random_state=random_state,
            verbose=verbose,
        )
        B_new = len(part)

        if B_new == prev_B:
            if verbose:
                logger.warning(
                    "_enforce_target_K_exact: could not increase B from %d; stopping.",
                    B_new,
                )
            return part

    if verbose:
        logger.warning(
            "_enforce_target_K_exact: reached max_iters=%d without stabilising at K=%d (final B=%d).",
            max_iters,
            K_target,
            len(part),
        )
    return part


# =============================================================================
# Vanilla SBM: BIC objective and multi-pass Leiden
# =============================================================================


@njit(cache=True, fastmath=True)
def _sbm_loglik(adj: np.ndarray, comm: np.ndarray, com_sizes: np.ndarray) -> float:
    """
    Compute the SBM log-likelihood:

        logL = sum_{r≤s} [ L_rs log(L_rs / M_rs) +
                           (M_rs − L_rs) log(1 − L_rs / M_rs) ],

    where L_rs is the number of observed edges between communities r and s,
    and M_rs the number of possible dyads in that block pair.
    """
    B = com_sizes.size
    L = np.zeros((B, B), dtype=np.int64)

    N = adj.shape[0]
    for i in range(N):
        ci = comm[i]
        for j in range(i + 1, N):
            if adj[i, j]:
                cj = comm[j]
                L[ci, cj] += 1
                if ci != cj:
                    L[cj, ci] += 1

    logL = 0.0
    for r in range(B):
        nr = com_sizes[r]
        Mrr = nr * (nr - 1) // 2
        Lrr = L[r, r]
        if 0 < Lrr < Mrr:
            p = Lrr / Mrr
            logL += Lrr * math.log(p) + (Mrr - Lrr) * math.log(1 - p)
        for s in range(r + 1, B):
            ns = com_sizes[s]
            Mrs = nr * ns
            Lrs = L[r, s]
            if 0 < Lrs < Mrs:
                p = Lrs / Mrs
                logL += Lrs * math.log(p) + (Mrs - Lrs) * math.log(1 - p)
    return logL


def _bic_sbm(adj: np.ndarray, comm_dict: Dict[int, int]) -> float:
    """
    Compute the BIC for the vanilla SBM:

        BIC = k * log(V) − 2 * logL,

    where:
      - k   = B(B+1)/2 is the number of blockwise parameters;
      - V   = N(N−1)/2 is the number of possible edges;
      - logL is the SBM log-likelihood under the given partition.
    """
    N = adj.shape[0]
    comm = np.empty(N, dtype=np.int64)
    for i in range(N):
        comm[i] = comm_dict[i]
    B = comm.max() + 1

    com_sizes = np.bincount(comm, minlength=B)
    logL = _sbm_loglik(adj, comm, com_sizes)

    num_params = B * (B + 1) // 2
    V = N * (N - 1) / 2
    return num_params * math.log(V) - 2 * logL


class SBM_BIC_Quality:
    """
    Quality function for Leiden that corresponds to minus the SBM BIC.

    The optional argument `node_index` allows the quality function to be
    used on induced subgraphs whose adjacency matrix is stored in a
    specific node order. In that case:

        node_index[k] = original node label of row/column k in adj.

    When node_index is None, node labels are assumed to be 0..N−1.
    """

    def __init__(self, adj: np.ndarray, node_index: Optional[np.ndarray] = None):
        self.adj = adj
        if node_index is None:
            self.node_index = None
        else:
            self.node_index = np.asarray(node_index, dtype=int)

    def _comm_dict_from_partition(self, part: Partition) -> Dict[int, int]:
        """
        Build a dictionary mapping adjacency indices (0..N−1) to community
        labels, taking into account the possible presence of a custom
        node_index for subgraphs.
        """
        raw = _part2dict(part.flatten())  # keys are node labels of the graph
        if self.node_index is None:
            # Full graph: adjacency index i corresponds directly to node i
            return raw

        # Subgraph: adjacency index k corresponds to node self.node_index[k]
        mapping: Dict[int, int] = {}
        for k, node in enumerate(self.node_index):
            mapping[k] = raw[int(node)]
        return mapping

    def __call__(self, part: Partition) -> float:
        comm_dict = self._comm_dict_from_partition(part)
        return -_bic_sbm(self.adj, comm_dict)

    def delta(self, part: Partition, v: int, target: int) -> float:
        """
        Differential quality used by some Leiden implementations.
        This version recomputes the full quality as a robust default.
        """
        old = self.__call__(part)
        new = copy(part).move_node(v, target)
        return self.__call__(new) - old


def leiden_sbm(
    G: nx.Graph,
    adj: np.ndarray,
    *,
    initial=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
) -> Partition:
    """
    Perform a single Leiden pass on graph G using the SBM BIC quality function.

    Parameters
    ----------
    G : nx.Graph
        The underlying graph.
    adj : ndarray of shape (N, N)
        Binary adjacency matrix aligned with node indices 0..N−1.
    initial : Partition-like, optional
        Optional initial partition for warm-start.
    theta, gamma : float
        Standard Leiden refinement parameters.
    random_state : int or RNG, optional
        Random seed or generator for reproducible shuffles.
    verbose : bool or int
        If truthy, enable INFO-level logging for this pass.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "Leiden (SBM): starting a pass (theta=%.3f, gamma=%.3f)", theta, gamma
        )

    qf = SBM_BIC_Quality(adj)
    return LeidenEngine.run(
        G, qf, initial, theta, gamma, random_state=random_state, verbose=verbose
    )


def iterative_leiden_SBM(
    G: nx.Graph,
    A: np.ndarray,
    *,
    initial_partition=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    max_outer: int = 10,
    do_macro_merge: bool = False,
    target_K: Optional[int] = None,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
) -> Tuple[Partition, float]:
    """
    Multi-pass Leiden optimisation under the SBM BIC objective.

    The algorithm alternates global Leiden passes and optional macro-merge
    steps, always retaining the best partition in terms of BIC.

    If target_K is not None, the helper `_enforce_target_K_exact` is
    applied after each pass in order to (heuristically) maintain exactly
    target_K communities.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "iterative_leiden_SBM: start (max_outer=%d, do_macro_merge=%s, target_K=%s)",
            max_outer,
            do_macro_merge,
            str(target_K),
        )

    qf = SBM_BIC_Quality(A)

    init_flat = None
    if initial_partition is not None:
        init_flat = Partition.from_partition(G, initial_partition).flatten()

    # First Leiden pass
    part = leiden_sbm(
        G,
        A,
        initial=initial_partition,
        theta=theta,
        gamma=gamma,
        random_state=random_state,
        verbose=verbose,
    )
    if do_macro_merge:
        part = macro_merge_partition(part, qf)

    if target_K is not None:
        part = _enforce_target_K_exact(
            part,
            G,
            A,
            target_K,
            theta=theta,
            gamma=gamma,
            random_state=random_state,
            verbose=verbose,
        )

    flat = part.flatten()

    # Early stop if initial partition is unchanged
    if init_flat is not None and flat == init_flat:
        bic0 = _bic_sbm(A, _part2dict(flat))
        print("[SBM] Early stop: partition unchanged after first pass.")
        if verbose:
            logger.info(
                "[SBM] Early stop: partition unchanged after first pass (BIC=%.2f).",
                bic0,
            )
        return copy(flat), bic0

    best_part = copy(flat)
    best_bic = _bic_sbm(A, _part2dict(flat))

    # Outer loop
    for it in range(1, max_outer + 1):
        msg = f"[SBM] iter {it}: BIC={best_bic:.2f}, communities={len(flat)}"
        print(msg)
        if verbose:
            logger.info(msg)

        nxt = leiden_sbm(
            G,
            A,
            initial=flat,
            theta=theta,
            gamma=gamma,
            random_state=random_state,
            verbose=verbose,
        )

        if do_macro_merge:
            nxt = macro_merge_partition(nxt, qf)

        if target_K is not None:
            nxt = _enforce_target_K_exact(
                nxt,
                G,
                A,
                target_K,
                theta=theta,
                gamma=gamma,
                random_state=random_state,
                verbose=verbose,
            )

        flat_next = nxt.flatten()

        if flat_next == flat:
            print("[SBM] Converged (stable partition).")
            if verbose:
                logger.info("[SBM] Converged (stable partition).")
            break

        bic_now = _bic_sbm(A, _part2dict(flat_next))
        if bic_now < best_bic:
            best_bic, best_part = bic_now, copy(flat_next)

        flat = flat_next

    return best_part, best_bic


# =============================================================================
# Degree-Corrected SBM: BIC objective and multi-pass Leiden
# =============================================================================

# Preserve legacy symbols for the χ-solver interface
TOL_NEW = TOL_CHI
MAX_IT_NEW = MAX_IT_CHI


def _group_by_comm(xs: np.ndarray, comm: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Group a vector xs by community labels comm.

    Returns
    -------
    xs_sorted : ndarray
        The entries of xs sorted by comm.
    starts : ndarray
        Vector of start indices for each community in xs_sorted,
        with an extra sentinel at the end.
    """
    order = np.argsort(comm, kind="stable")
    xs_sorted = xs[order]
    comm_sorted = comm[order]
    _, first, _ = np.unique(comm_sorted, return_index=True, return_counts=True)
    starts = np.empty(first.size + 1, dtype=np.int64)
    starts[:-1] = first
    starts[-1] = xs.size
    return xs_sorted, starts


@njit(cache=True, fastmath=True)
def _dc_loglik(
    adj: np.ndarray, xs: np.ndarray, comm: np.ndarray, chi: np.ndarray
) -> float:
    """
    Log-likelihood of the degree-corrected SBM:

        logL = sum_{i<j} [ A_ij log p_ij + (1−A_ij) log(1−p_ij) ],

    with:
        p_ij = x_i x_j χ_{c_i, c_j} / (1 + x_i x_j χ_{c_i, c_j}).
    """
    N = adj.shape[0]
    ll = 0.0
    for i in range(N):
        xi, ci = xs[i], comm[i]
        for j in range(i + 1, N):
            xj, cj = xs[j], comm[j]
            z = xi * xj * chi[ci, cj]
            p = z / (1 + z)
            if adj[i, j]:
                if p > 0:
                    ll += math.log(p)
            else:
                if p < 1:
                    ll += math.log(1 - p)
    return ll


@njit(cache=True, fastmath=True)
def _chi_newton_slice(
    xs: np.ndarray,
    a0: int,
    a1: int,
    b0: int,
    b1: int,
    L_rs: int,
    same_block: bool,
    chi_init: float,
) -> float:
    """
    Solve for χ_{r,s} in a single block pair (r,s) by Newton's method,
    matching the expected number of edges to the observed count L_rs.

    The update is performed in the parameter χ, while xs are kept fixed.
    """
    if L_rs == 0:
        return 0.0

    # Total possible edges in this block pair
    m_rs = (a1 - a0) * (a1 - a0 - 1) // 2 if same_block else (a1 - a0) * (b1 - b0)
    if L_rs == m_rs:
        return CHI_CAP

    chi = chi_init if chi_init > 0.0 else 1.0
    for _ in range(MAX_IT_NEW):
        f = 0.0
        fp = 0.0
        for i in range(a0, a1):
            xi = xs[i]
            j_start = i + 1 if (same_block and b0 == a0) else b0
            for j in range(j_start, b1):
                t = xi * xs[j]
                denom = 1.0 + chi * t
                f += chi * t / denom
                fp += t / (denom * denom)
        f -= L_rs
        if abs(f) < TOL_NEW:
            return chi
        if fp < EPS:
            break
        chi = max(chi - f / fp, EPS)
    return chi


@njit(cache=True, parallel=True, fastmath=True)
def _solve_all_chi(
    xs_sorted: np.ndarray, starts: np.ndarray, L: np.ndarray
) -> np.ndarray:
    """
    Solve χ_{r,s} for all block pairs in parallel, given fixed xs and
    observed edge counts L[r,s].
    """
    B = starts.size - 1
    chi = np.zeros((B, B))
    for r in prange(B):
        a0, a1 = starts[r], starts[r + 1]
        for s in range(r, B):
            b0, b1 = starts[s], starts[s + 1]
            val = _chi_newton_slice(xs_sorted, a0, a1, b0, b1, L[r, s], r == s, 1.0)
            chi[r, s] = chi[s, r] = val
    return chi


def _chi_from_partition_and_x(
    A: np.ndarray, c: np.ndarray, xs_fixed: np.ndarray
) -> np.ndarray:
    """
    Given a fixed vector x and community labels c, solve χ_{r,s} for all
    block pairs using the observed edge counts in adjacency A.
    """
    L_obs = _build_L_obs(A, c)
    xs_sorted, starts = _group_by_comm(xs_fixed, c)
    chi = _solve_all_chi(xs_sorted, starts, L_obs)
    return chi


def _bic_dcSBM(
    adj: np.ndarray,
    xs: np.ndarray,
    comm_dict: Dict[int, int],
    chi: Optional[np.ndarray] = None,
) -> float:
    """
    Compute the BIC for the degree-corrected SBM:

        BIC = κ * log(V) − 2 * logL,

    where:
      - κ   = N + B(B+1)/2 accounts for node parameters x_i and block
              parameters χ_{r,s};
      - V   = N(N−1)/2 is the number of possible edges;
      - logL is the dcSBM log-likelihood.
    """
    N = adj.shape[0]
    comm = np.fromiter((comm_dict[i] for i in range(N)), dtype=np.int64)
    B = comm.max() + 1

    # Observed edges per block pair
    L = np.zeros((B, B), dtype=np.int64)
    for i in range(N):
        for j in range(i + 1, N):
            if adj[i, j]:
                L[comm[i], comm[j]] += 1
    L += L.T
    np.fill_diagonal(L, np.diag(L) // 2)

    if chi is None:
        xs_sorted, starts = _group_by_comm(xs, comm)
        chi = _solve_all_chi(xs_sorted, starts, L)

    logL = _dc_loglik(adj, xs, comm, chi)
    kappa = N + (B * (B + 1)) // 2
    V = N * (N - 1) / 2
    return kappa * math.log(V) - 2.0 * logL


class DC_BIC_Quality:
    """
    Quality function for Leiden that corresponds to minus the dcSBM BIC.
    """

    def __init__(self, adj: np.ndarray, xs: np.ndarray):
        self.adj = adj
        self.xs = xs

    def __call__(self, part: Partition) -> float:
        return -_bic_dcSBM(self.adj, self.xs, _part2dict(part.flatten()))

    def delta(self, part: Partition, v: int, target: int) -> float:
        """
        Differential quality used by some Leiden implementations.
        This version recomputes the full quality as a robust default.
        """
        old = self.__call__(part)
        new = copy(part).move_node(v, target)
        return self.__call__(new) - old


def leiden_dcSBM(
    G: nx.Graph,
    adj: np.ndarray,
    xs: np.ndarray,
    *,
    initial=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
) -> Partition:
    """
    Perform a single Leiden pass on graph G using the dcSBM BIC quality.

    Parameters
    ----------
    G : nx.Graph
        The underlying graph.
    adj : ndarray of shape (N, N)
        Binary adjacency matrix aligned with node indices 0..N−1.
    xs : ndarray
        Node parameters x_i of the dcSBM.
    initial : Partition-like, optional
        Optional initial partition for warm-start.
    theta, gamma : float
        Standard Leiden refinement parameters.
    random_state : int or RNG, optional
        Random seed or generator for reproducible shuffles.
    verbose : bool or int
        If truthy, enable INFO-level logging for this pass.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "Leiden (dcSBM): starting a pass (theta=%.3f, gamma=%.3f)", theta, gamma
        )

    return LeidenEngine.run(
        G,
        DC_BIC_Quality(adj, xs),
        initial,
        theta,
        gamma,
        random_state=random_state,
        verbose=verbose,
    )


def _build_L_obs(A: np.ndarray, c: np.ndarray) -> np.ndarray:
    """
    Build the observed link-count matrix L_obs between communities.

    Only upper-triangular entries of A (i<j) are considered, and off-diagonal
    entries are mirrored in (r,s) and (s,r). Within-community edges are
    counted once on the diagonal.
    """
    R = int(c.max()) + 1
    L_obs = np.zeros((R, R), dtype=int)

    iu, ju = np.triu_indices_from(A, k=1)
    w = A[iu, ju]
    nz = w != 0
    iu, ju, w = iu[nz], ju[nz], w[nz]
    ci = c[iu]
    cj = c[ju]

    same = ci == cj
    diff = ~same

    if np.any(same):
        np.add.at(L_obs, (ci[same], cj[same]), w[same])

    if np.any(diff):
        np.add.at(L_obs, (ci[diff], cj[diff]), w[diff])
        np.add.at(L_obs, (cj[diff], ci[diff]), w[diff])

    return L_obs


def iterative_leiden_dcSBM(
    G: nx.Graph,
    A: np.ndarray,
    *,
    initial_partition=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    max_outer: int = 10,
    do_macro_merge: bool = False,
    target_K: Optional[int] = None,
    fix_x_ubcm: bool = True,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
) -> Tuple[Partition, float]:
    """
    Multi-pass Leiden optimisation for the degree-corrected SBM under a BIC objective.

    The algorithm alternates:
      1) Re-estimation of (x, χ) given the current partition;
      2) A Leiden pass on the dcSBM BIC quality;
      3) Optional macro-merge steps;
      4) Optional target-K enforcement via `_enforce_target_K_exact`.

    Parameters
    ----------
    fix_x_ubcm : bool
        If True, x_i are obtained once from a UBCM fit and then held fixed:
        at each iteration only χ_{r,s} are updated. If False, a joint
        dcSBM parameter re-fit is attempted at every outer iteration.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "iterative_leiden_dcSBM: start (max_outer=%d, do_macro_merge=%s, target_K=%s, fix_x_ubcm=%s)",
            max_outer,
            do_macro_merge,
            str(target_K),
            fix_x_ubcm,
        )

    k = A.sum(axis=1)
    m_total = A.sum() / 2.0

    # 0) Bootstrap x
    if fix_x_ubcm:
        x0 = k / math.sqrt(2.0 * m_total) if m_total > 0 else np.maximum(k, EPS)
        xs, _ = solve_UBCM_iterative(k, x0)
    else:
        if initial_partition is not None:
            init_part = Partition.from_partition(G, initial_partition).flatten()
            c0 = np.empty(A.shape[0], dtype=int)
            for r, comm in enumerate(init_part):
                for v in comm:
                    c0[v] = r
            if len(init_part) == G.order():
                x0 = k / math.sqrt(2.0 * m_total) if m_total > 0 else np.maximum(k, EPS)
                xs, _ = solve_UBCM_iterative(k, x0)
            else:
                L_obs0 = _build_L_obs(A, c0)
                block_list0 = [
                    (r, s) for r in range(c0.max() + 1) for s in range(r, c0.max() + 1)
                ]
                x0 = (
                    k / np.sqrt(2 * L_obs0.sum())
                    if L_obs0.sum() > 0
                    else np.maximum(k, EPS)
                )
                chi0 = np.ones(len(block_list0))
                u_init0 = np.concatenate([x0, chi0])
                u_opt0, _ = solve_dcSBM_iterative(
                    k=k,
                    c=c0,
                    L_obs=L_obs0,
                    u_init=u_init0,
                    method="lm",
                    tol=TOL_DCSBM,
                    max_iter=MAX_IT_DEFAULT,
                    patience=PATIENCE_DEFAULT,
                    verbose=False,
                )
                xs = u_opt0[: A.shape[0]]
        else:
            x0 = k / math.sqrt(2.0 * m_total) if m_total > 0 else np.maximum(k, EPS)
            xs, _ = solve_UBCM_iterative(k, x0)

    # 1) First Leiden pass under dcSBM BIC
    qf = DC_BIC_Quality(A, xs)
    part = leiden_dcSBM(
        G,
        A,
        xs,
        initial=initial_partition,
        theta=theta,
        gamma=gamma,
        random_state=random_state,
        verbose=verbose,
    )

    if do_macro_merge:
        part = macro_merge_partition(part, qf)

    if target_K is not None:
        part = _enforce_target_K_exact(
            part,
            G,
            A,
            target_K,
            theta=theta,
            gamma=gamma,
            random_state=random_state,
            verbose=verbose,
        )

    flat = part.flatten()

    # Early stop if the initializer is unchanged
    if initial_partition is not None:
        init_flat = Partition.from_partition(G, initial_partition).flatten()
        if flat == init_flat:
            bic0 = _bic_dcSBM(A, xs, _part2dict(flat))
            print("[dcSBM] Early stop: partition unchanged after first pass.")
            if verbose:
                logger.info(
                    "[dcSBM] Early stop: partition unchanged after first pass (BIC=%.2f).",
                    bic0,
                )
            return copy(flat), bic0

    best_part: Optional[Partition] = None
    best_bic = float("inf")

    # 2) Outer loop: re-fit parameters and run Leiden
    for it in range(1, max_outer + 1):
        # Community labels for current partition
        c = np.empty(A.shape[0], dtype=int)
        for r, comm in enumerate(flat):
            for v in comm:
                c[v] = r

        if fix_x_ubcm:
            xs_ref = xs
            chi_ref = _chi_from_partition_and_x(A, c, xs_ref)
        else:
            L_obs = _build_L_obs(A, c)
            block_list = [
                (r, s) for r in range(c.max() + 1) for s in range(r, c.max() + 1)
            ]
            x0 = (
                k / math.sqrt(2 * L_obs.sum())
                if L_obs.sum() > 0
                else np.maximum(k, EPS)
            )
            chi0 = np.ones(len(block_list))
            u_init = np.concatenate([x0, chi0])

            u_opt, _ = solve_dcSBM_iterative(
                k=k,
                c=c,
                L_obs=L_obs,
                u_init=u_init,
                method="lm",
                tol=TOL_DCSBM,
                max_iter=MAX_IT_DEFAULT,
                patience=PATIENCE_DEFAULT,
                verbose=False,
            )
            xs_ref = u_opt[: A.shape[0]]
            chi_flat = u_opt[A.shape[0] :]
            chi_ref = np.zeros((c.max() + 1, c.max() + 1))
            for idx, (r, s) in enumerate(block_list):
                chi_ref[r, s] = chi_ref[s, r] = chi_flat[idx]

        bic_val = _bic_dcSBM(A, xs_ref, _part2dict(flat), chi_ref)
        if bic_val < best_bic:
            best_bic, best_part = bic_val, copy(flat)

        msg = f"[dcSBM] iter {it}: BIC={bic_val:.2f}, communities={len(flat)}"
        print(msg)
        if verbose:
            logger.info(msg)

        # Next Leiden pass with updated parameters
        qf = DC_BIC_Quality(A, xs_ref)
        part_next = leiden_dcSBM(
            G,
            A,
            xs_ref,
            initial=flat,
            theta=theta,
            gamma=gamma,
            random_state=random_state,
            verbose=verbose,
        )
        if do_macro_merge:
            part_next = macro_merge_partition(part_next, qf)

        if target_K is not None:
            part_next = _enforce_target_K_exact(
                part_next,
                G,
                A,
                target_K,
                theta=theta,
                gamma=gamma,
                random_state=random_state,
                verbose=verbose,
            )

        flat_next = part_next.flatten()

        if flat_next == flat:
            print("[dcSBM] Converged (stable partition).")
            if verbose:
                logger.info("[dcSBM] Converged (stable partition).")
            break

        flat = flat_next
        xs = xs_ref

    # 3) Post-hoc exact dcSBM BIC on best_part (if available and fix_x_ubcm)
    if fix_x_ubcm and best_part is not None:
        flat_final = best_part
        c = np.empty(A.shape[0], dtype=int)
        for r, comm in enumerate(flat_final):
            for v in comm:
                c[v] = r

        L_obs = _build_L_obs(A, c)
        block_list = [(r, s) for r in range(c.max() + 1) for s in range(r, c.max() + 1)]
        k = A.sum(axis=1)

        x0 = k / np.sqrt(2 * L_obs.sum()) if L_obs.sum() > 0 else np.maximum(k, EPS)
        chi0 = np.ones(len(block_list))
        u0 = np.concatenate([x0, chi0])

        tol_solver = TOL_DCSBM
        u_opt, best_norm = solve_dcSBM_iterative(
            k=k,
            c=c,
            L_obs=L_obs,
            u_init=u0,
            method="lm",
            tol=tol_solver,
            max_iter=MAX_IT_DEFAULT,
            patience=PATIENCE_DEFAULT,
            verbose=False,
        )

        if best_norm < tol_solver:
            x_hat = u_opt[: A.shape[0]]
            chi_hat = np.zeros((c.max() + 1, c.max() + 1))
            for idx, (r, s) in enumerate(block_list):
                chi_hat[r, s] = chi_hat[s, r] = u_opt[A.shape[0] + idx]

            true_bic = _bic_dcSBM(A, x_hat, _part2dict(flat_final), chi_hat)
            print(f"[dcSBM] Post-hoc full-parameter BIC (exact): {true_bic:.2f}")
            if verbose:
                logger.info(
                    "[dcSBM] Post-hoc full-parameter BIC (exact): %.2f", true_bic
                )
            best_bic = true_bic
        else:
            print(
                f"[dcSBM] Post-hoc solver did not converge; keeping fixed-x BIC={best_bic:.2f}."
            )
            if verbose:
                logger.warning(
                    "[dcSBM] Post-hoc solver did not converge; keeping fixed-x BIC=%.2f.",
                    best_bic,
                )

    if best_part is None:
        best_part = copy(flat)

    return best_part, best_bic
