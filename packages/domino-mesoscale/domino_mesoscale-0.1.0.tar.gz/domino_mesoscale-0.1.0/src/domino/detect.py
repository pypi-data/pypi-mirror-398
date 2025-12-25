"""
detect.py

Unified entry point for community detection via Leiden optimization of
BIC-based objective functions.

This module provides two public functions:

1) detect_communities(...)
   Core solver entry point: runs Leiden passes and model parameter updates
   (when degree correction is enabled), returning (Partition, BIC).

2) detect(...)
   High-level convenience wrapper: calls detect_communities(...) and then
   optionally triggers visualization and/or reporting via
   domino.represent_and_analyze.process_graph.

Modes
-----
- mode="binary"   : SBM / dcSBM on a binarized adjacency support.
- mode="signed"   : signed SBM / signed dcSBM with (Apos, Aneg) layers.
- mode="weighted" : weighted SBM / weighted dcSBM on a nonnegative weight matrix.

Guards and coercions
--------------------
- Symmetry is enforced (M <- 0.5*(M + M.T)) when needed, with warnings.
- The diagonal is set to zero.
- mode="binary":
    If negative entries exist: binarize union support Abin = 1{|A| > 0}.
    Else: binarize positive support Abin = 1{A > 0}.
- mode="signed":
    If a single signed matrix is provided: split layers by sign:
        Apos = 1{A > 0}, Aneg = 1{A < 0}.
    If Aneg is provided explicitly: threshold each as 1{>0}.
- mode="weighted":
    If negative weights exist: abs(W) is used with a warning.
    If positive weights are fractional (non-integers): a warning is emitted.

Post-processing (detect only)
-----------------------------
The high-level function detect(...) accepts:
    viz: bool | dict
    report: bool | dict

These are adapted to process_graph in a backwards-compatible way:
- If process_graph supports viz/report keyword arguments, they are passed through.
- Otherwise, dictionaries are forwarded as plain kwargs (e.g., layout_type, pos),
  and report=True is mapped to print_info=True when possible.

This adapter is designed to keep detect_communities free from plotting or I/O.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple, Union

import networkx as nx
import numpy as np

from .bic_minimization.binary_bic import iterative_leiden_dcSBM, iterative_leiden_SBM
from .bic_minimization.signed_bic import iterative_leiden_sdcSBM, iterative_leiden_sSBM
from .bic_minimization.weighted_bic import (
    iterative_leiden_wdcSBM,
    iterative_leiden_wSBM,
)
from .leiden.partitions_functions import Partition

logger = logging.getLogger("domino.detect")

# Numerical tolerances used only for internal coercions and checks.
_INT_TOL = 1e-12


# -----------------------------------------------------------------------------
# Array hygiene helpers
# -----------------------------------------------------------------------------


def _as_float_array(A: Any) -> np.ndarray:
    """
    Return a C-contiguous float64 ndarray view or copy of A.

    Parameters
    ----------
    A : Any
        Array-like object representing an adjacency or weight matrix.

    Returns
    -------
    np.ndarray
        C-contiguous float64 matrix.
    """
    return np.asarray(A, dtype=float, order="C")


def _zero_diagonal_inplace(M: np.ndarray) -> None:
    """
    Force an exact zero diagonal in-place.

    Parameters
    ----------
    M : np.ndarray
        Square matrix to be modified in-place.
    """
    np.fill_diagonal(M, 0.0)


def _ensure_symmetric(M: np.ndarray, name: str = "matrix") -> np.ndarray:
    """
    Ensure symmetry within numerical tolerance.

    If symmetry is violated, symmetrize with 0.5*(M + M.T) and emit a warning.

    Parameters
    ----------
    M : np.ndarray
        Square matrix.
    name : str
        Name used in warning messages.

    Returns
    -------
    np.ndarray
        Symmetric matrix (may be a new array if symmetrization is needed).
    """
    if not np.allclose(M, M.T, atol=1e-12, rtol=1e-12):
        logger.warning("%s is not symmetric, symmetrizing as 0.5*(M+M.T).", name)
        M = 0.5 * (M + M.T)
    return M


def _has_negative(M: np.ndarray) -> bool:
    """
    Return True if any entry is negative beyond numerical tolerance.

    Parameters
    ----------
    M : np.ndarray

    Returns
    -------
    bool
    """
    return bool(np.any(M < -_INT_TOL))


def _is_binary_like(M: np.ndarray) -> bool:
    """
    Return True if all entries are close to 0 or 1.

    Parameters
    ----------
    M : np.ndarray

    Returns
    -------
    bool
    """
    return bool(
        np.all(np.isclose(M, 0.0, atol=_INT_TOL) | np.isclose(M, 1.0, atol=_INT_TOL))
    )


def _has_fractional_pos_weights(W: np.ndarray) -> bool:
    """
    Return True if any strictly positive weight is not close to an integer.

    Parameters
    ----------
    W : np.ndarray

    Returns
    -------
    bool
    """
    pos = W > _INT_TOL
    if not np.any(pos):
        return False
    w = W[pos]
    return not bool(np.allclose(w, np.round(w), atol=1e-12))


def _split_signed_layers(
    A: np.ndarray, Aneg: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Construct (Apos, Aneg) binary layers for signed modeling.

    Two supported inputs:
    (i) Explicit pair (A, Aneg): both thresholded as 1{>0}.
    (ii) Single signed A: sign-binarize Apos=1{A>0}, Aneg=1{A<0}.

    Symmetry and zero diagonal are enforced on both layers.

    Parameters
    ----------
    A : np.ndarray
        Positive layer (if Aneg is provided) or signed adjacency (if Aneg is None).
    Aneg : np.ndarray, optional
        Negative layer when explicitly provided.

    Returns
    -------
    (np.ndarray, np.ndarray)
        (Apos, Aneg) as int arrays with entries in {0,1}.
    """
    if Aneg is not None:
        Apos = (_as_float_array(A) > 0).astype(np.int8)
        Aneg2 = (_as_float_array(Aneg) > 0).astype(np.int8)
        if Apos.shape != Aneg2.shape:
            raise ValueError("A (Apos) and Aneg must have the same shape.")
        Apos = _ensure_symmetric(Apos.astype(float), "Apos").astype(np.int8)
        Aneg2 = _ensure_symmetric(Aneg2.astype(float), "Aneg").astype(np.int8)
        _zero_diagonal_inplace(Apos)
        _zero_diagonal_inplace(Aneg2)
        return Apos.astype(int), Aneg2.astype(int)

    M = _as_float_array(A)
    M = _ensure_symmetric(M, "signed adjacency")
    _zero_diagonal_inplace(M)

    Apos = (M > 0).astype(int)
    Aneg2 = (M < 0).astype(int)
    return Apos, Aneg2


