"""
signed_bic.py

Community detection powered by the Leiden algorithm with BIC minimization
for *signed* networks.

Models supported
----------------
  • sSBM   (Signed Stochastic Block Model; +/− edges, tri-nomial per dyad)
  • sdcSBM (Signed Degree-Corrected SBM; node +/− factors and block +/− affinities)

Pipelines
---------
Call `iterative_leiden_sSBM(...)` or `iterative_leiden_sdcSBM(...)` to run the
respective pipelines. Their parameters mirror the binary versions for a drop-in
experience alongside `binary_bic.py`.
"""

from __future__ import annotations

import logging
import math
import os
import random
from copy import copy
from typing import Dict, Optional, Tuple, Union

import networkx as nx
import numpy as np
from numba import njit, prange, set_num_threads

from ..ergms_solvers.signed_solvers import (
    solve_SCM_iterative,
    solve_signed_dcSBM_iterative,
)
from ..leiden.leiden_engine import (
    LeidenEngine,
    macro_merge_partition,
    merge_communities,
)
from ..leiden.partitions_functions import Partition

# Centralized constants (kept equal to legacy defaults where they existed)
from ..utils.constants import (
    CHI_CAP,  # 1e12  (cap for fully connected block-pairs)
    EPS,  # 1e-12
    MAX_IT_CHI,  # 20    (Newton max iters for χ slices)
    MAX_IT_DEFAULT,  # 1000  (outer iteration cap for solvers)
    PATIENCE_DEFAULT,  # 10    (early-stop patience)
    TOL_CHI,  # 1e-6  (Newton tol for χ slices)
    TOL_SIGNED_DCSBM,  # 1e-6  (solver tolerance)
)

# Optional helpers (no-ops if caller already configured logging)
from ..utils.repro import configure_logging

# -----------------------------------------------------------------------------
# Module-level logger
# -----------------------------------------------------------------------------
logger = logging.getLogger("domino.bic.signed")

# -----------------------------------------------------------------------------
# Thread control for numba (kept compatible with the original pattern)
# -----------------------------------------------------------------------------
# Environment variable THREADS takes precedence; else fall back to os.cpu_count().
# We set numba's thread pool once at import time to avoid mid-run reconfiguration.
N_THREADS = max(1, int(os.getenv("THREADS", os.cpu_count() or 1)))
set_num_threads(N_THREADS)


# -----------------------------------------------------------------------------
# Utility: flatten a Partition into a {node → community} dict
# -----------------------------------------------------------------------------
def _part2dict(part: Partition) -> Dict[int, int]:
    """
    Convert a Partition into a node→community mapping.

    This preserves the original community indices as iteration order over
    Partition blocks is consistent with how communities are stored.
    """
    mapping: Dict[int, int] = {}
    for cid, block in enumerate(part):
        for v in block:
            mapping[v] = cid
    return mapping


# =============================================================================
# Target-K enforcement for *signed* SBM (tri-nomial log-likelihood)
# =============================================================================


@njit(cache=True, fastmath=True)
def _ll_pair_signed(Lp_rs: np.int64, Ln_rs: np.int64, M_rs: np.int64) -> float:
    """
    Tri-nomial (+, −, 0) block-pair log-likelihood term at MLEs:
      p^+ = Lp/M, p^- = Ln/M, p^0 = 1 - (Lp+Ln)/M.

    Parameters
    ----------
    Lp_rs, Ln_rs : int
        Observed positive/negative edge counts for the block pair (unordered).
    M_rs : int
        Number of possible dyads in the block pair.

    Returns
    -------
    float
        Log-likelihood contribution for the pair.
    """
    if M_rs <= 0:
        return 0.0
    L0 = M_rs - (Lp_rs + Ln_rs)
    out = 0.0
    if Lp_rs > 0:
        p = Lp_rs / M_rs
        out += Lp_rs * math.log(p)
    if Ln_rs > 0:
        q = Ln_rs / M_rs
        out += Ln_rs * math.log(q)
    if L0 > 0:
        r = L0 / M_rs
        out += L0 * math.log(r)
    return out


