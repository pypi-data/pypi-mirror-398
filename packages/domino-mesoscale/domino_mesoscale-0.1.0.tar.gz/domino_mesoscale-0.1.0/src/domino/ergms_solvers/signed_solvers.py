"""
signed_solvers.py

Solvers for *signed* Exponential Random Graph Models (ERGMs):

  • SCM   (Signed Configuration Model; UBCM-equivalent for signed graphs)
  • signed dcSBM (degree-corrected SBM with positive/negative layers)

Each solver provides a residual function and an iterative root-finding routine
with a patience mechanism. Log-parameters are used internally to enforce
positivity of all factors.

Conventions
-----------
We model a binary signed, undirected network with dyads in three states:
  +1 (positive edge), -1 (negative edge), 0 (no edge).
We use:
  - k_plus[i],  k_minus[i]   : observed +/− degrees per node
  - Lp_obs[r,s], Ln_obs[r,s] : observed +/− link counts per block pair (r ≤ s)
  - x_plus[i],  x_minus[i]   : node degree-correction factors for +/−
  - chi_plus[r,s], chi_minus[r,s] : block affinities for +/−

The trinomial probabilities for a dyad (i,j) in blocks r=c[i], s=c[j] are
  p^+_ij = (x^+_i x^+_j χ^+_{rs}) / (1 + x^+_i x^+_j χ^+_{rs} + x^-_i x^-_j χ^-_{rs})
  p^-_ij = (x^-_i x^-_j χ^-_{rs}) / (1 + x^+_i x^+_j χ^+_{rs} + x^-_i x^-_j χ^-_{rs})
  p^0_ij = 1 - p^+_ij - p^-_ij
"""

from __future__ import annotations

import logging
import warnings
from typing import Tuple

import numpy as np
from numba import get_num_threads, njit, prange
from scipy.optimize import OptimizeWarning, newton_krylov, root

# ---------------------------------------------------------------------------
# Centralized numeric constants (keep behavior consistent across modules)
# ---------------------------------------------------------------------------
from ..utils.constants import (
    EPS,  # universal small epsilon (e.g., 1e-12)
    MAX_IT_DEFAULT,  # outer-loop max iterations (e.g., 1000)
    PATIENCE_DEFAULT,  # early-stop patience (e.g., 10)
    TOL_SIGNED_DCSBM,  # default residual tolerance for signed dcSBM (e.g., 1e-6)
    TOL_SIGNED_SCM,  # default residual tolerance for SCM (e.g., 1e-9)
)

# ---------------------------------------------------------------------------
# WARNING SUPPRESSION
# ---------------------------------------------------------------------------
# Silence non-critical SciPy optimization warnings. Users can enable the
# module logger to monitor progress instead of raw warning spam.
warnings.simplefilter("ignore", OptimizeWarning)

# Module-level logger (configure handlers/level once in your application)
logger = logging.getLogger("domino.ergms.signed")