def _as_weighted_matrix(
    W: np.ndarray, allow_abs_on_negative: bool = True
) -> np.ndarray:
    """
    Ensure a nonnegative, symmetric weighted matrix with zero diagonal.

    If negatives are present and allow_abs_on_negative=True, abs(W) is used
    and a warning is emitted.

    Parameters
    ----------
    W : np.ndarray
        Weight matrix.
    allow_abs_on_negative : bool
        Whether to coerce negatives by abs(W).

    Returns
    -------
    np.ndarray
        Nonnegative symmetric matrix with zero diagonal.
    """
    W = _as_float_array(W)
    if _has_negative(W):
        if allow_abs_on_negative:
            logger.warning("Negative weights detected in weighted mode, using abs(W).")
            W = np.abs(W)
        else:
            raise ValueError("Negative weights are not supported in weighted mode.")
    W = _ensure_symmetric(W, "weight matrix")
    _zero_diagonal_inplace(W)
    return W


# -----------------------------------------------------------------------------
# Initializer handling
# -----------------------------------------------------------------------------


def _build_initializer(
    mode: str,
    G: nx.Graph,
    A: np.ndarray,
    *,
    Apos: Optional[np.ndarray] = None,
    Aneg: Optional[np.ndarray] = None,
    W: Optional[np.ndarray] = None,
    key: str = "modularity",
) -> list[set[int]]:
    """
    Build an initial partition from a string key.

    The initializer returns a list of sets compatible with the Leiden pipelines.

    Supported keys
    --------------
    - binary  : "modularity"
    - signed  : "modularity", "pos_modularity"
    - weighted: "modularity"

    Parameters
    ----------
    mode : str
        One of {"binary","signed","weighted"}.
    G : nx.Graph
        Graph used for modularity-based initializations.
    A : np.ndarray
        Matrix used to derive auxiliary graphs when needed.
    Apos, Aneg : np.ndarray, optional
        Signed layers, used when mode="signed".
    W : np.ndarray, optional
        Weight matrix, used when mode="weighted".
    key : str
        Initialization strategy.

    Returns
    -------
    list[set[int]]
        Communities as sets of node indices.
    """
    k = key.lower().strip()

    if mode == "signed":
        if Apos is None or Aneg is None:
            Apos, Aneg = _split_signed_layers(A)
        if k == "modularity":
            Aunion = ((Apos > 0) | (Aneg > 0)).astype(int)
            G_mod = nx.from_numpy_array(Aunion, create_using=nx.Graph)
            comms = list(
                nx.algorithms.community.greedy_modularity_communities(
                    G_mod, weight="weight"
                )
            )
            return [set(C) for C in comms]
        if k in {"pos_modularity", "positive_modularity"}:
            G_pos = nx.from_numpy_array(Apos, create_using=nx.Graph)
            comms = list(
                nx.algorithms.community.greedy_modularity_communities(
                    G_pos, weight="weight"
                )
            )
            return [set(C) for C in comms]
        raise ValueError(
            "For mode='signed', initial_partition must be 'modularity' or 'pos_modularity'."
        )

    if mode == "weighted":
        if W is None:
            W = _as_weighted_matrix(A)
        if k == "modularity":
            G_w = nx.from_numpy_array(W, create_using=nx.Graph)
            comms = list(
                nx.algorithms.community.greedy_modularity_communities(
                    G_w, weight="weight"
                )
            )
            return [set(C) for C in comms]
        raise ValueError("For mode='weighted', initial_partition must be 'modularity'.")

    # mode == "binary"
    if k == "modularity":
        comms = list(
            nx.algorithms.community.greedy_modularity_communities(G, weight="weight")
        )
        return [set(C) for C in comms]
    raise ValueError("For mode='binary', initial_partition must be 'modularity'.")


