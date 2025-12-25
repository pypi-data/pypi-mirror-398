"""
weighted_solvers.py

Solvers for *weighted* (non-signed) Exponential Random Graph Models (ERGMs)
in the maximum-entropy (geometric) framework.

Models
------
  • WCM   (Weighted Configuration Model; strength-only)
  • weighted dcSBM (degree-corrected SBM for weights)

Conventions and likelihood (geometric)
--------------------------------------
For each dyad (i,j), let the *mean* parameter be
  z_ij = x_i x_j                        (WCM)
  z_ij = x_i x_j χ_{c_i,c_j}            (weighted dcSBM)

We use the geometric distribution on non-negative integer weights:
  P(w_ij = w) = (1 - p_ij) p_ij^w,   with   p_ij = z_ij / (1 + z_ij).

Hence  E[w_ij] = p_ij / (1 - p_ij) = z_ij,  and the log-likelihood is
  log L = ∑_{i<j} [ w_ij log z_ij − (w_ij + 1) log(1 + z_ij) ].

Residual systems (what we set to zero)
--------------------------------------
  • WCM:            ∑_{j≠i} E[w_ij]  − s_i         = 0    for all i,
                     with E[w_ij] = x_i x_j.
  • weighted dcSBM: [ ∑_{j≠i} E[w_ij] − s_i ]_i,  and
                    [ ∑_{(i<j)∈(r,s)} E[w_ij] − L_obs[r,s] ]_{r≤s}.

Implementation notes
--------------------
• We solve in *log*-space (u = log x, etc.) to enforce positivity of x and χ.
• Numerical guards (U_MIN/U_MAX/X_MIN/Z_MIN) are centralized in `utils/constants.py`
  and applied exactly as in the legacy code to preserve behavior.
• No RNG is used; runs are deterministic given inputs. Progress is reported via
  a module logger when `verbose=True` is passed to the solvers.
• Tolerances and iteration caps are centralized (TOL_WCM, TOL_WDCSBM, MAX_IT_DEFAULT,
  PATIENCE_DEFAULT) to keep consistency across binary/signed/weighted solvers.
"""

from __future__ import annotations

import logging
import warnings
from typing import Tuple

import numpy as np
from numba import get_num_threads, njit, prange
from scipy.optimize import OptimizeWarning, newton_krylov, root

# ---------------------------------------------------------------------------
# Centralized numeric constants & defaults (kept equal to legacy defaults)
# ---------------------------------------------------------------------------
from ..utils.constants import (
    EPS,  # universal epsilon to guard logs (e.g., 1e-12)
    MAX_IT_DEFAULT,  # default max outer iterations
    PATIENCE_DEFAULT,  # default patience for no-improve early stop
    TOL_WCM,  # default tolerance for WCM
    TOL_WDCSBM,  # default tolerance for weighted dcSBM
    U_MAX,
    U_MIN,  # clamps for log-parameters in WCM
    X_MIN,  # floor for x_i in WCM
    Z_MIN,  # lower bound on z = x_i x_j [χ_{rs}]
)

# ---------------------------------------------------------------------------
# WARNING SUPPRESSION
# ---------------------------------------------------------------------------
# Silence non-critical SciPy optimization warnings. Users can enable the
# module logger for progress instead of reading raw warnings.
warnings.simplefilter("ignore", OptimizeWarning)

# Module-level logger (configured once at application entrypoint)
logger = logging.getLogger("domino.ergms.weighted")


# -----------------------------------------------------------------------------
# WCM solver (strength-only, geometric weights)
# -----------------------------------------------------------------------------


@njit(cache=True, fastmath=True)
def _residuals_WCM_log(u: np.ndarray, s: np.ndarray) -> np.ndarray:
    """
    Geometric WCM residuals in log-space (x_i = exp(u_i) > 0).

    Model:
      E[w_ij] = x_i x_j,
      E[s_i]  = sum_{j!=i} x_i x_j = x_i (sum_j x_j - x_i).

    Residual:
      res[i] = x_i * (S - x_i) - s[i],   where S = sum_j x_j.

    Parameters
    ----------
    u : (N,)
        Log-parameters (u_i = log x_i).
    s : (N,)
        Observed strengths.

    Returns
    -------
    res : (N,)
        Residual vector (expected minus observed strengths).
    """
    N = u.size
    res = np.empty(N)
    x = np.empty(N)

    # Clamp logs for stable exponentiation, then floor x_i
    for i in range(N):
        ui = u[i]
        if ui < U_MIN:
            ui = U_MIN
        elif ui > U_MAX:
            ui = U_MAX
        xi = np.exp(ui)
        if xi < X_MIN:
            xi = X_MIN
        x[i] = xi

    # Sum of x's
    S = 0.0
    for i in range(N):
        S += x[i]

    # Residuals
    for i in range(N):
        res[i] = x[i] * (S - x[i]) - s[i]
    return res