# ---------------------------------------------------------------------------
# Helper: block-pair structure (same semantics as in the binary solvers)
# ---------------------------------------------------------------------------
def _make_block_struct(c: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build block-pair list and index map for communities.

    Parameters
    ----------
    c : np.ndarray, shape (N,)
        Community labels for each node.

    Returns
    -------
    block_pairs : np.ndarray, shape (M, 2)
        Array of unordered pairs (r, s) with r <= s.
    idx_map : np.ndarray, shape (R, R)
        Mapping matrix where idx_map[r, s] gives index into block_pairs.
        Symmetric by construction (idx_map[s, r] == idx_map[r, s]).
    """
    R = int(c.max()) + 1
    pairs = [(r, s) for r in range(R) for s in range(r, R)]
    block_pairs = np.array(pairs, dtype=np.int64)
    idx_map = -np.ones((R, R), dtype=np.int64)
    for idx, (r, s) in enumerate(pairs):
        idx_map[r, s] = idx
        idx_map[s, r] = idx
    return block_pairs, idx_map


# ===========================================================================
# 1) Signed UBCM-equivalent (SCM): node-only +/− factors
# ===========================================================================


@njit(cache=True, fastmath=True)
def _residuals_SCM_log(
    u: np.ndarray, k_plus: np.ndarray, k_minus: np.ndarray
) -> np.ndarray:
    """
    SCM residuals in log-space (x^+ = exp(u[:N]), x^- = exp(u[N:])).
    No NxN matrix is allocated; computation is O(N^2) with tight loops.

    For each node i:
      res_plus[i]  = sum_{j!=i} p^+_{ij} - k_plus[i]
      res_minus[i] = sum_{j!=i} p^-_{ij} - k_minus[i]

    We concatenate these to produce a residual vector of length 2N.

    Parameters
    ----------
    u : np.ndarray, shape (2N,)
        Log-parameters: first N entries for x^+, next N for x^-.
    k_plus, k_minus : np.ndarray, shape (N,)
        Observed positive and negative degrees.

    Returns
    -------
    np.ndarray, shape (2N,)
        Residual vector (expected minus observed).
    """
    N = k_plus.size
    xp = np.exp(u[:N])  # x^+ (positive layer)
    xm = np.exp(u[N : 2 * N])  # x^- (negative layer)

    res = np.empty(2 * N)
    for i in range(N):
        xpi = xp[i]
        xmi = xm[i]
        sp = 0.0
        sm = 0.0
        for j in range(N):
            if j == i:
                continue
            denom = 1.0 + xpi * xp[j] + xmi * xm[j]
            sp += (xpi * xp[j]) / denom
            sm += (xmi * xm[j]) / denom
        res[i] = sp - k_plus[i]
        res[N + i] = sm - k_minus[i]
    return res


def solve_SCM_iterative(
    k_plus: np.ndarray,
    k_minus: np.ndarray,
    x_plus_init: np.ndarray,
    x_minus_init: np.ndarray,
    method: str = "lm",
    tol: float = TOL_SIGNED_SCM,
    max_iter: int = MAX_IT_DEFAULT,
    patience: int = PATIENCE_DEFAULT,
    verbose: int | bool = False,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Solve the Signed Configuration Model (SCM) in log-space to enforce positivity.

    The routine maintains the best iterate by residual 2-norm and stops early
    when no improvement is observed for `patience` iterations.

    Parameters
    ----------
    k_plus, k_minus : (N,)
        Observed +/− degrees.
    x_plus_init, x_minus_init : (N,)
        Positive initial guesses for node factors (floored by EPS for logs).
    method : {'lm','hybr','krylov'}
        SciPy root-finder ('krylov' uses `newton_krylov(lgmres)`).
    tol : float
        Target residual 2-norm tolerance.
    max_iter : int
        Maximum number of outer iterations (patience loop).
    patience : int
        Early-stop if residual norm fails to improve for this many iterations.
    verbose : int | bool
        If truthy, emit INFO-level progress logs.

    Returns
    -------
    x_plus, x_minus : (N,), (N,)
        Optimized node factors for positive and negative layers.
    best_norm : float
        Residual 2-norm at the best iterate.
    """
    if verbose:
        logger.info(
            "SCM: starting solve (method=%s, tol=%.1e, max_iter=%d, patience=%d)",
            method,
            tol,
            max_iter,
            patience,
        )

    N = k_plus.size
    # Guarded initialization to keep logs finite
    z0 = np.concatenate(
        [
            np.log(np.maximum(x_plus_init, EPS)),
            np.log(np.maximum(x_minus_init, EPS)),
        ]
    )

    best_u = z0.copy()
    best_norm = np.linalg.norm(_residuals_SCM_log(best_u, k_plus, k_minus))
    no_improve = 0

    for it in range(max_iter):
        # One nonlinear step
        if method == "krylov":
            u_curr = newton_krylov(
                lambda uu: _residuals_SCM_log(uu, k_plus, k_minus),
                z0,
                method="lgmres",
                inner_maxiter=100,
            )
        else:
            sol = root(
                lambda uu: _residuals_SCM_log(uu, k_plus, k_minus),
                x0=z0,
                method=method,
                options={"maxfev": 10000},
            )
            u_curr = sol.x

        curr = np.linalg.norm(_residuals_SCM_log(u_curr, k_plus, k_minus))

        # Keep best
        if curr < best_norm:
            best_norm = curr
            best_u = u_curr.copy()
            no_improve = 0
        else:
            no_improve += 1

        if verbose:
            logger.info(
                "SCM: iter=%d  ||res||=%.3e  best=%.3e  no_improve=%d",
                it + 1,
                curr,
                best_norm,
                no_improve,
            )

        # Stopping conditions
        if curr < tol:
            best_u = u_curr.copy()
            if verbose:
                logger.info("SCM: converged at iter %d with ||res||=%.3e", it + 1, curr)
            break
        if no_improve >= patience:
            logger.warning(
                "SCM solver: stopping after %d no-improve iterations at iter %d.",
                patience,
                it + 1,
            )
            break
        if it == max_iter - 1:
            logger.warning("SCM solver: maximum iterations reached before convergence.")

        # Warm start next step
        z0 = u_curr.copy()

    xp = np.exp(best_u[:N])
    xm = np.exp(best_u[N : 2 * N])
    return xp, xm, best_norm


# ===========================================================================
# 2) Signed dcSBM: node +/− factors and block +/− affinities
# ===========================================================================


@njit(parallel=True, fastmath=True)
def _residuals_signed_dcSBM_log(
    u: np.ndarray,
    k_plus: np.ndarray,
    k_minus: np.ndarray,
    c: np.ndarray,
    Lp_obs: np.ndarray,
    Ln_obs: np.ndarray,
    block_pairs: np.ndarray,
    idx_map: np.ndarray,
) -> np.ndarray:
    """
    Parallel residuals for signed dcSBM in log-parameter space using per-thread
    accumulators and explicit reduction (no atomics). Evaluation is deterministic
    w.r.t. the thread count and static tiling strategy.

    Parameter packing (all in logs):
        u[0:N]            -> x_plus (N)
        u[N:2N]           -> x_minus (N)
        u[2N:2N+M]        -> chi_plus_flat (M)   for unordered (r ≤ s)
        u[2N+M:2N+2M]     -> chi_minus_flat (M)

    Residual vector of length 2N + 2M:
      - first  N:  ∑_j p^+_{ij} - k_plus[i]
      - next   N:  ∑_j p^-_{ij} - k_minus[i]
      - next   M:  ∑_{(i<j)∈(r,s)} p^+_{ij} - Lp_obs[r,s]
      - last   M:  ∑_{(i<j)∈(r,s)} p^-_{ij} - Ln_obs[r,s]

    Returns
    -------
    np.ndarray, shape (2N + 2M)
        Concatenated residuals for node-level and block-level constraints.
    """
    N = k_plus.size
    M = block_pairs.shape[0]

    xp = np.exp(u[:N])  # x^+ node factors
    xm = np.exp(u[N : 2 * N])  # x^- node factors
    cp = np.exp(u[2 * N : 2 * N + M])  # χ^+ (flat)
    cm = np.exp(u[2 * N + M : 2 * N + 2 * M])  # χ^- (flat)

    T = get_num_threads()

    degp_local = np.zeros((T, N))
    degm_local = np.zeros((T, N))
    blkp_local = np.zeros((T, M))
    blkm_local = np.zeros((T, M))

    base = N // T
    rem = N % T

    for t in prange(T):
        i0 = t * base + (t if t < rem else rem)
        i1 = i0 + base + (1 if t < rem else 0)
        if i0 >= i1:
            continue

        dp = degp_local[t]
        dm = degm_local[t]
        bp = blkp_local[t]
        bm = blkm_local[t]

        for i in range(i0, i1):
            xpi = xp[i]
            xmi = xm[i]
            ci = c[i]
            for j in range(i + 1, N):
                cj = c[j]
                idx = idx_map[ci, cj]
                zpi = xpi * xp[j] * cp[idx]
                zmi = xmi * xm[j] * cm[idx]
                denom = 1.0 + zpi + zmi
                pp = zpi / denom
                pm = zmi / denom

                dp[i] += pp
                dm[i] += pm
                dp[j] += pp
                dm[j] += pm
                bp[idx] += pp
                bm[idx] += pm

    # Reduction
    degp = np.zeros(N)
    degm = np.zeros(N)
    blkp = np.zeros(M)
    blkm = np.zeros(M)
    for t in range(T):
        for i in range(N):
            degp[i] += degp_local[t, i]
            degm[i] += degm_local[t, i]
        for m in range(M):
            blkp[m] += blkp_local[t, m]
            blkm[m] += blkm_local[t, m]

    # Assemble residual vector
    res = np.empty(2 * N + 2 * M)
    for i in range(N):
        res[i] = degp[i] - k_plus[i]
        res[N + i] = degm[i] - k_minus[i]
    for m in range(M):
        r = block_pairs[m, 0]
        s = block_pairs[m, 1]
        res[2 * N + m] = blkp[m] - Lp_obs[r, s]
        res[2 * N + M + m] = blkm[m] - Ln_obs[r, s]
    return res


def solve_signed_dcSBM_iterative(
    k_plus: np.ndarray,
    k_minus: np.ndarray,
    c: np.ndarray,
    Lp_obs: np.ndarray,
    Ln_obs: np.ndarray,
    u_init: np.ndarray,
    method: str = "lm",
    tol: float = TOL_SIGNED_DCSBM,
    max_iter: int = MAX_IT_DEFAULT,
    patience: int = PATIENCE_DEFAULT,
    verbose: int | bool = False,
) -> Tuple[np.ndarray, float]:
    """
    Iterative solver for signed dcSBM using log reparametrization and patience.

    The parameter vector is packed as:
      u = [ log x^+_0..N-1,  log x^-_0..N-1,  log χ^+_0..M-1,  log χ^-_0..M-1 ],
    where χ^±_flat index unordered block-pairs (r ≤ s).

    Parameters
    ----------
    k_plus, k_minus : (N,)
        Observed positive/negative degrees.
    c : (N,)
        Community labels.
    Lp_obs, Ln_obs : (R,R)
        Observed +/− block link counts for unordered pairs (upper-triangular semantics).
    u_init : (2N + 2M,)
        Positive initial parameters [x^+, x^−, χ^+_flat, χ^−_flat] (will be log-transformed).
    method : {'newton','lm','hybr'}
        Root-finding strategy. 'newton' uses `newton_krylov(lgmres)`.
    tol : float
        Target residual 2-norm tolerance.
    max_iter : int
        Maximum number of outer iterations (patience loop).
    patience : int
        Early-stop if best residual fails to improve for this many iterations.
    verbose : int | bool
        If truthy, emit INFO-level progress logs.

    Returns
    -------
    u_params : (2N + 2M,)
        Optimized positive parameters [x^+, x^−, χ^+_flat, χ^−_flat] (exponentiated).
    best_norm : float
        Residual 2-norm at the best solution found.
    """
    if verbose:
        logger.info(
            "signed dcSBM: starting solve (method=%s, tol=%.1e, max_iter=%d, patience=%d)",
            method,
            tol,
            max_iter,
            patience,
        )

    block_pairs, idx_map = _make_block_struct(c)

    def f_res(z: np.ndarray) -> np.ndarray:
        return _residuals_signed_dcSBM_log(
            z, k_plus, k_minus, c, Lp_obs, Ln_obs, block_pairs, idx_map
        )

    # Guarded logs for positivity
    z0 = np.log(np.maximum(u_init, EPS))

    best_z = z0.copy()
    best_norm = np.linalg.norm(f_res(best_z))
    no_improve = 0

    for it in range(max_iter):
        # One nonlinear step
        if method == "newton":
            z_curr = newton_krylov(f_res, z0, method="lgmres", inner_maxiter=100)
        else:
            sol = root(
                f_res, x0=z0, method=method, tol=tol, options={"maxfev": 100 * z0.size}
            )
            z_curr = sol.x

        curr = np.linalg.norm(f_res(z_curr))

        # Keep best
        if curr < best_norm:
            best_norm = curr
            best_z = z_curr.copy()
            no_improve = 0
        else:
            no_improve += 1

        if verbose:
            logger.info(
                "signed dcSBM: iter=%d  ||res||=%.3e  best=%.3e  no_improve=%d",
                it + 1,
                curr,
                best_norm,
                no_improve,
            )

        # Stopping conditions
        if curr < tol:
            best_z = z_curr.copy()
            if verbose:
                logger.info(
                    "signed dcSBM: converged at iter %d with ||res||=%.3e", it + 1, curr
                )
            break
        if no_improve >= patience:
            logger.warning(
                "signed dcSBM solver: stopped after %d no-improve iterations at iter %d.",
                patience,
                it + 1,
            )
            break
        if it == max_iter - 1:
            logger.warning(
                "signed dcSBM solver: maximum iterations reached before convergence."
            )

        # Warm start next step
        z0 = z_curr.copy()

    return np.exp(best_z), best_norm