@njit(cache=True, fastmath=True)
def _delta_ll_merge_signed(
    Lp: np.ndarray, Ln: np.ndarray, n: np.ndarray, r: int, s: int
) -> float:
    """
    Change in signed SBM log-likelihood if we merge communities r and s (into r).
    Only pairs touching r or s are affected.
    """
    B = n.size
    nr, ns = n[r], n[s]

    ll_old = 0.0
    # self and between r,s
    ll_old += _ll_pair_signed(Lp[r, r], Ln[r, r], nr * (nr - 1) // 2)
    ll_old += _ll_pair_signed(Lp[s, s], Ln[s, s], ns * (ns - 1) // 2)
    ll_old += _ll_pair_signed(Lp[r, s], Ln[r, s], nr * ns)

    # cross with q
    for q in range(B):
        if q == r or q == s:
            continue
        ll_old += _ll_pair_signed(Lp[r, q], Ln[r, q], nr * n[q])
        ll_old += _ll_pair_signed(Lp[s, q], Ln[s, q], ns * n[q])

    # NEW (after merge)
    nt = nr + ns
    lt_p = Lp[r, r] + Lp[s, s] + Lp[r, s]
    lt_n = Ln[r, r] + Ln[s, s] + Ln[r, s]
    ll_new = _ll_pair_signed(lt_p, lt_n, nt * (nt - 1) // 2)

    for q in range(B):
        if q == r or q == s:
            continue
        ltp = Lp[r, q] + Lp[s, q]
        ltn = Ln[r, q] + Ln[s, q]
        ll_new += _ll_pair_signed(ltp, ltn, nt * n[q])

    return ll_new - ll_old


@njit(cache=True, fastmath=True)
def _delta_bic_merge_signed(
    Lp: np.ndarray, Ln: np.ndarray, n: np.ndarray, r: int, s: int, N: int
) -> float:
    """
    ΔBIC for merging (r,s) in signed SBM:
        k = B(B+1)   (two parameters per unordered block-pair)
        Δk = k_after − k_before = (B−1)B − B(B+1) = −2B
        ΔBIC = Δk * log V  −  2 * ΔlogL
    """
    B = n.size
    V = N * (N - 1) / 2.0
    delta_pen = -2.0 * B * math.log(V)
    delta_ll = _delta_ll_merge_signed(Lp, Ln, n, r, s)
    return delta_pen - 2.0 * delta_ll


def _init_block_stats_from_partition_signed(
    Ap: np.ndarray, An: np.ndarray, part: Partition
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build Lp (pos), Ln (neg) and size vector n for the current partition.
    Costs O(B^2) submatrix sums once; subsequent merges are O(B) updates.
    """
    B = len(part)
    Lp = np.zeros((B, B), dtype=np.int64)
    Ln = np.zeros((B, B), dtype=np.int64)
    n = np.zeros(B, dtype=np.int64)

    idxs: list[np.ndarray] = []
    for cid, C in enumerate(part):
        idx = np.fromiter((int(v) for v in C), dtype=np.int64)
        idxs.append(idx)
        n[cid] = idx.size

    for r in range(B):
        ir = idxs[r]
        if ir.size >= 2:
            subp = Ap[np.ix_(ir, ir)]
            subn = An[np.ix_(ir, ir)]
            Lp[r, r] = int(np.triu(subp, 1).sum())
            Ln[r, r] = int(np.triu(subn, 1).sum())
        for s in range(r + 1, B):
            is_ = idxs[s]
            if ir.size > 0 and is_.size > 0:
                vp = int(Ap[np.ix_(ir, is_)].sum())
                vn = int(An[np.ix_(ir, is_)].sum())
                Lp[r, s] = Lp[s, r] = vp
                Ln[r, s] = Ln[s, r] = vn
    return Lp, Ln, n


def _apply_merge_update_stats_signed(
    Lp: np.ndarray, Ln: np.ndarray, n: np.ndarray, r: int, s: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Update (Lp, Ln, n) after merging s into r (and dropping s).
    """
    B = n.size
    # new self
    Lp_rr_new = Lp[r, r] + Lp[s, s] + Lp[r, s]
    Ln_rr_new = Ln[r, r] + Ln[s, s] + Ln[r, s]

    for q in range(B):
        if q == r or q == s:
            continue
        Lp[r, q] += Lp[s, q]
        Ln[r, q] += Ln[s, q]
        Lp[q, r] = Lp[r, q]
        Ln[q, r] = Ln[r, q]

    Lp[r, r] = Lp_rr_new
    Ln[r, r] = Ln_rr_new

    # remove row/col s
    Lp = np.delete(np.delete(Lp, s, axis=0), s, axis=1)
    Ln = np.delete(np.delete(Ln, s, axis=0), s, axis=1)
    n[r] = n[r] + n[s]
    n = np.delete(n, s)
    return Lp, Ln, n


@njit(cache=True, fastmath=True)
def _best_merge_pair_signed(
    Lp: np.ndarray, Ln: np.ndarray, n: np.ndarray, N: int
) -> tuple[int, int, float]:
    """
    Evaluate ΔBIC for all pairs (i<j) and return the best (most negative).
    """
    B = n.size
    best_i, best_j = -1, -1
    best_delta = 1e300
    for i in range(B - 1):
        for j in range(i + 1, B):
            d = _delta_bic_merge_signed(Lp, Ln, n, i, j, N)
            if d < best_delta:
                best_delta = d
                best_i, best_j = i, j
    return best_i, best_j, best_delta


def _enforce_target_K_sSBM(
    part: Partition, Ap: np.ndarray, An: np.ndarray, K_target: int
) -> Partition:
    """
    Greedy BIC-optimal merges until len(part) == K_target (signed SBM model).
    Works entirely on block stats; updates partition only for the chosen merge.
    """
    part = part.flatten()
    if len(part) <= K_target:
        return part

    N = Ap.shape[0]
    Lp, Ln, n = _init_block_stats_from_partition_signed(Ap, An, part)

    while len(part) > K_target:
        i, j, _ = _best_merge_pair_signed(Lp, Ln, n, N)
        if i < 0:
            break
        part = merge_communities(part, i, j).flatten()
        Lp, Ln, n = _apply_merge_update_stats_signed(Lp, Ln, n, i, j)

    return part


# -----------------------------------------------------------------------------
# Exact target-K enforcement (split + merge), in analogy with binary_bic.py
# -----------------------------------------------------------------------------
def _split_largest_community_with_leiden_sSBM(
    part: Partition,
    G: nx.Graph,
    Ap: np.ndarray,
    An: np.ndarray,
    theta: float,
    gamma: float,
    random_state: Optional[Union[int, np.random.Generator, random.Random]],
    verbose: int | bool = False,
) -> Partition:
    """
    Attempt to increase the number of communities by splitting the largest
    block via a local Leiden pass on the induced subgraph.

    The procedure is:
      1. Identify the largest community C in the current partition.
      2. Build the induced adjacency matrices (Apos_C, Aneg_C) on C and
         re-index nodes locally as 0,...,|C|−1.
      3. Run a fresh Leiden pass on the local graph with BIC as quality.
      4. If Leiden returns more than one community, replace C with these
         subcommunities (mapped back to global node labels).
      5. If the split does not increase the total number of blocks, return
         the original partition.
    """
    part_flat = part.flatten()
    B = len(part_flat)
    if B == 0:
        return part_flat

    # Find index of the largest community
    sizes = [len(C) for C in part_flat]
    idx_big = int(np.argmax(sizes))
    C_big = list(part_flat[idx_big])
    if len(C_big) <= 1:
        # Cannot split a singleton community
        return part_flat

    # Sort for deterministic behaviour
    C_big_sorted = sorted(int(v) for v in C_big)
    n_sub = len(C_big_sorted)

    # Induced signed adjacency on C_big, with local indices 0..n_sub-1
    Ap_sub = Ap[np.ix_(C_big_sorted, C_big_sorted)]
    An_sub = An[np.ix_(C_big_sorted, C_big_sorted)]

    # Local graph with nodes {0,...,n_sub-1}
    G_sub = nx.Graph()
    G_sub.add_nodes_from(range(n_sub))

    iu, ju = np.triu_indices(n_sub, k=1)
    mask = (Ap_sub[iu, ju] != 0) | (An_sub[iu, ju] != 0)
    edges = [(int(i), int(j)) for i, j, ok in zip(iu, ju, mask, strict=False) if ok]
    if not edges:
        # Community is internally edgeless, nothing meaningful to split
        return part_flat
    G_sub.add_edges_from(edges)

    # Local Signed-SBM BIC quality on (Ap_sub, An_sub)
    qf_sub = Signed_SBM_BIC_Quality(Ap_sub, An_sub)

    # Local Leiden pass (no initializer: we want a fresh split proposal)
    part_sub = LeidenEngine.run(
        G_sub,
        qf_sub,
        initial=None,
        theta=theta,
        gamma=gamma,
        random_state=random_state,
        verbose=verbose,
    ).flatten()

    if len(part_sub) <= 1:
        # Leiden did not find a non-trivial split
        return part_flat

    # Map local communities back to global node labels
    new_blocks_big = []
    for block in part_sub:
        global_block = {C_big_sorted[int(v)] for v in block}
        if len(global_block) > 0:
            new_blocks_big.append(global_block)

    if len(new_blocks_big) <= 1:
        # No effective increase in the number of blocks
        return part_flat

    # Rebuild the full partition: replace C_big with the blocks from the split
    blocks_new = []
    for b_idx, block in enumerate(part_flat):
        if b_idx == idx_big:
            continue
        blocks_new.append(set(int(v) for v in block))
    blocks_new.extend(new_blocks_big)

    # Construct a new Partition on the original graph
    new_part = Partition.from_partition(G, blocks_new)
    return new_part.flatten()


def _enforce_target_K_exact_sSBM(
    part: Partition,
    G: nx.Graph,
    Ap: np.ndarray,
    An: np.ndarray,
    K_target: int,
    theta: float,
    gamma: float,
    random_state: Optional[Union[int, np.random.Generator, random.Random]],
    verbose: int | bool = False,
    max_iters: int = 50,
) -> Partition:
    """
    Enforce an exact target number of communities K_target using a combination
    of BIC-optimal merges and local Leiden-based splits, in analogy with the
    binary SBM implementation.

    Strategy
    --------
      • If the current number of blocks B is larger than K_target, we rely on
        the merge-only routine `_enforce_target_K_sSBM`, which repeatedly
        merges blocks so as to minimise the increase in BIC.

      • If B is smaller than K_target, we attempt to increase B by splitting
        the largest block using `_split_largest_community_with_leiden_sSBM`,
        which proposes a finer partition of that community based on a local
        Leiden run with the signed-SBM BIC as quality function.

      • Whenever a split overshoots K_target (B > K_target after splitting),
        we finish by invoking `_enforce_target_K_sSBM` once to merge back to
       exactly K_target blocks.

    The procedure is stopped either when K_target is reached or when no
    additional non-trivial splits are possible.
    """
    part = part.flatten()
    if K_target is None:
        return part

    # Case B > K_target: use merge-only enforcement, which is already BIC-based.
    if len(part) > K_target:
        return _enforce_target_K_sSBM(part, Ap, An, K_target)

    # Case B <= K_target: try to create new blocks by splitting the largest one.
    it = 0
    while len(part) < K_target and it < max_iters:
        it += 1
        prev_B = len(part)
        part = _split_largest_community_with_leiden_sSBM(
            part, G, Ap, An, theta, gamma, random_state, verbose
        )
        B_new = len(part)
        if B_new <= prev_B:
            # No effective split, cannot get closer to K_target
            break
        if B_new > K_target:
            # Slight overshoot: finish with merge-only reduction back to K_target
            part = _enforce_target_K_sSBM(part, Ap, An, K_target)
            break

    return part


# =============================================================================
# Signed SBM: likelihood & BIC
# =============================================================================


@njit(cache=True, fastmath=True)
def _signed_sbm_loglik(
    Ap: np.ndarray, An: np.ndarray, comm: np.ndarray, sizes: np.ndarray
) -> float:
    """
    Tri-nomial (+,−,0) SBM log-likelihood at blockwise MLEs.
    """
    B = sizes.size
    N = Ap.shape[0]

    Lp = np.zeros((B, B), dtype=np.int64)
    Ln = np.zeros((B, B), dtype=np.int64)

    # count +/− edges per block-pair (i<j once)
    for i in range(N):
        ci = comm[i]
        for j in range(i + 1, N):
            if Ap[i, j]:
                cj = comm[j]
                Lp[ci, cj] += 1
                if ci != cj:
                    Lp[cj, ci] += 1
            if An[i, j]:
                cj = comm[j]
                Ln[ci, cj] += 1
                if ci != cj:
                    Ln[cj, ci] += 1

    logL = 0.0
    for r in range(B):
        nr = sizes[r]
        Mrr = nr * (nr - 1) // 2
        logL += _ll_pair_signed(Lp[r, r], Ln[r, r], Mrr)
        for s in range(r + 1, B):
            Mrs = nr * sizes[s]
            logL += _ll_pair_signed(Lp[r, s], Ln[r, s], Mrs)
    return logL


def _bic_signed_sbm(Ap: np.ndarray, An: np.ndarray, comm_dict: Dict[int, int]) -> float:
    """
    BIC for signed SBM:
      k = B(B+1),  V = N(N−1)/2
      BIC = k*log(V) − 2*logL
    """
    N = Ap.shape[0]
    comm = np.empty(N, dtype=np.int64)
    for i in range(N):
        comm[i] = comm_dict[i]
    B = comm.max() + 1
    sizes = np.bincount(comm, minlength=B)

    logL = _signed_sbm_loglik(Ap, An, comm, sizes)
    k = B * (B + 1)  # two parameters per unordered block-pair
    V = N * (N - 1) / 2.0
    return k * math.log(V) - 2.0 * logL


class Signed_SBM_BIC_Quality:
    """Leiden quality = −BIC for the signed SBM."""

    def __init__(self, Apos: np.ndarray, Aneg: np.ndarray):
        self.Apos, self.Aneg = Apos, Aneg

    def __call__(self, part):
        return -_bic_signed_sbm(self.Apos, self.Aneg, _part2dict(part.flatten()))

    def delta(self, part, v, target):
        old = self.__call__(part)
        new = copy(part).move_node(v, target)
        return self.__call__(new) - old


def leiden_signed_sbm(
    G: nx.Graph,
    Apos: np.ndarray,
    Aneg: np.ndarray,
    *,
    initial=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
):
    """
    One Leiden pass maximizing −BIC for signed SBM.

    Parameters
    ----------
    G : nx.Graph
        Graph on which to run Leiden.
    Apos, Aneg : (N,N) ndarray
        Binary +/− adjacencies (0/1).
    initial : Partition-like or None
        Initial partition (optional).
    theta, gamma : float
        Refinement parameters (as in Leiden).
    random_state : int | np.random.Generator | random.Random | None
        RNG seed/instance enabling deterministic shuffles and tie-breaks.
    verbose : int | bool
        If truthy, emit INFO-level progress logs.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "Leiden (sSBM): starting a pass (theta=%.3f, gamma=%.3f)", theta, gamma
        )

    qf = Signed_SBM_BIC_Quality(Apos, Aneg)
    return LeidenEngine.run(
        G, qf, initial, theta, gamma, random_state=random_state, verbose=verbose
    )


def iterative_leiden_sSBM(
    G: nx.Graph,
    Apos: np.ndarray,
    Aneg: np.ndarray,
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
    Repeat Leiden passes until no further improvement in BIC (signed SBM).
    Returns the best partition found and its BIC.

    Notes
    -----
    • `random_state` is forwarded to the engine for reproducible node-order shuffles.
    • `verbose` controls INFO-level logging; legacy prints are preserved.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "iterative_leiden_sSBM: start (max_outer=%d, do_macro_merge=%s, target_K=%s)",
            max_outer,
            do_macro_merge,
            str(target_K),
        )

    qf = Signed_SBM_BIC_Quality(Apos, Aneg)

    init_flat = None
    if initial_partition is not None:
        init_flat = Partition.from_partition(G, initial_partition).flatten()

    part = leiden_signed_sbm(
        G,
        Apos,
        Aneg,
        initial=initial_partition,
        theta=theta,
        gamma=gamma,
        random_state=random_state,
        verbose=verbose,
    )
    if do_macro_merge:
        part = macro_merge_partition(part, qf)
    if target_K is not None:
        part = _enforce_target_K_exact_sSBM(
            part, G, Apos, Aneg, target_K, theta, gamma, random_state, verbose
        )
    flat = part.flatten()

    if init_flat is not None and flat == init_flat:
        bic0 = _bic_signed_sbm(Apos, Aneg, _part2dict(flat))
        print("[sSBM] Early stop: partition unchanged after first pass.")
        if verbose:
            logger.info(
                "[sSBM] Early stop: partition unchanged after first pass (BIC=%.2f).",
                bic0,
            )
        return copy(flat), bic0

    best_part = copy(flat)
    best_bic = _bic_signed_sbm(Apos, Aneg, _part2dict(flat))

    for it in range(1, max_outer + 1):
        msg = f"[sSBM] iter {it}: BIC={best_bic:.2f}, communities={len(flat)}"
        print(msg)
        if verbose:
            logger.info(msg)

        nxt = leiden_signed_sbm(
            G,
            Apos,
            Aneg,
            initial=flat,
            theta=theta,
            gamma=gamma,
            random_state=random_state,
            verbose=verbose,
        )
        if do_macro_merge:
            nxt = macro_merge_partition(nxt, qf)
        if target_K is not None:
            nxt = _enforce_target_K_exact_sSBM(
                nxt, G, Apos, Aneg, target_K, theta, gamma, random_state, verbose
            )
        flat_next = nxt.flatten()

        if flat_next == flat:
            print("[sSBM] Converged (stable partition).")
            if verbose:
                logger.info("[sSBM] Converged (stable partition).")
            break

        bic_now = _bic_signed_sbm(Apos, Aneg, _part2dict(flat_next))
        if bic_now < best_bic:
            best_bic, best_part = bic_now, copy(flat_next)
        flat = flat_next

    return best_part, best_bic


# =============================================================================
# Signed dcSBM: likelihood, χ-solvers (fixed-x path), and BIC
# =============================================================================


def _group_by_comm_both(
    xs_plus: np.ndarray, xs_minus: np.ndarray, comm: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Sort x^+ and x^- by community label (same permutation for both) and
    return xs_plus_sorted, xs_minus_sorted, and 'starts' boundaries.
    """
    order = np.argsort(comm, kind="stable")
    xp_sorted = xs_plus[order]
    xm_sorted = xs_minus[order]
    comm_sorted = comm[order]
    _, first, _ = np.unique(comm_sorted, return_index=True, return_counts=True)
    starts = np.empty(first.size + 1, dtype=np.int64)
    starts[:-1] = first
    starts[-1] = xs_plus.size
    return xp_sorted, xm_sorted, starts


@njit(cache=True, fastmath=True)
def _loglik_signed_dcSBM(
    Ap: np.ndarray,
    An: np.ndarray,
    xp: np.ndarray,
    xm: np.ndarray,
    comm: np.ndarray,
    chi_p: np.ndarray,
    chi_m: np.ndarray,
) -> float:
    """
    Log-likelihood for signed dcSBM with tri-nomial probabilities.
    """
    N = Ap.shape[0]
    ll = 0.0
    for i in range(N):
        xpi, xmi, ci = xp[i], xm[i], comm[i]
        for j in range(i + 1, N):
            cj = comm[j]
            zpi = xpi * xp[j] * chi_p[ci, cj]
            zmi = xmi * xm[j] * chi_m[ci, cj]
            denom = 1.0 + zpi + zmi
            if Ap[i, j]:
                p = zpi / denom
                if p > 0:
                    ll += math.log(p)
            elif An[i, j]:
                p = zmi / denom
                if p > 0:
                    ll += math.log(p)
            else:
                q = 1.0 - (zpi + zmi) / denom  # = 1/denom
                if q > 0:
                    ll += math.log(q)
    return ll


def _build_L_obs_signed(
    Ap: np.ndarray, An: np.ndarray, c: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build observed +/− link counts per community pair:
      - use only upper triangle (i<j)
      - off-diagonals filled symmetrically
      - diagonals count within-block edges once
    """
    R = int(c.max()) + 1
    Lp = np.zeros((R, R), dtype=int)
    Ln = np.zeros((R, R), dtype=int)

    iu, ju = np.triu_indices_from(Ap, k=1)
    # positive
    w = Ap[iu, ju]
    nz = w != 0
    ci = c[iu[nz]]
    cj = c[ju[nz]]
    same = ci == cj
    if np.any(same):
        np.add.at(Lp, (ci[same], cj[same]), w[nz][same])
    diff = ~same
    if np.any(diff):
        np.add.at(Lp, (ci[diff], cj[diff]), w[nz][diff])
        np.add.at(Lp, (cj[diff], ci[diff]), w[nz][diff])

    # negative
    w = An[iu, ju]
    nz = w != 0
    ci = c[iu[nz]]
    cj = c[ju[nz]]
    same = ci == cj
    if np.any(same):
        np.add.at(Ln, (ci[same], cj[same]), w[nz][same])
    diff = ~same
    if np.any(diff):
        np.add.at(Ln, (ci[diff], cj[diff]), w[nz][diff])
        np.add.at(Ln, (cj[diff], ci[diff]), w[nz][diff])

    return Lp, Ln


@njit(cache=True, fastmath=True)
def _chi2_newton_slice(
    xp_sorted: np.ndarray,
    xm_sorted: np.ndarray,
    a0: int,
    a1: int,
    b0: int,
    b1: int,
    Lp_rs: int,
    Ln_rs: int,
    same_block: bool,
    chi_p_init: float,
    chi_m_init: float,
) -> tuple[float, float]:
    """
    Solve (f^+=0, f^−=0) for a single block-pair (r,s) using 2D Newton:
      f^+(χ^+,χ^−) = ∑ p^+_{ij} − Lp_rs
      f^−(χ^+,χ^−) = ∑ p^−_{ij} − Ln_rs

    with p^+_{ij} = (χ^+ t^+_{ij}) / (1 + χ^+ t^+_{ij} + χ^- t^-_{ij}),
         p^−_{ij} = (χ^- t^-_{ij}) / (1 + χ^+ t^+_{ij} + χ^- t^-_{ij}),
    where t^+_{ij} = x^+_i x^+_j, t^-_{ij} = x^-_i x^-_j.
    """
    # total possible dyads in the slice
    m_rs = (a1 - a0) * (a1 - a0 - 1) // 2 if same_block else (a1 - a0) * (b1 - b0)
    # trivial cases
    if Lp_rs == 0 and Ln_rs == 0:
        return 0.0, 0.0
    if Lp_rs == m_rs and Ln_rs == 0:
        return CHI_CAP, 0.0
    if Ln_rs == m_rs and Lp_rs == 0:
        return 0.0, CHI_CAP

    cp = chi_p_init if chi_p_init > 0 else 1.0
    cm = chi_m_init if chi_m_init > 0 else 1.0

    for _ in range(MAX_IT_CHI):
        f1 = 0.0
        f2 = 0.0
        j11 = 0.0
        j12 = 0.0
        j21 = 0.0
        j22 = 0.0

        for i in range(a0, a1):
            xpi = xp_sorted[i]
            xmi = xm_sorted[i]
            j_start = i + 1 if (same_block and b0 == a0) else b0
            for j in range(j_start, b1):
                tp = xpi * xp_sorted[j]
                tm = xmi * xm_sorted[j]
                D = 1.0 + cp * tp + cm * tm

                pp = (cp * tp) / D
                pm = (cm * tm) / D

                f1 += pp
                f2 += pm

                invD2 = 1.0 / (D * D)
                j11 += tp * (D - cp * tp) * invD2
                j12 += -(cp * tp * tm) * invD2
                j21 += -(cm * tm * tp) * invD2
                j22 += tm * (D - cm * tm) * invD2

        f1 -= Lp_rs
        f2 -= Ln_rs

        # Solve 2x2 linear system J * d = -f
        det = j11 * j22 - j12 * j21
        if abs(det) < EPS:
            break
        dcp = (-j22 * f1 + j12 * f2) / det
        dcm = (j21 * f1 - j11 * f2) / det

        # update with basic damping to keep positivity
        cp = max(cp + dcp, EPS)
        cm = max(cm + dcm, EPS)

        if abs(f1) < TOL_CHI and abs(f2) < TOL_CHI:
            break

    # clamp to avoid runaway values when blocks are near-saturated
    return min(cp, CHI_CAP), min(cm, CHI_CAP)


@njit(cache=True, parallel=True, fastmath=True)
def _solve_all_chi_signed(
    xp_sorted: np.ndarray,
    xm_sorted: np.ndarray,
    starts: np.ndarray,
    Lp: np.ndarray,
    Ln: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Solve (χ^+, χ^−) for every block-pair in parallel.
    """
    B = starts.size - 1
    chi_p = np.zeros((B, B))
    chi_m = np.zeros((B, B))
    for r in prange(B):
        a0, a1 = starts[r], starts[r + 1]
        for s in range(r, B):
            b0, b1 = starts[s], starts[s + 1]
            cp, cm = _chi2_newton_slice(
                xp_sorted,
                xm_sorted,
                a0,
                a1,
                b0,
                b1,
                Lp[r, s],
                Ln[r, s],
                r == s,
                1.0,
                1.0,
            )
            chi_p[r, s] = chi_p[s, r] = cp
            chi_m[r, s] = chi_m[s, r] = cm
    return chi_p, chi_m


def _chi_from_partition_and_x_signed(
    Ap: np.ndarray, An: np.ndarray, c: np.ndarray, xp: np.ndarray, xm: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Given fixed (x^+, x^−) and labels c, solve (χ^+, χ^−) for all block pairs.
    """
    Lp_obs, Ln_obs = _build_L_obs_signed(Ap, An, c)
    xp_s, xm_s, starts = _group_by_comm_both(xp, xm, c)
    chi_p, chi_m = _solve_all_chi_signed(xp_s, xm_s, starts, Lp_obs, Ln_obs)
    return chi_p, chi_m


def _bic_signed_dcSBM(
    Ap: np.ndarray,
    An: np.ndarray,
    xp: np.ndarray,
    xm: np.ndarray,
    comm_dict: Dict[int, int],
    chi_p: Optional[np.ndarray] = None,
    chi_m: Optional[np.ndarray] = None,
) -> float:
    """
    BIC for signed dcSBM:
      κ = 2N + B(B+1),   V = N(N−1)/2
      BIC = κ*log(V) − 2*logL
    """
    N = Ap.shape[0]
    c = np.fromiter((comm_dict[i] for i in range(N)), dtype=np.int64)
    B = c.max() + 1

    if chi_p is None or chi_m is None:
        chi_p, chi_m = _chi_from_partition_and_x_signed(Ap, An, c, xp, xm)

    logL = _loglik_signed_dcSBM(Ap, An, xp, xm, c, chi_p, chi_m)
    kappa = 2 * N + (B * (B + 1))
    V = N * (N - 1) / 2.0
    return kappa * math.log(V) - 2.0 * logL


class Signed_DC_BIC_Quality:
    """Leiden quality = −BIC for the signed degree-corrected SBM."""

    def __init__(self, Ap: np.ndarray, An: np.ndarray, xp: np.ndarray, xm: np.ndarray):
        self.Ap, self.An = Ap, An
        self.xp, self.xm = xp, xm

    def __call__(self, part):
        return -_bic_signed_dcSBM(
            self.Ap, self.An, self.xp, self.xm, _part2dict(part.flatten())
        )

    def delta(self, part, v, target):
        old = self.__call__(part)
        new = copy(part).move_node(v, target)
        return self.__call__(new) - old


def leiden_signed_dcSBM(
    G: nx.Graph,
    Ap: np.ndarray,
    An: np.ndarray,
    xp: np.ndarray,
    xm: np.ndarray,
    *,
    initial=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
):
    """
    One Leiden pass maximizing −BIC for the signed dcSBM.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "Leiden (sdcSBM): starting a pass (theta=%.3f, gamma=%.3f)", theta, gamma
        )

    return LeidenEngine.run(
        G,
        Signed_DC_BIC_Quality(Ap, An, xp, xm),
        initial,
        theta,
        gamma,
        random_state=random_state,
        verbose=verbose,
    )


def iterative_leiden_sdcSBM(
    G: nx.Graph,
    Apos: np.ndarray,
    Aneg: np.ndarray,
    *,
    initial_partition=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    max_outer: int = 10,
    do_macro_merge: bool = False,
    target_K: Optional[int] = None,
    fix_x_scm: bool = True,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
) -> Tuple[Partition, float]:
    """
    Multi-pass Leiden for the *signed* dcSBM, alternating community moves
    with re-estimation of (x^+, x^−) & (χ^+, χ^−).

    Bootstrapping of (x^+, x^−):
      • If fix_x_scm=True (default): run a single SCM solve and keep (x^+, x^−) frozen.
      • Otherwise: re-estimate all parameters each outer iteration with the full solver.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "iterative_leiden_sdcSBM: start (max_outer=%d, do_macro_merge=%s, target_K=%s, fix_x_scm=%s)",
            max_outer,
            do_macro_merge,
            str(target_K),
            fix_x_scm,
        )

    # 0) Bootstrap x^+, x^− from SCM
    k_plus = Apos.sum(axis=1)
    k_minus = Aneg.sum(axis=1)

    m_plus = Apos.sum() / 2.0
    m_minus = Aneg.sum() / 2.0

    # conservative positive initial guesses
    x0_plus = np.maximum(k_plus, EPS) / max(1.0, math.sqrt(2.0 * max(m_plus, 1.0)))
    x0_minus = np.maximum(k_minus, EPS) / max(1.0, math.sqrt(2.0 * max(m_minus, 1.0)))

    xp, xm, _ = solve_SCM_iterative(
        k_plus,
        k_minus,
        x0_plus,
        x0_minus,
        # leave defaults for tol/max_iter/patience; centralized in solver
        verbose=False,
    )

    # 1) First Leiden pass
    qf = Signed_DC_BIC_Quality(Apos, Aneg, xp, xm)
    part = leiden_signed_dcSBM(
        G,
        Apos,
        Aneg,
        xp,
        xm,
        initial=initial_partition,
        theta=theta,
        gamma=gamma,
        random_state=random_state,
        verbose=verbose,
    )
    if do_macro_merge:
        part = macro_merge_partition(part, qf)
    if target_K is not None:
        part = _enforce_target_K_exact_sSBM(
            part, G, Apos, Aneg, target_K, theta, gamma, random_state, verbose
        )
    flat = part.flatten()

    # EARLY STOP when initializer unchanged
    if initial_partition is not None:
        init_flat = Partition.from_partition(G, initial_partition).flatten()
        if flat == init_flat:
            # With fixed x, compute chi and BIC right away
            c = np.empty(Apos.shape[0], dtype=int)
            for r, comm in enumerate(flat):
                for v in comm:
                    c[v] = r
            chi_p, chi_m = _chi_from_partition_and_x_signed(Apos, Aneg, c, xp, xm)
            bic0 = _bic_signed_dcSBM(Apos, Aneg, xp, xm, _part2dict(flat), chi_p)
            print("[sdcSBM] Early stop: partition unchanged after first pass.")
            if verbose:
                logger.info(
                    "[sdcSBM] Early stop: partition unchanged after first pass (BIC=%.2f).",
                    bic0,
                )
            return copy(flat), bic0

    best_part = None
    best_bic = float("inf")

    # 2) Outer loop
    for it in range(1, max_outer + 1):
        # labels for current partition
        c = np.empty(Apos.shape[0], dtype=int)
        for r, comm in enumerate(flat):
            for v in comm:
                c[v] = r

        if fix_x_scm:
            # Fixed (x^+, x^−): update only (χ^+, χ^−)
            chi_p, chi_m = _chi_from_partition_and_x_signed(Apos, Aneg, c, xp, xm)
            xp_ref, xm_ref = xp, xm
        else:
            # Full solve: (x^+, x^−, χ^+, χ^−)
            Lp_obs, Ln_obs = _build_L_obs_signed(Apos, Aneg, c)
            R = c.max() + 1
            M = R * (R + 1) // 2
            # flat parameter vector: [x+, x-, chi+_flat, chi-_flat]
            u0 = np.concatenate(
                [
                    np.maximum(xp, EPS),
                    np.maximum(xm, EPS),
                    np.ones(M),
                    np.ones(M),
                ]
            )
            u_opt, _ = solve_signed_dcSBM_iterative(
                k_plus=k_plus,
                k_minus=k_minus,
                c=c,
                Lp_obs=Lp_obs,
                Ln_obs=Ln_obs,
                u_init=u0,
                method="lm",
                tol=TOL_SIGNED_DCSBM,
                max_iter=MAX_IT_DEFAULT,
                patience=PATIENCE_DEFAULT,
                verbose=False,
            )
            xp_ref = u_opt[: Apos.shape[0]]
            xm_ref = u_opt[Apos.shape[0] : 2 * Apos.shape[0]]
            chi_p = np.zeros((R, R))
            chi_m = np.zeros((R, R))
            flat_plus = u_opt[2 * Apos.shape[0] : 2 * Apos.shape[0] + M]
            flat_minus = u_opt[2 * Apos.shape[0] + M : 2 * Apos.shape[0] + 2 * M]
            # unpack flats
            idx = 0
            for r in range(R):
                for s in range(r, R):
                    chi_p[r, s] = chi_p[s, r] = flat_plus[idx]
                    chi_m[r, s] = chi_m[s, r] = flat_minus[idx]
                    idx += 1

        # evaluate BIC
        bic_val = _bic_signed_dcSBM(Apos, Aneg, xp_ref, xm_ref, _part2dict(flat), chi_p)
        if bic_val < best_bic:
            best_bic, best_part = bic_val, copy(flat)
        msg = f"[sdcSBM] iter {it}: BIC={bic_val:.2f}, communities={len(flat)}"
        print(msg)
        if verbose:
            logger.info(msg)

        # next Leiden pass
        qf = Signed_DC_BIC_Quality(Apos, Aneg, xp_ref, xm_ref)
        part_next = leiden_signed_dcSBM(
            G,
            Apos,
            Aneg,
            xp_ref,
            xm_ref,
            initial=flat,
            theta=theta,
            gamma=gamma,
            random_state=random_state,
            verbose=verbose,
        )
        if do_macro_merge:
            part_next = macro_merge_partition(part_next, qf)
        if target_K is not None:
            part_next = _enforce_target_K_exact_sSBM(
                part_next, G, Apos, Aneg, target_K, theta, gamma, random_state, verbose
            )
        flat_next = part_next.flatten()

        if flat_next == flat:
            print("[sdcSBM] Converged (stable partition).")
            if verbose:
                logger.info("[sdcSBM] Converged (stable partition).")
            break

        flat = flat_next
        xp = xp_ref
        xm = xm_ref

    # --- Post-hoc exact BIC (when x was frozen) -----------------------------
    if fix_x_scm and best_part is not None:
        flat_final = best_part
        c = np.empty(Apos.shape[0], dtype=int)
        for r, comm in enumerate(flat_final):
            for v in comm:
                c[v] = r

        Lp_obs, Ln_obs = _build_L_obs_signed(Apos, Aneg, c)
        R = c.max() + 1
        M = R * (R + 1) // 2
        u0 = np.concatenate(
            [
                np.maximum(xp, EPS),
                np.maximum(xm, EPS),
                np.ones(M),
                np.ones(M),
            ]
        )

        tol_solver = TOL_SIGNED_DCSBM
        u_opt, best_norm = solve_signed_dcSBM_iterative(
            k_plus=k_plus,
            k_minus=k_minus,
            c=c,
            Lp_obs=Lp_obs,
            Ln_obs=Ln_obs,
            u_init=u0,
            method="lm",
            tol=tol_solver,
            max_iter=MAX_IT_DEFAULT,
            patience=PATIENCE_DEFAULT,
            verbose=False,
        )
        if best_norm < tol_solver:
            xp_hat = u_opt[: Apos.shape[0]]
            xm_hat = u_opt[Apos.shape[0] : 2 * Apos.shape[0]]
            chi_p = np.zeros((R, R))
            chi_m = np.zeros((R, R))
            flat_plus = u_opt[2 * Apos.shape[0] : 2 * Apos.shape[0] + M]
            flat_minus = u_opt[2 * Apos.shape[0] + M : 2 * Apos.shape[0] + 2 * M]
            idx = 0
            for r in range(R):
                for s in range(r, R):
                    chi_p[r, s] = chi_p[s, r] = flat_plus[idx]
                    chi_m[r, s] = chi_m[s, r] = flat_minus[idx]
                    idx += 1

            true_bic = _bic_signed_dcSBM(
                Apos, Aneg, xp_hat, xm_hat, _part2dict(flat_final), chi_p
            )
            print(f"[sdcSBM] Post-hoc full-parameter BIC (exact): {true_bic:.2f}")
            if verbose:
                logger.info(
                    "[sdcSBM] Post-hoc full-parameter BIC (exact): %.2f", true_bic
                )
            best_bic = true_bic
        else:
            print(
                f"[sdcSBM] Post-hoc solver did not converge "
                f"Keeping fixed-x BIC={best_bic:.2f}."
            )
            if verbose:
                logger.warning(
                    "[sdcSBM] Post-hoc solver did not converge; keeping fixed-x BIC=%.2f.",
                    best_bic,
                )
        return flat_final, best_bic

    return best_part if best_part is not None else flat, best_bic