def solve_WCM_iterative(
    s: np.ndarray,
    x_init: np.ndarray,
    method: str = "lm",
    tol: float = TOL_WCM,
    max_iter: int = MAX_IT_DEFAULT,
    patience: int = PATIENCE_DEFAULT,
    verbose: int | bool = False,
) -> Tuple[np.ndarray, float]:
    """
    Solve WCM in log-space to enforce positivity; supports 'lm', 'hybr', or 'krylov'.

    The routine maintains the best iterate (by residual 2-norm) and stops early
    when no improvement is observed for `patience` iterations.

    Parameters
    ----------
    s : (N,)
        Observed strengths.
    x_init : (N,)
        Positive initial guess for x (floored by EPS for logs).
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
            "WCM: starting solve (method=%s, tol=%.1e, max_iter=%d, patience=%d)",
            method,
            tol,
            max_iter,
            patience,
        )

    # Guard for logs
    z0 = np.log(np.maximum(x_init, EPS))

    best_u = z0.copy()
    best_norm = np.linalg.norm(_residuals_WCM_log(best_u, s))
    no_improve = 0

    for it in range(max_iter):
        # One nonlinear step
        if method == "krylov":
            u_curr = newton_krylov(
                lambda u: _residuals_WCM_log(u, s),
                z0,
                method="lgmres",
                inner_maxiter=100,
            )
        else:
            sol = root(
                lambda u: _residuals_WCM_log(u, s),
                x0=z0,
                method=method,
                options={"maxfev": 10000},
            )
            u_curr = sol.x

        curr = np.linalg.norm(_residuals_WCM_log(u_curr, s))

        # Keep best iterate
        if curr < best_norm:
            best_norm = curr
            best_u = u_curr.copy()
            no_improve = 0
        else:
            no_improve += 1

        if verbose:
            logger.info(
                "WCM: iter=%d  ||res||=%.3e  best=%.3e  no_improve=%d",
                it + 1,
                curr,
                best_norm,
                no_improve,
            )

        # Stopping conditions
        if curr < tol:
            best_u = u_curr.copy()
            if verbose:
                logger.info("WCM: converged at iter %d with ||res||=%.3e", it + 1, curr)
            break
        if no_improve >= patience:
            logger.warning(
                "WCM solver: stopping after %d no-improve iterations at iter %d.",
                patience,
                it + 1,
            )
            break
        if it == max_iter - 1:
            logger.warning(
                "WCM solver: maximum iterations reached before reaching convergence."
            )

        # Warm start next step
        z0 = u_curr.copy()

    return np.exp(best_u), best_norm


# -----------------------------------------------------------------------------
# weighted dcSBM residuals and solver
# -----------------------------------------------------------------------------


def _make_block_struct(c: np.ndarray):
    """
    Build block-pair list and index map. Identical semantics as in the binary solvers.

    Parameters
    ----------
    c : (N,)
        Community labels per node.

    Returns
    -------
    block_pairs : (M, 2)
        Unordered (r, s) pairs with r ≤ s.
    idx_map : (R, R)
        Fast lookup: idx_map[r, s] -> index in block_pairs (symmetric).
    """
    R = int(c.max()) + 1
    pairs = [(r, s) for r in range(R) for s in range(r, R)]
    block_pairs = np.array(pairs, dtype=np.int64)
    idx_map = -np.ones((R, R), dtype=np.int64)
    for idx, (r, s) in enumerate(pairs):
        idx_map[r, s] = idx
        idx_map[s, r] = idx
    return block_pairs, idx_map


@njit(parallel=True, fastmath=True)
def _residuals_wdcSBM_log(
    u: np.ndarray,
    s: np.ndarray,  # observed strengths (N,)
    c: np.ndarray,  # labels (N,)
    L_obs: np.ndarray,  # block weight totals (R,R); upper-triangular semantics
    block_pairs: np.ndarray,  # (M,2) unordered pairs r<=s
    idx_map: np.ndarray,  # (R,R) -> index in block_pairs
) -> np.ndarray:
    """
    Weighted dcSBM residuals in log-parameter space with per-thread accumulators
    and explicit reduction (no atomics). Deterministic w.r.t. thread tiling.

    Parameter packing (all in logs):
      u[0:N]      -> log x_i
      u[N:N+M]    -> log chi_flat (for unordered block-pairs)

    Expected weights:
      E[w_ij] = z_ij = x_i x_j χ_{c_i,c_j}.

    Residual vector (length N + M):
      - first N:  ∑_j z_ij  −  s_i
      - next  M:  ∑_{(i<j)∈(r,s)} z_ij  −  L_obs[r,s]
    """
    N = s.size
    M = block_pairs.shape[0]

    x = np.exp(u[:N])
    ch = np.exp(u[N:])

    T = get_num_threads()
    deg_local = np.zeros((T, N))
    blk_local = np.zeros((T, M))

    base = N // T
    rem = N % T

    for t in prange(T):
        i0 = t * base + (t if t < rem else rem)
        i1 = i0 + base + (1 if t < rem else 0)
        if i0 >= i1:
            continue

        dloc = deg_local[t]
        bloc = blk_local[t]

        for i in range(i0, i1):
            xi = x[i]
            ci = c[i]
            for j in range(i + 1, N):
                idx = idx_map[ci, c[j]]
                z = xi * x[j] * ch[idx]
                if z < Z_MIN:
                    z = Z_MIN  # floor to avoid degenerate zeros
                dloc[i] += z
                dloc[j] += z
                bloc[idx] += z

    # Reduce per-thread accumulators
    deg = np.zeros(N)
    for t in range(T):
        for i in range(N):
            deg[i] += deg_local[t, i]

    blk = np.zeros(M)
    for t in range(T):
        for m in range(M):
            blk[m] += blk_local[t, m]

    # Assemble residuals
    res = np.empty(N + M)
    for i in range(N):
        res[i] = deg[i] - s[i]
    for m in range(M):
        r = block_pairs[m, 0]
        s_ = block_pairs[m, 1]
        res[N + m] = blk[m] - L_obs[r, s_]
    return res


def solve_wdcSBM_iterative(
    s: np.ndarray,
    c: np.ndarray,
    L_obs: np.ndarray,
    u_init: np.ndarray,
    method: str = "lm",
    tol: float = TOL_WDCSBM,
    max_iter: int = MAX_IT_DEFAULT,
    patience: int = PATIENCE_DEFAULT,
    verbose: int | bool = False,
) -> Tuple[np.ndarray, float]:
    """
    Iterative solver for weighted dcSBM (geometric) using log reparametrization and patience.

    The parameter vector is packed as:
      u = [ log x_0..N-1,   log χ_0..M-1 ],  where χ_flat indexes unordered (r ≤ s).

    Parameters
    ----------
    s : (N,)
        Observed node strengths.
    c : (N,)
        Community labels.
    L_obs : (R,R)
        Observed block weight totals (upper-triangular semantics).
    u_init : (N+M,)
        Positive initial parameters [x; χ_flat] (floored by EPS for logs).
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
        Optimized positive parameters [x; χ_flat] (exponentiated).
    best_norm : float
        Residual 2-norm at the best solution found.
    """
    if verbose:
        logger.info(
            "weighted dcSBM: starting solve (method=%s, tol=%.1e, max_iter=%d, patience=%d)",
            method,
            tol,
            max_iter,
            patience,
        )

    block_pairs, idx_map = _make_block_struct(c)

    def f_res(logu: np.ndarray) -> np.ndarray:
        return _residuals_wdcSBM_log(logu, s, c, L_obs, block_pairs, idx_map)

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

        # Keep best iterate
        if curr < best_norm:
            best_norm = curr
            best_z = z_curr.copy()
            no_improve = 0
        else:
            no_improve += 1

        if verbose:
            logger.info(
                "weighted dcSBM: iter=%d  ||res||=%.3e  best=%.3e  no_improve=%d",
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
                    "weighted dcSBM: converged at iter %d with ||res||=%.3e",
                    it + 1,
                    curr,
                )
            break
        if no_improve >= patience:
            logger.warning(
                "weighted dcSBM solver: stopped after %d no-improve at iter %d.",
                patience,
                it + 1,
            )
            break
        if it == max_iter - 1:
            logger.warning(
                "weighted dcSBM solver: maximum iterations reached before reaching convergence."
            )

        # Warm start next step
        z0 = z_curr.copy()

    return np.exp(best_z), best_norm