def _maybe_make_initializer(
    mode: str,
    initial_partition: Any,
    *,
    G: nx.Graph,
    A: np.ndarray,
    Apos: Optional[np.ndarray] = None,
    Aneg: Optional[np.ndarray] = None,
    W: Optional[np.ndarray] = None,
) -> Any:
    """
    Accept None, str, or a partition-like object and return a partition initializer.

    If a supported string is provided, a list-of-sets partition is built.

    Parameters
    ----------
    mode : str
        One of {"binary","signed","weighted"}.
    initial_partition : Any
        None, string key, or partition-like object.
    G, A, Apos, Aneg, W : see _build_initializer.

    Returns
    -------
    Any
        None, list-of-sets, or the original partition-like object.
    """
    if initial_partition is None:
        return None
    if isinstance(initial_partition, str):
        key = initial_partition.lower().strip()
        if key in {"none", "singleton", "singletons"}:
            return None
        return _build_initializer(mode, G, A, Apos=Apos, Aneg=Aneg, W=W, key=key)
    return initial_partition


# -----------------------------------------------------------------------------
# Public core API: detect_communities
# -----------------------------------------------------------------------------


def detect_communities(
    G: nx.Graph,
    A: np.ndarray,
    *,
    mode: str = "binary",
    Aneg: Optional[np.ndarray] = None,
    degree_corrected: bool = False,
    initial_partition: Any = None,
    theta: float = 0.0,
    gamma: float = 0.0,
    max_outer: int = 5,
    do_macro_merge: bool = False,
    target_K: Optional[int] = None,
    fix_x: Optional[bool] = None,
) -> Tuple[Partition, float]:
    """
    Run Leiden-based BIC optimization under the selected mode and model family.

    Parameters
    ----------
    G : nx.Graph
        Graph object (used by the Leiden engines and for modularity initializers).
    A : np.ndarray
        Input matrix: adjacency (binary/signed) or weights (weighted mode).
    mode : str
        One of {"binary","signed","weighted"}.
    Aneg : np.ndarray, optional
        Negative layer when mode="signed" and layers are supplied explicitly.
    degree_corrected : bool
        If True, run degree/strength-corrected variants (dc*).
    initial_partition : Any
        None, a supported string key, or a partition-like object.
    theta, gamma : float
        Leiden refinement knobs forwarded to the underlying engine.
    max_outer : int
        Maximum number of outer loops for alternating partition updates and
        model parameter updates (dc* pipelines).
    do_macro_merge : bool
        Whether to greedily merge communities when it improves the objective.
    target_K : int, optional
        If provided, enforce exactly K communities by BIC-aware merges.
    fix_x : bool, optional
        For dc* models: whether to solve node factors once and keep them fixed.

    Returns
    -------
    (Partition, float)
        Best partition (flattened) and its BIC score.
    """
    mode = mode.lower().strip()
    if fix_x is None:
        fix_x = True

    M = _as_float_array(A)
    M = _ensure_symmetric(M, "input matrix")
    _zero_diagonal_inplace(M)

    if mode == "binary":
        has_neg = _has_negative(M)
        is_bin = _is_binary_like(M)

        if has_neg:
            logger.warning(
                "Negative entries detected but mode='binary', binarizing union support 1{|A| > 0}. "
                "Consider mode='signed' for explicit signed modeling."
            )
        elif not is_bin:
            logger.warning(
                "Non-binary values detected but mode='binary', binarizing positive support 1{A > 0}. "
                "Consider mode='weighted' to model weights."
            )

        Abin = (np.abs(M) > 0).astype(int) if has_neg else (M > 0).astype(int)
        init = _maybe_make_initializer("binary", initial_partition, G=G, A=Abin)

        if degree_corrected:
            return iterative_leiden_dcSBM(
                G,
                Abin,
                initial_partition=init,
                theta=theta,
                gamma=gamma,
                max_outer=max_outer,
                do_macro_merge=do_macro_merge,
                target_K=target_K,
                fix_x_ubcm=fix_x,
            )

        return iterative_leiden_SBM(
            G,
            Abin,
            initial_partition=init,
            theta=theta,
            gamma=gamma,
            max_outer=max_outer,
            do_macro_merge=do_macro_merge,
            target_K=target_K,
        )

    if mode == "signed":
        Apos, Aneg_eff = _split_signed_layers(M, Aneg=Aneg)

        raw_nonzero = np.abs(M[np.abs(M) > _INT_TOL])
        if raw_nonzero.size and not np.allclose(raw_nonzero, 1.0, atol=1e-12):
            logger.warning(
                "Signed magnitudes not equal to 1 detected, proceeding by sign-binarization "
                "(Apos=1{A>0}, Aneg=1{A<0})."
            )

        if not np.any(Aneg_eff):
            raise ValueError(
                "mode='signed' requires at least one negative edge, but none were found."
            )

        init = _maybe_make_initializer(
            "signed", initial_partition, G=G, A=M, Apos=Apos, Aneg=Aneg_eff
        )

        if degree_corrected:
            return iterative_leiden_sdcSBM(
                G,
                Apos,
                Aneg_eff,
                initial_partition=init,
                theta=theta,
                gamma=gamma,
                max_outer=max_outer,
                do_macro_merge=do_macro_merge,
                target_K=target_K,
                fix_x_scm=fix_x,
            )

        return iterative_leiden_sSBM(
            G,
            Apos,
            Aneg_eff,
            initial_partition=init,
            theta=theta,
            gamma=gamma,
            max_outer=max_outer,
            do_macro_merge=do_macro_merge,
            target_K=target_K,
        )

    if mode == "weighted":
        W = _as_weighted_matrix(M, allow_abs_on_negative=True)

        if _has_fractional_pos_weights(W):
            logger.warning(
                "Fractional (non-integer) positive weights detected. The geometric maximum-entropy "
                "weight model behaves as a quasi-likelihood in this regime."
            )

        init = _maybe_make_initializer("weighted", initial_partition, G=G, A=W, W=W)

        if degree_corrected:
            return iterative_leiden_wdcSBM(
                G,
                W,
                initial_partition=init,
                theta=theta,
                gamma=gamma,
                max_outer=max_outer,
                do_macro_merge=do_macro_merge,
                target_K=target_K,
                fix_x_wcm=fix_x,
            )

        return iterative_leiden_wSBM(
            G,
            W,
            initial_partition=init,
            theta=theta,
            gamma=gamma,
            max_outer=max_outer,
            do_macro_merge=do_macro_merge,
            target_K=target_K,
        )

    raise ValueError("mode must be one of {'binary','signed','weighted'}")


