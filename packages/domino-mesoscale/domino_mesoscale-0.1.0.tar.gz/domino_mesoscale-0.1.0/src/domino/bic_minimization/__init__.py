"""
Leiden + BIC Community Detection Pipelines
==========================================

Iterative pipelines that alternate:
  (1) parameter updates (where applicable) and
  (2) a Leiden pass optimizing -BIC,
with optional macro merges and an optional target number of communities K via
greedy BIC-optimal merges.

BIC (lower is better), V = N(N-1)/2
-----------------------------------
- SBM (binary):            k = B(B+1)/2
- dcSBM (binary):          k = N + B(B+1)/2
- Signed SBM:              k = B(B+1)            (two per unordered block pair)
- Signed dcSBM:            k = 2N + B(B+1)
- Weighted wSBM:           k = B(B+1)/2
- Weighted wdcSBM:         k = N + B(B+1)/2

Pipelines (return (Partition, best_bic))
----------------------------------------
Binary:
  iterative_leiden_SBM(
      G, A, *, initial_partition=None|"modularity",
      theta=0.0, gamma=0.0, max_outer=5,
      do_macro_merge=False, target_K=None
  )

  iterative_leiden_dcSBM(
      G, A, *, initial_partition=None|"modularity",
      theta=0.0, gamma=0.0, max_outer=5,
      do_macro_merge=False, target_K=None,
      fix_x_ubcm=True
  )
  # fix_x_ubcm=True: freeze x from a single UBCM solve, update chi each outer pass;
  # a post-hoc full dcSBM solve computes the exact BIC for the best partition.

Signed:
  iterative_leiden_sSBM(
      G, Apos, Aneg, *, initial_partition=None|"modularity"|"pos_modularity",
      theta=0.0, gamma=0.0, max_outer=5,
      do_macro_merge=False, target_K=None
  )

  iterative_leiden_sdcSBM(
      G, Apos, Aneg, *, initial_partition=None|"modularity"|"pos_modularity",
      theta=0.0, gamma=0.0, max_outer=5,
      do_macro_merge=False, target_K=None,
      fix_x_scm=True
  )
  # fix_x_scm=True: freeze (x_pos,x_neg) from SCM once; update (chi_pos,chi_neg) each pass;
  # optional post-hoc full solve for exact BIC.

Weighted (geometric):
  iterative_leiden_wSBM(
      G, W, *, initial_partition=None|"modularity",
      theta=0.0, gamma=0.0, max_outer=5,
      do_macro_merge=False, target_K=None
  )

  iterative_leiden_wdcSBM(
      G, W, *, initial_partition=None|"modularity",
      theta=0.0, gamma=0.0, max_outer=5,
      do_macro_merge=False, target_K=None,
      fix_x_wcm=True
  )
  # fix_x_wcm=True: freeze x from one WCM solve; closed-form chi_hat each pass;
  # optional post-hoc full (x,chi) solve for exact BIC.
"""

from __future__ import annotations

from .binary_bic import iterative_leiden_dcSBM, iterative_leiden_SBM
from .signed_bic import iterative_leiden_sdcSBM, iterative_leiden_sSBM
from .weighted_bic import iterative_leiden_wdcSBM, iterative_leiden_wSBM

__all__ = [
    "iterative_leiden_SBM",
    "iterative_leiden_dcSBM",
    "iterative_leiden_sSBM",
    "iterative_leiden_sdcSBM",
    "iterative_leiden_wSBM",
    "iterative_leiden_wdcSBM",
]
