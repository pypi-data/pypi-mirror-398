"""
binary_solvers.py

Solvers for Exponential Random Graph Models (ERGMs):
  - UBCM (Undirected Binary Configuration Model)
  - degree-corrected SBM (dcSBM)

Each solver provides:
  • a residual function
  • an iterative root-finding routine with a patience mechanism
  • optional verbose logging for reproducibility/debugging
"""

from __future__ import annotations

import logging
import warnings
from typing import Tuple

import numpy as np
from numba import get_num_threads, njit, prange
from scipy.optimize import OptimizeWarning, newton_krylov, root

# Centralized numeric constants (kept equal to legacy defaults)
from ..utils.constants import (
    EPS,  # 1e-12
    MAX_IT_DEFAULT,  # 1000
    PATIENCE_DEFAULT,  # 10
    TOL_DCSBM,  # 1e-6
    TOL_UBCM,  # 1e-6
)

# ---------------------------------------------------------------------------
# WARNING SUPPRESSION
# ---------------------------------------------------------------------------
# Silence non-critical optimization warnings from SciPy (e.g., non-convergence
# messages during exploratory runs). Users can always raise the log level to
# see progress through the module logger instead of raw SciPy warnings.
warnings.simplefilter("ignore", OptimizeWarning)

# Module logger (configure once at application entrypoint)
logger = logging.getLogger("domino.ergms.binary")

# ---------------------------------------------------------------------------
# UBCM SOLVER
# ---------------------------------------------------------------------------


@njit(cache=True, fastmath=True)
def _residuals_UBCM_log(u: np.ndarray, k: np.ndarray) -> np.ndarray:
    """
    UBCM residuals in log-space (x = exp(u)), no NxN matrix allocation.

    For the undirected binary configuration model with edge probabilities
      p_ij = x_i x_j / (1 + x_i x_j),
    the expected degree is E[k_i] = sum_{j≠i} p_ij.

    Residual definition:
      res[i] = sum_{j!=i} x_i x_j / (1 + x_i x_j) - k[i]

    Parameters
    ----------
    u : (N,)
        Log-parameters, u_i = log x_i (so x_i > 0).
    k : (N,)
        Observed degrees.

    Returns
    -------
    res : (N,)
        Residual vector (expected degree minus observed).
    """
    x = np.exp(u)
    N = x.size
    res = np.empty(N)
    for i in range(N):
        xi = x[i]
        s = 0.0
        for j in range(N):
            if j == i:
                continue
            t = xi * x[j]
            s += t / (1.0 + t)
        res[i] = s - k[i]
    return res


def solve_UBCM_iterative(
    k: np.ndarray,
    x_init: np.ndarray,
    method: str = "lm",
    tol: float = TOL_UBCM,
    max_iter: int = MAX_IT_DEFAULT,
    patience: int = PATIENCE_DEFAULT,
    verbose: int | bool = False,
) -> Tuple[np.ndarray, float]:
    """
    Solve UBCM in log-space to enforce positivity; supports 'lm', 'hybr', or 'krylov'.

    The routine maintains the best iterate seen (by residual 2-norm) and
    stops early if no improvement is observed for `patience` iterations.

    Parameters
    ----------
    k : (N,)
        Observed degrees.
    x_init : (N,)
        Positive initial guess for x (will be floored by EPS for safety).
    method : {'lm','hybr','krylov'}
        SciPy root-finding strategy. 'krylov' uses `newton_krylov(lgmres)`.
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
    x_opt : (N,)
        Optimized positive node factors.
    best_norm : float
        Residual 2-norm at the best iterate.
    """
    if verbose:
        logger.info(
            "UBCM: starting solve (method=%s, tol=%.1e, max_iter=%d, patience=%d)",
            method,
            tol,
            max_iter,
            patience,
        )

    # Guard against zeros to keep logs finite.
    z0 = np.log(np.maximum(x_init, EPS))

    best_u = z0.copy()
    best_norm = np.linalg.norm(_residuals_UBCM_log(best_u, k))
    no_improve = 0

    for i in range(max_iter):
        # One nonlinear step
        if method == "krylov":
            u_curr = newton_krylov(
                lambda u: _residuals_UBCM_log(u, k),
                z0,
                method="lgmres",
                inner_maxiter=100,
            )
        else:
            sol = root(
                lambda u: _residuals_UBCM_log(u, k),
                x0=z0,
                method=method,
                options={"maxfev": 10000},
            )
            u_curr = sol.x

        curr_norm = np.linalg.norm(_residuals_UBCM_log(u_curr, k))

        # Keep the best iterate
        if curr_norm < best_norm:
            best_norm = curr_norm
            best_u = u_curr.copy()
            no_improve = 0
        else:
            no_improve += 1

        if verbose:
            logger.info(
                "UBCM: iter=%d  ||res||=%.3e  best=%.3e  no_improve=%d",
                i + 1,
                curr_norm,
                best_norm,
                no_improve,
            )

        # Stopping conditions
        if curr_norm < tol:
            best_u = u_curr.copy()
            if verbose:
                logger.info(
                    "UBCM: converged at iter %d with ||res||=%.3e", i + 1, curr_norm
                )
            break
        if no_improve >= patience:
            logger.warning(
                "UBCM solver: stopping after %d no-improve iterations at iter %d.",
                patience,
                i + 1,
            )
            break
        if i == max_iter - 1:
            logger.warning(
                "UBCM solver: maximum iterations reached before convergence."
            )

        # Warm start next step
        z0 = u_curr.copy()

    return np.exp(best_u), best_norm