# -----------------------------------------------------------------------------
# High-level API: detect (post-processing adapter)
# -----------------------------------------------------------------------------


def _normalize_post_arg(
    arg: Union[bool, Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Normalize a post-processing control argument.

    Parameters
    ----------
    arg : bool | dict
        If False: disabled.
        If True : enabled with default kwargs.
        If dict : enabled and kwargs are provided.

    Returns
    -------
    (enabled, kwargs) : (bool, dict)
    """
    if arg is False:
        return False, {}
    if arg is True:
        return True, {}
    if isinstance(arg, dict):
        return True, dict(arg)
    raise TypeError("viz/report must be bool or dict.")


def detect(
    G: nx.Graph,
    A: np.ndarray,
    *,
    mode: str = "binary",
    Aneg: Optional[np.ndarray] = None,
    degree_corrected: bool = False,
    initial_partition: Any = None,
    theta: float = 0.0,
    gamma: float = 0.0,
    max_outer: int = 5,
    do_macro_merge: bool = False,
    target_K: Optional[int] = None,
    fix_x: Optional[bool] = None,
    viz: Union[bool, Dict[str, Any]] = False,
    report: Union[bool, Dict[str, Any]] = False,
) -> Dict[str, Any]:
    """
    Full pipeline: detect communities, optionally visualize and optionally print diagnostics.

    Only two parameters control post-processing:
      - viz: bool | dict
      - report: bool | dict

    The remaining parameters match detect_communities and provide model control.

    Returns
    -------
    dict
        Always includes:
            "partition": Partition
            "bic": float
        May include extra fields returned by process_graph (e.g., "pos").
    """
    part, bic = detect_communities(
        G,
        A,
        mode=mode,
        Aneg=Aneg,
        degree_corrected=degree_corrected,
        initial_partition=initial_partition,
        theta=theta,
        gamma=gamma,
        max_outer=max_outer,
        do_macro_merge=do_macro_merge,
        target_K=target_K,
        fix_x=fix_x,
    )

    out: Dict[str, Any] = {"partition": part, "bic": float(bic)}

    viz_enabled, viz_kwargs = _normalize_post_arg(viz)
    rep_enabled, rep_kwargs = _normalize_post_arg(report)

    if not viz_enabled and not rep_enabled:
        return out

    # Import locally to avoid hard coupling core solver logic to plotting stacks.
    from .represent_and_analyze import (
        process_graph,  # pylint: disable=import-outside-toplevel
    )

    mode2 = mode.lower().strip()

    # Heuristic defaults: if report=True, ensure print_info=True unless user overrides.
    if rep_enabled and (report is True) and ("print_info" not in rep_kwargs):
        rep_kwargs["print_info"] = True

    # Merge keyword arguments for downstream process_graph.
    post_kwargs: Dict[str, Any] = {}
    post_kwargs.update(viz_kwargs)
    post_kwargs.update(rep_kwargs)

    # Backwards compatibility:
    # - If process_graph supports viz/report keywords, pass them.
    # - Otherwise, forward dict content as plain kwargs.
    # The implementation attempts the newer signature first and falls back on TypeError.
    def _call_process_graph_signed(Apos2: np.ndarray, Aneg2: np.ndarray) -> Any:
        try:
            return process_graph(
                G, part, Apos=Apos2, Aneg=Aneg2, viz=viz, report=report
            )
        except TypeError:
            return process_graph(G, part, Apos=Apos2, Aneg=Aneg2, **post_kwargs)

    def _call_process_graph_plain() -> Any:
        try:
            return process_graph(G, part, viz=viz, report=report)
        except TypeError:
            return process_graph(G, part, **post_kwargs)

    if mode2 == "signed":
        M = _as_float_array(A)
        M = _ensure_symmetric(M, "input matrix")
        _zero_diagonal_inplace(M)
        Apos2, Aneg2 = _split_signed_layers(M, Aneg=Aneg)
        post = _call_process_graph_signed(Apos2, Aneg2)
    else:
        post = _call_process_graph_plain()

    if isinstance(post, dict):
        out.update(post)
    return out
