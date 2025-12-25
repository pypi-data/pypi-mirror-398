"""
ERGM Solvers (maximum-entropy)
==============================

Binary (unsigned), signed, and weighted solvers used inside BIC pipelines.

Notation
--------
N nodes; communities c[i] in {0,...,B-1}.

Binary (UBCM / dcSBM)
---------------------
- Degrees: k[i] = sum_j A[i,j]
- UBCM (undirected): parameters x_i > 0
    p_ij = (x_i x_j) / (1 + x_i x_j)
  Residuals (log-space u = log x):
    r_i(u) = sum_{j != i} p_ij(u) - k[i]
- dcSBM: parameters x_i > 0, chi_{rs} > 0
    z_ij = x_i x_j chi_{c_i,c_j},   p_ij = z_ij / (1 + z_ij)
  Residual vector stacks node and block constraints:
    [sum_j p_ij - k[i]]_i,  [sum_{(i<j) in (r,s)} p_ij - L_obs[r,s]]_{r<=s}

Signed (SCM / signed dcSBM)
---------------------------
- Degrees: k_plus[i] = sum_j Apos[i,j],  k_minus[i] = sum_j Aneg[i,j]
- Tri-nomial (+, -, 0) with node factors x_plus_i, x_minus_i and block affinities chi_plus, chi_minus:
    p_plus_ij  = (x_plus_i x_plus_j chi_plus_{rs}) / (1 + x_plus_i x_plus_j chi_plus_{rs} + x_minus_i x_minus_j chi_minus_{rs})
    p_minus_ij = (x_minus_i x_minus_j chi_minus_{rs}) / (1 + x_plus_i x_plus_j chi_plus_{rs} + x_minus_i x_minus_j chi_minus_{rs})
- SCM (node-only): chi_plus_{rs} = chi_minus_{rs} = 1 (two node systems, coupled via the denominator)

Weighted (WCM / weighted dcSBM; geometric weights)
--------------------------------------------------
- Strengths: s[i] = sum_j W[i,j]
- Geometric model with mean z_ij > 0 and p_ij = z_ij/(1+z_ij):
    P(w_ij = w) = (1 - p_ij) p_ij^w,    E[w_ij] = z_ij
- WCM:             z_ij = x_i x_j
- weighted dcSBM:  z_ij = x_i x_j chi_{rs}
Residuals stack node strengths and block totals.

Public API
----------
Binary:
  solve_UBCM_iterative(k, x_init, method="lm"|"hybr"|"krylov", tol, max_iter, patience)
  solve_dcSBM_iterative(k, c, L_obs, u_init, method="lm"|"hybr"|"newton", tol, max_iter, patience)

Signed:
  solve_SCM_iterative(k_plus, k_minus, x_plus_init, x_minus_init, method, tol, max_iter, patience)
  solve_signed_dcSBM_iterative(k_plus, k_minus, c, Lp_obs, Ln_obs, u_init, method, tol, max_iter, patience)

Weighted:
  solve_WCM_iterative(s, x_init, method, tol, max_iter, patience)
  solve_wdcSBM_iterative(s, c, L_obs, u_init, method, tol, max_iter, patience)
"""

from __future__ import annotations

from .binary_solvers import solve_dcSBM_iterative, solve_UBCM_iterative
from .signed_solvers import solve_SCM_iterative, solve_signed_dcSBM_iterative
from .weighted_solvers import solve_WCM_iterative, solve_wdcSBM_iterative

__all__ = [
    "solve_UBCM_iterative",
    "solve_dcSBM_iterative",
    "solve_SCM_iterative",
    "solve_signed_dcSBM_iterative",
    "solve_WCM_iterative",
    "solve_wdcSBM_iterative",
]