# ---------------------------------------------------------------------------
# degree-corrected SBM (dcSBM) SOLVER
# ---------------------------------------------------------------------------


def _make_block_struct(c: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build block-pair list and index map for communities.

    Parameters
    ----------
    c : np.ndarray
        Community labels for each node, shape (N,).

    Returns
    -------
    block_pairs : np.ndarray
        Array of (r, s) pairs with r <= s, shape (M, 2).
    idx_map : np.ndarray
        Mapping matrix of shape (R, R) where idx_map[r,s] gives index in block_pairs.
        Symmetric by construction (idx_map[s,r] = idx_map[r,s]).
    """
    R = int(c.max()) + 1
    pairs = [(r, s) for r in range(R) for s in range(r, R)]
    block_pairs = np.array(pairs, dtype=np.int64)
    # Index mapping for fast lookups
    idx_map = -np.ones((R, R), dtype=np.int64)
    for idx, (r, s) in enumerate(pairs):
        idx_map[r, s] = idx
        idx_map[s, r] = idx
    return block_pairs, idx_map


@njit(parallel=True, fastmath=True)
def _residuals_numba(
    u: np.ndarray,
    k: np.ndarray,
    c: np.ndarray,
    L_obs: np.ndarray,
    block_pairs: np.ndarray,
    idx_map: np.ndarray,
) -> np.ndarray:
    """
    Parallel dcSBM residuals in log-parameter space using per-thread accumulators
    and explicit reduction (no atomics). The evaluation is deterministic with
    respect to thread count T and tile partitioning.

    Model:
      p_ij = z_ij / (1 + z_ij),       z_ij = x_i x_j χ_{c_i,c_j}.

    Residual vector (length N + M):
      • first N:   ∑_j p_ij  −  k_i
      • next  M:   ∑_{(i<j)∈(r,s)} p_ij  −  L_obs[r,s]

    Parameters
    ----------
    u : (N+M,)
        Log-parameters: [ log x (N), log chi_flat (M) ].
    k : (N,)
        Observed degrees.
    c : (N,)
        Community labels.
    L_obs : (R,R)
        Observed block link counts (upper-triangular semantics).
    block_pairs : (M,2)
        Unordered block indices (r <= s) mapping into chi_flat.
    idx_map : (R,R)
        r,s -> index into block_pairs (symmetric).

    Returns
    -------
    res : (N+M,)
        Concatenated residuals for node degrees and block totals.
    """
    N = k.shape[0]
    M = block_pairs.shape[0]

    # Recover positive parameters
    x = np.exp(u[:N])
    chi_flat = np.exp(u[N:])

    # Number of tiles = number of worker threads.
    T = get_num_threads()

    # Per-thread accumulators
    deg_local = np.zeros((T, N))
    blk_local = np.zeros((T, M))

    # Static partitioning of i-range into T tiles: [i0, i1)
    base = N // T
    rem = N % T

    for t in prange(T):
        i0 = t * base + (t if t < rem else rem)
        i1 = i0 + base + (1 if t < rem else 0)
        if i0 >= i1:
            continue

        deg_t = deg_local[t]
        blk_t = blk_local[t]

        for i in range(i0, i1):
            xi = x[i]
            ci_ = c[i]
            for j in range(i + 1, N):
                cj = c[j]
                idx = idx_map[ci_, cj]

                z = xi * x[j] * chi_flat[idx]
                p = z / (1.0 + z)

                deg_t[i] += p
                deg_t[j] += p
                blk_t[idx] += p

    # Explicit reduction across tiles
    deg_exp = np.zeros(N)
    for t in range(T):
        for i in range(N):
            deg_exp[i] += deg_local[t, i]

    blk_exp = np.zeros(M)
    for t in range(T):
        for m in range(M):
            blk_exp[m] += blk_local[t, m]

    # Build residual vector
    res = np.empty(N + M)
    for i in range(N):
        res[i] = deg_exp[i] - k[i]
    for m in range(M):
        r = block_pairs[m, 0]
        s = block_pairs[m, 1]
        res[N + m] = blk_exp[m] - L_obs[r, s]

    return res


def solve_dcSBM_iterative(
    k: np.ndarray,
    c: np.ndarray,
    L_obs: np.ndarray,
    u_init: np.ndarray,
    method: str = "lm",
    tol: float = TOL_DCSBM,
    max_iter: int = MAX_IT_DEFAULT,
    patience: int = PATIENCE_DEFAULT,
    verbose: int | bool = False,
) -> Tuple[np.ndarray, float]:
    """
    Iterative solver for degree-corrected SBM using log reparametrization and patience.

    The parameter vector is packed as:
      u = [ log x_0, …, log x_{N-1},   log χ_0, …, log χ_{M-1} ],
    where χ_flat indexes unordered block-pairs (r ≤ s).

    Parameters
    ----------
    k : (N,)
        Observed degrees.
    c : (N,)
        Community labels.
    L_obs : (R,R)
        Observed block link counts for unordered pairs (upper-triangular semantics).
    u_init : (N+M,)
        Positive initial parameters [x; chi_flat] (will be log-transformed).
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
    u_params : (N+M,)
        Optimized positive parameters [x; chi_flat] (exponentiated).
    best_norm : float
        Residual 2-norm at the best solution found.
    """
    if verbose:
        logger.info(
            "dcSBM: starting solve (method=%s, tol=%.1e, max_iter=%d, patience=%d)",
            method,
            tol,
            max_iter,
            patience,
        )

    # Precompute block structure and wrap residual function in log-space
    block_pairs, idx_map = _make_block_struct(c)

    def f_res(logu: np.ndarray) -> np.ndarray:
        return _residuals_numba(logu, k, c, L_obs, block_pairs, idx_map)

    # Initialize logs (guarded to keep logs finite)
    alpha0 = np.log(np.maximum(u_init[: k.size], EPS))
    beta0 = np.log(np.maximum(u_init[k.size :], EPS))
    z0 = np.concatenate([alpha0, beta0])

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

        norm_curr = np.linalg.norm(f_res(z_curr))

        # Keep the best iterate
        if norm_curr < best_norm:
            best_norm = norm_curr
            best_z = z_curr.copy()
            no_improve = 0
        else:
            no_improve += 1

        if verbose:
            logger.info(
                "dcSBM: iter=%d  ||res||=%.3e  best=%.3e  no_improve=%d",
                it + 1,
                norm_curr,
                best_norm,
                no_improve,
            )

        # Stopping conditions
        if norm_curr < tol:
            best_z = z_curr.copy()
            if verbose:
                logger.info(
                    "dcSBM: converged at iter %d with ||res||=%.3e", it + 1, norm_curr
                )
            break
        if no_improve >= patience:
            logger.warning(
                "dcSBM solver: stopped after %d no-improve at iter %d.",
                patience,
                it + 1,
            )
            break
        if it == max_iter - 1:
            logger.warning(
                "dcSBM solver: maximum iterations reached before reaching convergence."
            )

        # Warm start next step
        z0 = z_curr.copy()

    u_params = np.exp(best_z)
    return u_params, best_norm


# ---------------------------------------------------------------------------
# Example usage (kept commented to illustrate how to call the solvers)
# ---------------------------------------------------------------------------
# Initial guess for x: x_UBCM_initial = k / sqrt(2*L)
#
# Solve UBCM:
# x_UBCM, norm_UBCM = solve_UBCM_iterative(
#     k, x_UBCM_initial,
#     method='lm', tol=1e-9, max_iter=1000, patience=10, verbose=True
# )
#
# Compute expected UBCM probabilities:
# p_UBCM = (x_UBCM[:, None] * x_UBCM[None, :]) / (1 + x_UBCM[:, None] * x_UBCM[None, :])
# np.fill_diagonal(p_UBCM, 0)
# k_UBCM = p_UBCM.sum(axis=1)
#
# Solve dcSBM:
# x_dcSBM_init = k / np.sqrt(2 * np.sum(L_obs))
# block_list = [(r, s) for r in range(R) for s in range(r, R)]
# chi_dcSBM_init = np.ones(len(block_list))
# u_dcSBM_init = np.concatenate([x_dcSBM_init, chi_dcSBM_init])
# u_dcSBM, _ = solve_dcSBM_iterative(k, c, L_obs, u_dcSBM_init, verbose=True)
#
# Reconstruct parameters:
# x_dcSBM = u_dcSBM[:N]
# chi_dcSBM = np.zeros((R, R))
# for idx, (r, s) in enumerate(block_list):
#     chi_dcSBM[r, s] = chi_dcSBM[s, r] = u_dcSBM[N + idx]
#
# Compute expected values and compare
# p_dcSBM = np.zeros((N,N))
# for i in range(N):
#     for j in range(i+1, N):
#         val = x_dcSBM[i] * x_dcSBM[j] * chi_dcSBM[c[i], c[j]]
#         p_dcSBM[i, j] = p_dcSBM[j, i] = val / (1 + val)
# np.fill_diagonal(p_dcSBM, 0)
# k_dcSBM = p_dcSBM.sum(axis=1)
