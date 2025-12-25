"""
weighted_bic.py

Community detection powered by the Leiden algorithm with BIC minimization
for *weighted* (non-signed) graphs under the maximum-entropy (geometric) model.

Models supported
----------------
  • wSBM   (Weighted Stochastic Block Model; shared z per block-pair)
  • wdcSBM (Weighted Degree-Corrected SBM; node x_i and block χ_{rs})

Likelihood (geometric) and BIC
------------------------------
For each dyad (i,j), with  z_ij > 0  and  p_ij = z_ij / (1 + z_ij),

  log L = ∑_{i<j} [ w_ij log z_ij − (w_ij + 1) log(1 + z_ij) ],
  BIC   = k log V − 2 log L,  with  V = N(N−1)/2.

• wSBM:    z_ij = z_{c_i,c_j};                      k = B(B+1)/2.
• wdcSBM:  z_ij = x_i x_j χ_{c_i,c_j};              k = N + B(B+1)/2.

Structure & Reproducibility
---------------------------
This mirrors the binary/signed BIC modules:
  • quality classes that return −BIC for Leiden
  • iterative Leiden loops (optional macro merges, optional target-K)
  • for wdcSBM: a fixed-x outer loop (from WCM) with post-hoc full solve

• `random_state` (int, np.random.Generator, or random.Random) is forwarded to
  the Leiden engine for deterministic shuffles/tie-breaks.
• `verbose` toggles INFO-level progress messages via the module logger.
• Numeric constants live in `utils/constants.py`. Numba threads are set from $THREADS.
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
from numba import njit, set_num_threads

from ..ergms_solvers.weighted_solvers import (
    solve_WCM_iterative,
    solve_wdcSBM_iterative,
)
from ..leiden.leiden_engine import (
    LeidenEngine,
    macro_merge_partition,
    merge_communities,
)
from ..leiden.partitions_functions import Partition

# Centralized numeric constants
from ..utils.constants import (
    EPS,  # 1e-12
    MAX_IT_DEFAULT,  # 1000
    PATIENCE_DEFAULT,  # 10
    TOL_WDCSBM,  # 1e-6 (default tol for weighted dcSBM solver)
    Z_MIN,  # 1e-12 (lower bound for z = x_i x_j [χ_rs])
)

# Optional logging helpers (safe no-ops if caller already configured logging)
from ..utils.repro import configure_logging

# -----------------------------------------------------------------------------
# Module logger & threads
# -----------------------------------------------------------------------------
logger = logging.getLogger("domino.bic.weighted")

N_THREADS = max(1, int(os.getenv("THREADS", os.cpu_count() or 1)))
set_num_threads(N_THREADS)


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
def _part2dict(part: Partition) -> Dict[int, int]:
    """Flatten a Partition into {node → community}."""
    mapping: Dict[int, int] = {}
    for cid, block in enumerate(part):
        for v in block:
            mapping[v] = cid
    return mapping


# ---- Weighted block sums L_obs (upper triangle semantics) -------------------
def _build_L_obs_weighted(A: np.ndarray, c: np.ndarray) -> np.ndarray:
    """
    Build observed *weight sums* per community pair:
      - Only i<j (upper triangle) are counted once.
      - Off-diagonals filled symmetrically.
      - Diagonals sum within-block (i<j) weights once.

    Returns L_obs (R,R) with L_obs[r,s] = L_obs[s,r], diag already halved correctly.
    """
    R = int(c.max()) + 1
    L = np.zeros((R, R), dtype=float)

    iu, ju = np.triu_indices_from(A, k=1)
    w = A[iu, ju]
    nz = w != 0
    iu = iu[nz]
    ju = ju[nz]
    w = w[nz]
    ci = c[iu]
    cj = c[ju]
    same = ci == cj
    if np.any(same):
        np.add.at(L, (ci[same], cj[same]), w[same])  # ci==cj → diagonal
    diff = ~same
    if np.any(diff):
        np.add.at(L, (ci[diff], cj[diff]), w[diff])
        np.add.at(L, (cj[diff], ci[diff]), w[diff])
    return L


# -----------------------------------------------------------------------------
# Target-K greedy enforcement under wSBM
#   (merge-only, identical structure to binary, but using weight totals)
# -----------------------------------------------------------------------------


@njit(cache=True, fastmath=True)
def _ll_pair_wgeom(L_rs: float, M_rs: int) -> float:
    """
    Block-pair geometric log-likelihood at MLE ẑ = L/M.
      For z > 0:  L log z − (L + M) log(1 + z)
      With ẑ = L/M: interpret L=0 special case → contribution 0.
    """
    if M_rs <= 0:
        return 0.0
    if L_rs <= 0.0:
        return 0.0
    z = L_rs / M_rs
    if z < Z_MIN:
        z = Z_MIN
    return L_rs * math.log(z) - (L_rs + M_rs) * math.log(1.0 + z)


@njit(cache=True, fastmath=True)
def _delta_ll_merge_wsbm(L: np.ndarray, n: np.ndarray, r: int, s: int) -> float:
    """
    Change in wSBM log-likelihood if we merge communities r and s into r.
    Uses only block weight totals L and sizes n (to get M_rs).
    """
    B = n.size
    nr, ns = int(n[r]), int(n[s])

    def M_rr(nr_):
        return nr_ * (nr_ - 1) // 2

    def M_rs(nr_, ns_):
        return nr_ * ns_

    ll_old = 0.0
    ll_old += _ll_pair_wgeom(L[r, r], M_rr(nr))
    ll_old += _ll_pair_wgeom(L[s, s], M_rr(ns))
    ll_old += _ll_pair_wgeom(L[r, s], M_rs(nr, ns))
    for q in range(B):
        if q == r or q == s:
            continue
        ll_old += _ll_pair_wgeom(L[r, q], M_rs(nr, n[q]))
        ll_old += _ll_pair_wgeom(L[s, q], M_rs(ns, n[q]))

    nt = nr + ns
    ll_new = 0.0
    lt = L[r, r] + L[s, s] + L[r, s]
    ll_new += _ll_pair_wgeom(lt, M_rr(nt))
    for q in range(B):
        if q == r or q == s:
            continue
        l_tq = L[r, q] + L[s, q]
        ll_new += _ll_pair_wgeom(l_tq, M_rs(nt, n[q]))

    return ll_new - ll_old


@njit(cache=True, fastmath=True)
def _delta_bic_merge_wsbm(
    L: np.ndarray, n: np.ndarray, r: int, s: int, N: int
) -> float:
    """
    ΔBIC when merging (r,s) under wSBM:
      parameters k = B(B+1)/2 ⇒   Δk = −B
      ΔBIC = Δk·log V − 2·ΔlogL  =  (−B)·log V − 2·ΔlogL.
    """
    B = n.size
    V = N * (N - 1) / 2.0
    delta_pen = -B * math.log(V)
    delta_ll = _delta_ll_merge_wsbm(L, n, r, s)
    return delta_pen - 2.0 * delta_ll


def _init_block_stats_from_partition_weighted(A: np.ndarray, part: Partition):
    """
    Build (weighted) block totals L and size vector n for the current partition.
    """
    B = len(part)
    L = np.zeros((B, B), dtype=float)
    n = np.zeros(B, dtype=np.int64)

    idxs: List[np.ndarray] = []
    for cid, C in enumerate(part):
        idx = np.fromiter((int(v) for v in C), dtype=np.int64)
        idxs.append(idx)
        n[cid] = idx.size

    for r in range(B):
        ir = idxs[r]
        if ir.size >= 2:
            sub = A[np.ix_(ir, ir)]
            L[r, r] = float(np.triu(sub, 1).sum())
        for s in range(r + 1, B):
            is_ = idxs[s]
            if ir.size > 0 and is_.size > 0:
                val = float(A[np.ix_(ir, is_)].sum())
                L[r, s] = L[s, r] = val
    return L, n


def _apply_merge_update_stats_weighted(L: np.ndarray, n: np.ndarray, r: int, s: int):
    """
    Update (L, n) after merging s into r (and dropping s).
    """
    B = n.size
    L_rr_new = L[r, r] + L[s, s] + L[r, s]
    for q in range(B):
        if q == r or q == s:
            continue
        L[r, q] += L[s, q]
        L[q, r] = L[r, q]
    L[r, r] = L_rr_new

    L = np.delete(L, s, axis=0)
    L = np.delete(L, s, axis=1)
    n[r] = n[r] + n[s]
    n = np.delete(n, s)
    return L, n


@njit(cache=True, fastmath=True)
def _best_merge_pair_wsbm(L: np.ndarray, n: np.ndarray, N: int):
    B = n.size
    best_i, best_j = -1, -1
    best_delta = 1e300
    for i in range(B - 1):
        for j in range(i + 1, B):
            d = _delta_bic_merge_wsbm(L, n, i, j, N)
            if d < best_delta:
                best_delta = d
                best_i, best_j = i, j
    return best_i, best_j, best_delta


def _enforce_target_K_wSBM(part: Partition, A: np.ndarray, K_target: int) -> Partition:
    """
    Greedy BIC-optimal merges until len(part) == K_target (wSBM model).
    """
    part = part.flatten()
    if len(part) <= K_target:
        return part

    N = A.shape[0]
    L, n = _init_block_stats_from_partition_weighted(A, part)

    while len(part) > K_target:
        i, j, _ = _best_merge_pair_wsbm(L, n, N)
        if i < 0:
            break
        part = merge_communities(part, i, j).flatten()
        L, n = _apply_merge_update_stats_weighted(L, n, i, j)

    return part


# -----------------------------------------------------------------------------
# Exact target-K enforcement (split + merge), mirroring signed/binary modules
# -----------------------------------------------------------------------------
def _split_largest_community_with_leiden_wSBM(
    part: Partition,
    G: nx.Graph,
    A: np.ndarray,
    theta: float,
    gamma: float,
    random_state: Optional[Union[int, np.random.Generator, random.Random]],
    verbose: int | bool = False,
) -> Partition:
    """
    Attempt to increase the number of communities by splitting the largest
    block via a local Leiden pass on the induced subgraph, using wSBM–BIC
    as quality function.

    Steps
    -----
      1. Identify the largest community C in the current partition.
      2. Build the induced weighted adjacency A_C on C and re-index nodes
         locally as 0,...,|C|−1.
      3. Run a fresh Leiden pass on the local graph with wSBM–BIC quality.
      4. If Leiden returns more than one community, replace C with these
         subcommunities (mapped back to global node labels).
      5. If the split does not increase the total number of blocks, return
         the original partition.
    """
    part_flat = part.flatten()
    B = len(part_flat)
    if B == 0:
        return part_flat

    # Largest community index
    sizes = [len(C) for C in part_flat]
    idx_big = int(np.argmax(sizes))
    C_big = list(part_flat[idx_big])
    if len(C_big) <= 1:
        # Cannot split a singleton community
        return part_flat

    # Deterministic ordering
    C_big_sorted = sorted(int(v) for v in C_big)
    n_sub = len(C_big_sorted)

    # Induced weighted adjacency on C_big, local indices 0..n_sub-1
    A_sub = A[np.ix_(C_big_sorted, C_big_sorted)]

    # Local graph with nodes {0,...,n_sub-1}
    G_sub = nx.Graph()
    G_sub.add_nodes_from(range(n_sub))

    iu, ju = np.triu_indices(n_sub, k=1)
    mask = A_sub[iu, ju] != 0
    edges = [(int(i), int(j)) for i, j, ok in zip(iu, ju, mask, strict=False) if ok]
    if not edges:
        # Community is internally edgeless
        return part_flat
    G_sub.add_edges_from(edges)

    # Local wSBM quality on A_sub
    qf_sub = Weighted_SBM_BIC_Quality(A_sub)

    # Local Leiden run (no initializer, we want a fresh proposal)
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
        # No non-trivial split discovered
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

    # Rebuild the full partition: replace C_big with the split blocks
    blocks_new = []
    for b_idx, block in enumerate(part_flat):
        if b_idx == idx_big:
            continue
        blocks_new.append(set(int(v) for v in block))
    blocks_new.extend(new_blocks_big)

    new_part = Partition.from_partition(G, blocks_new)
    return new_part.flatten()


def _enforce_target_K_exact_wSBM(
    part: Partition,
    G: nx.Graph,
    A: np.ndarray,
    K_target: int,
    theta: float,
    gamma: float,
    random_state: Optional[Union[int, np.random.Generator, random.Random]],
    verbose: int | bool = False,
    max_iters: int = 50,
) -> Partition:
    """
    Enforce an exact target number of communities K_target using a combination
    of BIC-optimal merges (wSBM) and local Leiden-based splits, mirroring the
    binary and signed implementations.

    Strategy
    --------
      • If the current number of blocks B is larger than K_target, use the
        merge-only routine `_enforce_target_K_wSBM`, which repeatedly merges
        blocks so as to minimise the increase in BIC under wSBM.

      • If B is smaller than K_target, repeatedly try to increase B by
        splitting the largest block using `_split_largest_community_with_leiden_wSBM`,
        which proposes a finer partition of that community based on a local
        Leiden pass with wSBM–BIC as quality.

      • Whenever a split produces B > K_target, finish by invoking
        `_enforce_target_K_wSBM` once to merge back to exactly K_target blocks.

    The procedure stops either when K_target is reached or when no additional
    non-trivial splits are possible.
    """
    part = part.flatten()
    if K_target is None:
        return part

    # Case B > K_target: merge-only enforcement, already BIC-based.
    if len(part) > K_target:
        return _enforce_target_K_wSBM(part, A, K_target)

    # Case B <= K_target: create new blocks via splits of the largest community.
    it = 0
    while len(part) < K_target and it < max_iters:
        it += 1
        prev_B = len(part)
        part = _split_largest_community_with_leiden_wSBM(
            part, G, A, theta, gamma, random_state, verbose
        )
        B_new = len(part)
        if B_new <= prev_B:
            # No effective split, cannot approach K_target further
            break
        if B_new > K_target:
            # Overshoot: merge back down to K_target
            part = _enforce_target_K_wSBM(part, A, K_target)
            break

    return part


# -----------------------------------------------------------------------------
# wSBM: log-likelihood and BIC
# -----------------------------------------------------------------------------


@njit(cache=True, fastmath=True)
def _wsbm_loglik(A: np.ndarray, comm: np.ndarray, com_sizes: np.ndarray) -> float:
    """
    Geometric wSBM log-likelihood with blockwise MLEs.
    For block pair (r,s):
      L_rs = ∑_{(i<j)∈(r,s)} w_ij,  M_rr = n_r(n_r−1)/2,  M_rs = n_r n_s (r<s).
      With ẑ_rs = L_rs/M_rs, contribution = L_rs log ẑ_rs − (L_rs + M_rs) log(1 + ẑ_rs).
      If L_rs = 0 (or M_rs = 0), contribution is 0.
    """
    B = com_sizes.size
    N = A.shape[0]
    L = np.zeros((B, B), dtype=float)

    for i in range(N):
        ci = comm[i]
        for j in range(i + 1, N):
            w = A[i, j]
            if w != 0:
                cj = comm[j]
                L[ci, cj] += w
                if ci != cj:
                    L[cj, ci] += w

    ll = 0.0
    for r in range(B):
        nr = int(com_sizes[r])
        Mrr = nr * (nr - 1) // 2
        if Mrr > 0 and L[r, r] > 0.0:
            z = L[r, r] / Mrr
            if z < Z_MIN:
                z = Z_MIN
            ll += L[r, r] * math.log(z) - (L[r, r] + Mrr) * math.log(1.0 + z)
        for s in range(r + 1, B):
            Mrs = int(com_sizes[r]) * int(com_sizes[s])
            if Mrs > 0 and L[r, s] > 0.0:
                z = L[r, s] / Mrs
                if z < Z_MIN:
                    z = Z_MIN
                ll += L[r, s] * math.log(z) - (L[r, s] + Mrs) * math.log(1.0 + z)
    return ll


def _bic_wsbm(A: np.ndarray, comm_dict: Dict[int, int]) -> float:
    """
    BIC for geometric wSBM:
      k = B(B+1)/2,  V = N(N−1)/2,  BIC = k log V − 2 log L.
    """
    N = A.shape[0]
    comm = np.empty(N, dtype=np.int64)
    for i in range(N):
        comm[i] = comm_dict[i]
    B = comm.max() + 1
    sizes = np.bincount(comm, minlength=B)

    logL = _wsbm_loglik(A, comm, sizes)
    k = B * (B + 1) // 2
    V = N * (N - 1) / 2.0
    return k * math.log(V) - 2.0 * logL


class Weighted_SBM_BIC_Quality:
    """Leiden quality = −BIC for the geometric wSBM."""

    def __init__(self, A: np.ndarray):
        self.A = A

    def __call__(self, part):
        return -_bic_wsbm(self.A, _part2dict(part.flatten()))

    def delta(self, part, v, target):
        old = self.__call__(part)
        new = copy(part).move_node(v, target)
        return self.__call__(new) - old


def leiden_weighted_sbm(
    G: nx.Graph,
    A: np.ndarray,
    *,
    initial=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
):
    """One Leiden pass maximizing −BIC for geometric wSBM."""
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info("Leiden (wSBM): pass start (theta=%.3f, gamma=%.3f)", theta, gamma)
    return LeidenEngine.run(
        G,
        Weighted_SBM_BIC_Quality(A),
        initial,
        theta,
        gamma,
        random_state=random_state,
        verbose=verbose,
    )


def iterative_leiden_wSBM(
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
    Repeat Leiden passes until no further improvement in BIC (geometric wSBM).
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "iterative_leiden_wSBM: start (max_outer=%d, macro=%s, target_K=%s)",
            max_outer,
            do_macro_merge,
            str(target_K),
        )

    qf = Weighted_SBM_BIC_Quality(A)

    init_flat = None
    if initial_partition is not None:
        init_flat = Partition.from_partition(G, initial_partition).flatten()

    part = leiden_weighted_sbm(
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
        part = _enforce_target_K_exact_wSBM(
            part, G, A, target_K, theta, gamma, random_state, verbose
        )
    flat = part.flatten()

    if init_flat is not None and flat == init_flat:
        bic0 = _bic_wsbm(A, _part2dict(flat))
        print("[wSBM] Early stop: partition unchanged after first pass.")
        if verbose:
            logger.info(
                "[wSBM] Early stop: partition unchanged after first pass (BIC=%.2f).",
                bic0,
            )
        return copy(flat), bic0

    best_part = copy(flat)
    best_bic = _bic_wsbm(A, _part2dict(flat))

    for it in range(1, max_outer + 1):
        msg = f"[wSBM] iter {it}: BIC={best_bic:.2f}, communities={len(flat)}"
        print(msg)
        if verbose:
            logger.info(msg)

        nxt = leiden_weighted_sbm(
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
            nxt = _enforce_target_K_exact_wSBM(
                nxt, G, A, target_K, theta, gamma, random_state, verbose
            )
        flat_next = nxt.flatten()

        if flat_next == flat:
            print("[wSBM] Converged (stable partition).")
            if verbose:
                logger.info("[wSBM] Converged (stable partition).")
            break

        bic_now = _bic_wsbm(A, _part2dict(flat_next))
        if bic_now < best_bic:
            best_bic, best_part = bic_now, copy(flat_next)
        flat = flat_next

    return best_part, best_bic


# -----------------------------------------------------------------------------
# weighted dcSBM: log-likelihood, χ from fixed x, BIC, Leiden loop
# -----------------------------------------------------------------------------


@njit(cache=True, fastmath=True)
def _w_dc_loglik(
    A: np.ndarray, xs: np.ndarray, comm: np.ndarray, chi: np.ndarray
) -> float:
    """
    Geometric weighted dcSBM log-likelihood:
      log L = ∑_{i<j} [ w_ij log z_ij − (w_ij + 1) log(1 + z_ij) ],
      z_ij  = x_i x_j χ_{c_i,c_j}.
    """
    N = A.shape[0]
    ll = 0.0
    for i in range(N):
        xi, ci = xs[i], comm[i]
        for j in range(i + 1, N):
            z = xi * xs[j] * chi[ci, comm[j]]
            if z < Z_MIN:
                z = Z_MIN
            w = A[i, j]
            if w == 0.0:
                ll -= math.log(1.0 + z)
            else:
                ll += w * math.log(z) - (w + 1.0) * math.log(1.0 + z)
    return ll


def _chi_from_partition_and_x_weighted(
    A: np.ndarray, c: np.ndarray, xs: np.ndarray
) -> np.ndarray:
    """
    With geometric weights, χ_{rs} has a *closed form* given x and c:

      Let S_rs = ∑_{(i<j)∈(r,s)} x_i x_j.
      Let L_rs = ∑_{(i<j)∈(r,s)} w_ij.
      Then  E[L_rs] = χ_{rs} S_rs  ⇒  χ̂_{rs} = L_rs / S_rs  (if S_rs>0 else 0).

    This returns a symmetric (R,R) matrix χ̂.
    """
    R = int(c.max()) + 1

    # ---- S_rs via per-community sums (O(N + R^2))
    sum_x = np.bincount(c, weights=xs, minlength=R)
    sum_x2 = np.bincount(c, weights=xs * xs, minlength=R)

    # Off-diagonals: outer product
    S = sum_x[:, None] * sum_x[None, :]

    # Diagonals: 1/2 * (sum_x^2 - sum_x2)
    np.fill_diagonal(S, 0.5 * (sum_x * sum_x - sum_x2))

    # ---- L_rs: aggregate observed weights
    L = _build_L_obs_weighted(A, c)

    # ---- chi = L / S (safe divide), symmetric
    chi = np.zeros((R, R), dtype=float)
    nz = S > 0
    chi[nz] = L[nz] / S[nz]
    return chi


def _bic_w_dcSBM(
    A: np.ndarray,
    xs: np.ndarray,
    comm_dict: Dict[int, int],
    chi: Optional[np.ndarray] = None,
) -> float:
    """
    BIC for geometric weighted dcSBM:
      kappa = N + B(B+1)/2,   V = N(N−1)/2,   BIC = kappa log V − 2 log L.

    If chi is None, compute χ̂ from current (xs, c) in closed form.
    """
    N = A.shape[0]
    comm = np.fromiter((comm_dict[i] for i in range(N)), dtype=np.int64)
    B = comm.max() + 1

    if chi is None:
        chi = _chi_from_partition_and_x_weighted(A, comm, xs)

    logL = _w_dc_loglik(A, xs, comm, chi)
    kappa = N + (B * (B + 1)) // 2
    V = N * (N - 1) / 2.0
    return kappa * math.log(V) - 2.0 * logL


class Weighted_DC_BIC_Quality:
    """Leiden quality = −BIC for the geometric weighted dcSBM."""

    def __init__(self, A: np.ndarray, xs: np.ndarray):
        self.A, self.xs = A, xs

    def __call__(self, part):
        return -_bic_w_dcSBM(self.A, self.xs, _part2dict(part.flatten()))

    def delta(self, part, v, target):
        old = self.__call__(part)
        new = copy(part).move_node(v, target)
        return self.__call__(new) - old


def leiden_weighted_dcSBM(
    G: nx.Graph,
    A: np.ndarray,
    xs: np.ndarray,
    *,
    initial=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
):
    """One Leiden pass maximizing −BIC for the weighted dcSBM."""
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "Leiden (wdcSBM): pass start (theta=%.3f, gamma=%.3f)", theta, gamma
        )
    return LeidenEngine.run(
        G,
        Weighted_DC_BIC_Quality(A, xs),
        initial,
        theta,
        gamma,
        random_state=random_state,
        verbose=verbose,
    )


def iterative_leiden_wdcSBM(
    G: nx.Graph,
    A: np.ndarray,
    *,
    initial_partition=None,
    theta: float = 0.3,
    gamma: float = 0.0,
    max_outer: int = 10,
    do_macro_merge: bool = False,
    target_K: Optional[int] = None,
    fix_x_wcm: bool = True,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    verbose: int | bool = False,
) -> Tuple[Partition, float]:
    """
    Multi-pass Leiden for geometric weighted dcSBM, alternating community moves
    with re-estimation of x & χ.

    Bootstrapping x:
      • If fix_x_wcm=True (default): run a single WCM solve and keep x frozen.
      • Otherwise: re-fit (x, χ) jointly each outer iteration via the residual solver.
    """
    if verbose:
        configure_logging(verbose=bool(verbose))
        logger.info(
            "iterative_leiden_wdcSBM: start (max_outer=%d, macro=%s, target_K=%s, fix_x_wcm=%s)",
            max_outer,
            do_macro_merge,
            str(target_K),
            fix_x_wcm,
        )

    s = A.sum(axis=1)  # node strengths
    W_total = A.sum() / 2.0

    # Initial WCM solve (used both paths; fixed-x path freezes it)
    x0 = np.maximum(s, EPS) / max(1.0, math.sqrt(max(W_total, 1.0)))
    xs, _ = solve_WCM_iterative(s, x0)

    # First Leiden pass
    qf = Weighted_DC_BIC_Quality(A, xs)
    part = leiden_weighted_dcSBM(
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
        part = _enforce_target_K_exact_wSBM(
            part, G, A, target_K, theta, gamma, random_state, verbose
        )
    flat = part.flatten()

    # Early stop when initializer unchanged
    if initial_partition is not None:
        init_flat = Partition.from_partition(G, initial_partition).flatten()
        if flat == init_flat:
            c = np.empty(A.shape[0], dtype=int)
            for r, comm in enumerate(flat):
                for v in comm:
                    c[v] = r
            chi = _chi_from_partition_and_x_weighted(A, c, xs)
            bic0 = _bic_w_dcSBM(A, xs, _part2dict(flat), chi)
            print("[wdcSBM] Early stop: partition unchanged after first pass.")
            if verbose:
                logger.info(
                    "[wdcSBM] Early stop: partition unchanged after first pass (BIC=%.2f).",
                    bic0,
                )
            return copy(flat), bic0

    best_part = None
    best_bic = float("inf")

    for it in range(1, max_outer + 1):
        # labels
        c = np.empty(A.shape[0], dtype=int)
        for r, comm in enumerate(flat):
            for v in comm:
                c[v] = r

        if fix_x_wcm:
            # fixed x: closed-form χ̂
            chi = _chi_from_partition_and_x_weighted(A, c, xs)
            xs_ref = xs
        else:
            # full residual solve for (x, χ)
            L_obs = _build_L_obs_weighted(A, c)
            R = c.max() + 1
            M = R * (R + 1) // 2
            u0 = np.concatenate([np.maximum(xs, EPS), np.ones(M)])
            u_opt, _ = solve_wdcSBM_iterative(
                s=s,
                c=c,
                L_obs=L_obs,
                u_init=u0,
                method="lm",
                tol=TOL_WDCSBM,
                max_iter=MAX_IT_DEFAULT,
                patience=PATIENCE_DEFAULT,
                verbose=False,
            )
            xs_ref = u_opt[: A.shape[0]]
            chi_flat = u_opt[A.shape[0] :]
            chi = np.zeros((R, R))
            idx = 0
            for r in range(R):
                for s_ in range(r, R):
                    chi[r, s_] = chi[s_, r] = chi_flat[idx]
                    idx += 1

        bic_val = _bic_w_dcSBM(A, xs_ref, _part2dict(flat), chi)
        if bic_val < best_bic:
            best_bic, best_part = bic_val, copy(flat)
        msg = f"[wdcSBM] iter {it}: BIC={bic_val:.2f}, communities={len(flat)}"
        print(msg)
        if verbose:
            logger.info(msg)

        qf = Weighted_DC_BIC_Quality(A, xs_ref)
        part_next = leiden_weighted_dcSBM(
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
            part_next = _enforce_target_K_exact_wSBM(
                part_next, G, A, target_K, theta, gamma, random_state, verbose
            )
        flat_next = part_next.flatten()

        if flat_next == flat:
            print("[wdcSBM] Converged (stable partition).")
            if verbose:
                logger.info("[wdcSBM] Converged (stable partition).")
            break

        flat = flat_next
        xs = xs_ref

    # --- Post-hoc exact BIC (when x was frozen) -----------------------------
    if fix_x_wcm and best_part is not None:
        flat_final = best_part
        c = np.empty(A.shape[0], dtype=int)
        for r, comm in enumerate(flat_final):
            for v in comm:
                c[v] = r

        L_obs = _build_L_obs_weighted(A, c)
        R = c.max() + 1
        M = R * (R + 1) // 2
        u0 = np.concatenate([np.maximum(xs, EPS), np.ones(M)])

        tol_solver = TOL_WDCSBM
        u_opt, best_norm = solve_wdcSBM_iterative(
            s=s,
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
            chi_hat = np.zeros((R, R))
            idx = 0
            for r in range(R):
                for s_ in range(r, R):
                    chi_hat[r, s_] = chi_hat[s_, r] = u_opt[A.shape[0] + idx]
                    idx += 1
            true_bic = _bic_w_dcSBM(A, x_hat, _part2dict(flat_final), chi_hat)
            print(f"[wdcSBM] Post-hoc full-parameter BIC (exact): {true_bic:.2f}")
            if verbose:
                logger.info(
                    "[wdcSBM] Post-hoc full-parameter BIC (exact): %.2f", true_bic
                )
            best_bic = true_bic
        else:
            print(
                f"[wdcSBM] Post-hoc solver did not converge "
                f"Keeping fixed-x BIC={best_bic:.2f}."
            )
            if verbose:
                logger.warning(
                    "[wdcSBM] Post-hoc solver did not converge; keeping fixed-x BIC=%.2f.",
                    best_bic,
                )

    return best_part if best_part is not None else flat, best_bic
