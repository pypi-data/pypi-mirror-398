"""
represent_and_analyze.py

Unified helpers to:
  - normalize and relabel community assignments
  - visualize community-colored networks (binary or signed), with robust defaults
  - visualize reordered adjacency matrices efficiently, with diagonal block contours
  - compute and print community diagnostics with safeguards

Exports (stable API):
  - process_graph
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from scipy import sparse

logger = logging.getLogger("domino.viz")


# -----------------------------------------------------------------------------
# Basic conversion and relabeling
# -----------------------------------------------------------------------------


def partition_to_dict(part: Iterable[Iterable[Any]]) -> Dict[Any, int]:
    """
    Convert a Partition-like object into a mapping {node: community_id}.

    The conversion is deterministic given the iteration order of the communities.
    """
    mapping: Dict[Any, int] = {}
    for idx, comm in enumerate(part):
        for node in comm:
            mapping[node] = int(idx)
    return mapping


def standardize_communities(G: nx.Graph, communities: Any) -> Dict[Any, int]:
    """
    Normalize community assignments into a dict {node: label} aligned to sorted(G.nodes()).

    Accepted formats
    ----------------
    dict:
        Interpreted as {node: label}.
    list | np.ndarray:
        Interpreted as a label vector aligned to sorted(G.nodes()).
    Partition-like:
        Iterable of iterables, each inner iterable defines a community.
    """
    node_list = sorted(G.nodes())
    if isinstance(communities, dict):
        return {n: int(communities[n]) for n in node_list}
    if isinstance(communities, (list, np.ndarray)):
        if len(communities) != len(node_list):
            raise ValueError("Label vector length does not match number of nodes.")
        return {node_list[i]: int(communities[i]) for i in range(len(node_list))}
    return partition_to_dict(communities)


def relabel_communities_sorted(C: Dict[Any, int]) -> Dict[Any, int]:
    """
    Relabel community ids to contiguous 0..K-1 in a deterministic manner.

    The mapping is induced by scanning nodes in sorted order and assigning new
    labels in order of first appearance.
    """
    mapping: Dict[int, int] = {}
    next_id = 0
    out: Dict[Any, int] = {}
    for n in sorted(C.keys()):
        old = int(C[n])
        if old not in mapping:
            mapping[old] = next_id
            next_id += 1
        out[n] = mapping[old]
    return out


def _degrees_from_adjacency(adj: Union[np.ndarray, sparse.spmatrix]) -> np.ndarray:
    """
    Compute degrees from a dense or sparse adjacency representation.

    The result is returned as a one-dimensional float array.
    """
    if sparse.issparse(adj):
        return np.asarray(adj.sum(axis=1)).ravel().astype(float, copy=False)
    return adj.sum(axis=1).astype(float, copy=False)


def rename_communities_by_connectivity_standard(
    adj_matrix: Union[np.ndarray, sparse.spmatrix],
    community_dict: Dict[Any, int],
) -> Tuple[Dict[Any, int], List[Tuple[int, int, float, Any]]]:
    """
    Rank communities by average node degree (descending) and rename them to 0,1,2,...

    Returns
    -------
    renamed_labels:
        New labels by node after renaming.
    history:
        List of tuples (new_label, old_label, avg_degree, min_node_id) for provenance.
    """
    nodes = sorted(community_dict.keys())
    node_to_idx = {n: i for i, n in enumerate(nodes)}
    degs = _degrees_from_adjacency(adj_matrix)

    stats: Dict[int, Tuple[float, Any]] = {}
    for old in set(community_dict.values()):
        old = int(old)
        members = [n for n in nodes if int(community_dict[n]) == old]
        if members:
            idx = [node_to_idx[n] for n in members]
            avg = float(np.mean(degs[idx]))
            stats[old] = (avg, min(members))
        else:
            stats[old] = (0.0, float("inf"))

    # Order by average degree (desc), then by smallest node id (asc)
    order = sorted(stats.items(), key=lambda x: (-x[1][0], x[1][1]))
    label_map = {old: new for new, (old, _) in enumerate(order)}
    renamed = {n: label_map[int(community_dict[n])] for n in nodes}

    hist: List[Tuple[int, int, float, Any]] = []
    for new, (old, (avg, mmin)) in enumerate(order):
        hist.append((new, old, float(avg), mmin))
    return renamed, hist


def connectivity_info_string(
    sorted_connectivity: List[Tuple[int, int, float, Any]],
    graph_name: str = "Graph",
) -> str:
    """
    Return a compact, human-readable summary of the connectivity-based ranking.
    """
    lines = [f"{graph_name}: community ranking by average degree"]
    for new_label, old_label, avg_degree, _ in sorted_connectivity:
        lines.append(f"  C{new_label} (from {old_label}), AvgDeg={avg_degree:.4f}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Layout helpers
# -----------------------------------------------------------------------------


def _to_nx_seed(obj: Any, default: int = 42) -> Any:
    """
    Convert a random-state-like object into a NetworkX-compatible seed.

    Accepts integers, NumPy RNG objects, random.Random, or hashable objects.
    """
    if obj is None:
        return int(default)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    try:
        if isinstance(obj, (np.random.RandomState, np.random.Generator)):  # type: ignore[attr-defined]
            return obj
    except Exception:
        pass
    if isinstance(obj, random.Random):
        return obj.randrange(0, 2**32 - 1)
    try:
        return abs(hash(obj)) % (2**32 - 1)
    except Exception:
        return int(default)


def community_layout(
    G: nx.Graph,
    labels: Dict[Any, int],
    pos: Optional[Dict[Any, Tuple[float, float]]] = None,
    seed: int = 42,
    random_state: Optional[Any] = None,
) -> Dict[Any, Tuple[float, float]]:
    """
    Community-grid layout: each community is laid out by a local spring layout and
    then placed on a coarse grid.

    The procedure aims to produce stable and interpretable placements across datasets.
    """
    if pos is not None:
        return pos

    seed_for_nx = _to_nx_seed(
        random_state if random_state is not None else seed, default=seed
    )

    comm_to_nodes: Dict[int, List[Any]] = {}
    for n, c in labels.items():
        comm_to_nodes.setdefault(int(c), []).append(n)

    comms = sorted(comm_to_nodes.keys())
    grid = int(math.ceil(math.sqrt(len(comms)))) or 1

    out: Dict[Any, Tuple[float, float]] = {}
    for idx, c in enumerate(comms):
        sub = G.subgraph(comm_to_nodes[c])
        local = nx.spring_layout(sub, seed=seed_for_nx)
        r, col = divmod(idx, grid)
        offset = np.array([col * 3.0, r * 3.0], dtype=float)
        for n, p in local.items():
            out[n] = (np.asarray(p, dtype=float) + offset).astype(float)
    return out


def kshell_layout(
    G: nx.Graph, shell_gap: float = 1.5
) -> Dict[Any, Tuple[float, float]]:
    """
    Deterministic k-shell radial layout, higher core number nodes are closer to the origin.
    """
    core = nx.core_number(G)
    kmax = max(core.values()) if core else 0
    shells: Dict[int, List[Any]] = {}
    for n, k in core.items():
        shells.setdefault(int(k), []).append(n)

    pos: Dict[Any, Tuple[float, float]] = {}
    for k, nodes in shells.items():
        R = (kmax - k + 1) * shell_gap
        m = len(nodes) or 1
        for i, n in enumerate(nodes):
            a = 2.0 * np.pi * i / m
            pos[n] = (float(R * np.cos(a)), float(R * np.sin(a)))
    return pos


# -----------------------------------------------------------------------------
# Visualization helpers (robust defaults)
# -----------------------------------------------------------------------------


def _auto_figsize(
    n: int, base: float = 6.0, max_side: float = 12.0
) -> Tuple[float, float]:
    """
    Choose a square figure size that scales mildly with n and saturates.
    """
    side = min(max_side, max(base, base + 0.005 * float(n)))
    return float(side), float(side)


def _auto_node_size(n: int, min_size: float = 4.0, max_size: float = 80.0) -> float:
    """
    Choose a node marker size that decreases with n and is clipped.
    """
    if n <= 0:
        return float(max_size)
    s = 3000.0 / math.sqrt(float(n))
    return float(min(max_size, max(min_size, s)))


def _auto_linewidth(n: int, min_lw: float = 0.1, max_lw: float = 1.0) -> float:
    """
    Choose an edge linewidth that decreases with n and is clipped.
    """
    if n <= 0:
        return float(max_lw)
    lw = 4.0 / math.sqrt(float(n))
    return float(min(max_lw, max(min_lw, lw)))


def _auto_tick_step(n: int, target_ticks: int = 12) -> int:
    """
    Choose an axis tick step such that roughly target_ticks ticks are displayed.
    """
    if n <= target_ticks:
        return 1
    step = int(math.ceil(n / target_ticks))
    nice = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
    for v in nice:
        if step <= v:
            return v
    return step


def _safe_savefig(fig: plt.Figure, savepath: Optional[str], dpi: int = 300) -> None:
    """
    Save a figure to disk if savepath is provided.
    """
    if savepath is None:
        return
    fig.savefig(savepath, dpi=dpi, bbox_inches="tight")
    logger.info("Saved figure to %s", savepath)


def _graph_to_binary_sparse(G: nx.Graph, nodes: List[Any]) -> sparse.csr_matrix:
    """
    Return a binary (0/1) sparse adjacency matrix for G in the given node order.
    """
    try:
        A = nx.to_scipy_sparse_array(
            G, nodelist=nodes, weight=None, format="csr", dtype=np.int8
        )
        return sparse.csr_matrix(A)
    except Exception:
        A = nx.to_scipy_sparse_matrix(
            G, nodelist=nodes, weight=None, format="csr", dtype=np.int8
        )
        return A.tocsr()


def _coerce_viz(viz: Union[bool, Dict[str, Any], None]) -> Dict[str, Any]:
    """
    Coerce visualization configuration into a dictionary.
    """
    if viz is None:
        return {"enabled": True}
    if isinstance(viz, bool):
        return {"enabled": bool(viz)}
    out = dict(viz)
    out.setdefault("enabled", True)
    return out


def _coerce_report(report: Union[bool, Dict[str, Any], None]) -> Dict[str, Any]:
    """
    Coerce reporting configuration into a dictionary.
    """
    if report is None:
        return {"enabled": False}
    if isinstance(report, bool):
        return {"enabled": bool(report)}
    out = dict(report)
    out.setdefault("enabled", True)
    return out


def visualize_communities(
    G: nx.Graph,
    labels: Dict[Any, int],
    *,
    predefined_colors: Optional[Dict[int, Any]] = None,
    pos: Optional[Dict[Any, Tuple[float, float]]] = None,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    max_layout_nodes: int = 3000,
    max_draw_edges: int = 20000,
    savepath: Optional[str] = None,
    dpi: int = 300,
    show: bool = True,
    close: bool = False,
) -> Tuple[Dict[int, Any], Optional[plt.Figure]]:
    """
    Draw a community-colored graph with stable defaults across network sizes.

    Node labels are intentionally suppressed to preserve readability.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()

    uniq = sorted(set(int(v) for v in labels.values()))
    if predefined_colors is None:
        cmap = plt.get_cmap("tab20")
        colors = {c: cmap(i % 20) for i, c in enumerate(uniq)}
    else:
        colors = predefined_colors

    if n > max_layout_nodes:
        logger.info(
            "Skipping network layout and drawing (n=%d exceeds max_layout_nodes=%d).",
            n,
            max_layout_nodes,
        )
        return colors, None

    if pos is None:
        pos = community_layout(G, labels, pos=None, seed=42, random_state=random_state)

    fig_w, fig_h = _auto_figsize(n)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    node_size = _auto_node_size(n)
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=[colors[int(labels[u])] for u in G.nodes()],
        node_size=node_size,
        alpha=0.9,
        ax=ax,
        linewidths=0.0,
    )

    if m <= max_draw_edges:
        lw = _auto_linewidth(n)
        nx.draw_networkx_edges(G, pos, alpha=0.25, width=lw, ax=ax)
    else:
        logger.info(
            "Skipping edge rendering (m=%d exceeds max_draw_edges=%d).",
            m,
            max_draw_edges,
        )

    ax.set_axis_off()

    if len(uniq) <= 20:
        leg = [Patch(facecolor=colors[c], edgecolor="k", label=f"C{c}") for c in uniq]
        ax.legend(handles=leg, title="Communities", loc="upper right", frameon=True)

    fig.tight_layout()
    _safe_savefig(fig, savepath, dpi=dpi)
    if show:
        plt.show()
    if close:
        plt.close(fig)
    return colors, fig


def visualize_signed_communities(
    G: nx.Graph,
    labels: Dict[Any, int],
    Apos: np.ndarray,
    Aneg: np.ndarray,
    *,
    predefined_colors: Optional[Dict[int, Any]] = None,
    pos: Optional[Dict[Any, Tuple[float, float]]] = None,
    random_state: Optional[Union[int, np.random.Generator, random.Random]] = None,
    max_layout_nodes: int = 3000,
    max_draw_edges: int = 20000,
    savepath: Optional[str] = None,
    dpi: int = 300,
    show: bool = True,
    close: bool = False,
) -> Tuple[Dict[int, Any], Optional[plt.Figure]]:
    """
    Draw a signed graph with community-colored nodes and two edge styles.

    Positive edges are rendered as black solid segments, negative edges as crimson dashed segments.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()

    uniq = sorted(set(int(v) for v in labels.values()))
    if predefined_colors is None:
        cmap = plt.get_cmap("tab20")
        colors = {c: cmap(i % 20) for i, c in enumerate(uniq)}
    else:
        colors = predefined_colors

    if n > max_layout_nodes:
        logger.info(
            "Skipping signed network layout and drawing (n=%d exceeds max_layout_nodes=%d).",
            n,
            max_layout_nodes,
        )
        return colors, None

    if pos is None:
        pos = community_layout(G, labels, pos=None, seed=42, random_state=random_state)

    fig_w, fig_h = _auto_figsize(n)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    node_size = _auto_node_size(n)
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=[colors[int(labels[u])] for u in G.nodes()],
        node_size=node_size,
        alpha=0.9,
        ax=ax,
        linewidths=0.0,
    )

    if m <= max_draw_edges:
        lw = _auto_linewidth(n)
        pos_edges = [(u, v) for u, v in G.edges() if int(Apos[u, v]) == 1]
        neg_edges = [(u, v) for u, v in G.edges() if int(Aneg[u, v]) == 1]

        if pos_edges:
            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=pos_edges,
                alpha=0.20,
                width=lw,
                edge_color="blue",
                ax=ax,
            )
        if neg_edges:
            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=neg_edges,
                alpha=0.30,
                width=lw,
                edge_color="crimson",
                ax=ax,
            )
    else:
        logger.info(
            "Skipping signed edge rendering (m=%d exceeds max_draw_edges=%d).",
            m,
            max_draw_edges,
        )

    ax.set_axis_off()

    legend_edges = [
        Line2D([0], [0], color="blue", lw=2, label="Positive"),
        Line2D([0], [0], color="crimson", lw=2, label="Negative"),
    ]
    ax.legend(handles=legend_edges, loc="upper right", frameon=True)

    fig.tight_layout()
    _safe_savefig(fig, savepath, dpi=dpi)
    if show:
        plt.show()
    if close:
        plt.close(fig)
    return colors, fig


def _block_spans_from_labels(comm_ord: np.ndarray) -> List[Tuple[int, int]]:
    """
    Return contiguous spans [start, end) for each community in an ordered label array.
    """
    n = int(comm_ord.size)
    if n == 0:
        return []
    spans: List[Tuple[int, int]] = []
    start = 0
    for i in range(1, n):
        if comm_ord[i] != comm_ord[i - 1]:
            spans.append((start, i))
            start = i
    spans.append((start, n))
    return spans


def plot_reordered_adjacency_matrix_by_connectivity(
    G: nx.Graph,
    labels: Dict[Any, int],
    *,
    max_n_dense: int = 6000,
    target_ticks: int = 12,
    block_lw: float = 2.0,
    savepath: Optional[str] = None,
    dpi: int = 300,
    show: bool = True,
    close: bool = False,
) -> plt.Figure:
    """
    Plot a community-reordered binary adjacency matrix with diagonal block contours.

    Axis tick labels are numeric indices in the reordered matrix, and the tick density
    is adapted to the network size.
    """
    nodes = sorted(G.nodes())
    n = len(nodes)

    A = _graph_to_binary_sparse(G, nodes)
    A.setdiag(0)
    A.eliminate_zeros()

    comm = np.array([int(labels[u]) for u in nodes], dtype=int)
    order = np.lexsort((np.arange(n), comm))
    comm_ord = comm[order]
    A_ord = A[order, :][:, order]

    fig_w, fig_h = _auto_figsize(n, base=6.0, max_side=12.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    if n <= max_n_dense:
        M = A_ord.toarray()
        ax.imshow(M, interpolation="nearest", aspect="equal", cmap="Greys")
    else:
        ax.spy(A_ord, markersize=0.5, aspect="equal")

    step = _auto_tick_step(n, target_ticks=target_ticks)
    ticks = np.arange(0, n, step)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels([str(int(t)) for t in ticks], rotation=90)
    ax.set_yticklabels([str(int(t)) for t in ticks])

    spans = _block_spans_from_labels(comm_ord)
    for a, b in spans:
        rect = Rectangle(
            (a - 0.5, a - 0.5),
            b - a,
            b - a,
            fill=False,
            edgecolor="k",
            linewidth=block_lw,
        )
        ax.add_patch(rect)

    # ax.set_title("Reordered adjacency (by community)")
    fig.tight_layout()
    _safe_savefig(fig, savepath, dpi=dpi)
    if show:
        plt.show()
    if close:
        plt.close(fig)
    return fig


def plot_reordered_signed_adjacency(
    Apos: np.ndarray,
    Aneg: np.ndarray,
    labels: Dict[Any, int],
    *,
    max_n_dense: int = 6000,
    target_ticks: int = 12,
    block_lw: float = 2.0,
    savepath: Optional[str] = None,
    dpi: int = 300,
    show: bool = True,
    close: bool = False,
) -> plt.Figure:
    """
    Plot a community-reordered signed adjacency matrix with diagonal block contours.

    For large n, the routine switches to a sparse visualization that preserves the
    sparsity pattern, but does not encode the sign.
    """
    n = int(Apos.shape[0])
    comm = np.array([int(labels[i]) for i in range(n)], dtype=int)
    order = np.lexsort((np.arange(n), comm))
    comm_ord = comm[order]

    P = sparse.csr_matrix(Apos.astype(np.int8))
    N = sparse.csr_matrix(Aneg.astype(np.int8))
    S = (P - N).tocsr()
    S.setdiag(0)
    S.eliminate_zeros()
    S_ord = S[order, :][:, order]

    fig_w, fig_h = _auto_figsize(n, base=6.0, max_side=12.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    if n <= max_n_dense:
        M = S_ord.toarray()
        from matplotlib.colors import BoundaryNorm, ListedColormap

        cmap = ListedColormap(["#d62728", "white", "#1f77b4"])
        norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap.N)
        ax.imshow(M, interpolation="nearest", aspect="equal", cmap=cmap, norm=norm)
    else:
        ax.spy(S_ord, markersize=0.5, aspect="equal")

    step = _auto_tick_step(n, target_ticks=target_ticks)
    ticks = np.arange(0, n, step)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels([str(int(t)) for t in ticks], rotation=90)
    ax.set_yticklabels([str(int(t)) for t in ticks])

    spans = _block_spans_from_labels(comm_ord)
    for a, b in spans:
        rect = Rectangle(
            (a - 0.5, a - 0.5),
            b - a,
            b - a,
            fill=False,
            edgecolor="k",
            linewidth=block_lw,
        )
        ax.add_patch(rect)

    ax.set_title("Reordered signed adjacency (by community)")
    fig.tight_layout()
    _safe_savefig(fig, savepath, dpi=dpi)
    if show:
        plt.show()
    if close:
        plt.close(fig)
    return fig


# -----------------------------------------------------------------------------
# Analysis helpers
# -----------------------------------------------------------------------------


def community_block_matrix(G: nx.Graph, labels: Dict[Any, int]) -> np.ndarray:
    """
    Return the community block matrix B[a,b] counting edges between communities.
    """
    k = max(labels.values()) + 1 if labels else 0
    B = np.zeros((k, k), dtype=int)
    for u, v in G.edges():
        cu, cv = int(labels[u]), int(labels[v])
        B[cu, cv] += 1
        if cu != cv:
            B[cv, cu] += 1
    return B


def average_degree_by_community(G: nx.Graph, labels: Dict[Any, int]) -> np.ndarray:
    """
    Return the average binary degree per community.
    """
    k = max(labels.values()) + 1 if labels else 0
    s = np.zeros(k, dtype=float)
    c = np.zeros(k, dtype=int)
    for n, g in G.degree():
        lab = int(labels[n])
        s[lab] += float(g)
        c[lab] += 1
    out = np.zeros(k, dtype=float)
    nz = c > 0
    out[nz] = s[nz] / c[nz]
    return out


def average_signed_degree_by_community(
    Apos: np.ndarray,
    Aneg: np.ndarray,
    labels: Dict[Any, int],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return the average positive and negative degrees per community.

    The function assumes nodes are indexed as 0..N-1, consistent with matrices Apos/Aneg.
    """
    k = max(labels.values()) + 1 if labels else 0
    pos_deg = Apos.sum(axis=1).astype(float)
    neg_deg = Aneg.sum(axis=1).astype(float)

    s_pos = np.zeros(k, dtype=float)
    s_neg = np.zeros(k, dtype=float)
    cnt = np.zeros(k, dtype=int)

    for n, lab in labels.items():
        i = int(n)
        c = int(lab)
        s_pos[c] += float(pos_deg[i])
        s_neg[c] += float(neg_deg[i])
        cnt[c] += 1

    avg_pos = np.zeros(k, dtype=float)
    avg_neg = np.zeros(k, dtype=float)
    nz = cnt > 0
    avg_pos[nz] = s_pos[nz] / cnt[nz]
    avg_neg[nz] = s_neg[nz] / cnt[nz]
    return avg_pos, avg_neg


def analyze_communities(
    G: nx.Graph,
    labels: Dict[Any, int],
    *,
    node_names: Optional[Dict[Any, str]] = None,
    Apos: Optional[np.ndarray] = None,
    Aneg: Optional[np.ndarray] = None,
    max_print_k: int = 30,
    max_members_per_comm: int = 50,
) -> None:
    """
    Print community diagnostics with safeguards for large partitions.

    The routine prints:
      1) The block matrix (only if K <= max_print_k),
      2) Average degree statistics,
      3) Community member lists (truncated to max_members_per_comm).
    """
    k = max(labels.values()) + 1 if labels else 0

    B = community_block_matrix(G, labels)
    avg_union = average_degree_by_community(G, labels)
    order = sorted(range(len(avg_union)), key=lambda c: (-avg_union[c], c))

    if k <= max_print_k:
        B_ord = B[np.ix_(order, order)]
        print("\nCommunity block matrix (reordered by avg degree desc):")
        print(B_ord)
    else:
        print(
            f"\nCommunity block matrix not printed (K={k} exceeds max_print_k={max_print_k})."
        )

    if (Apos is not None) and (Aneg is not None):
        avg_pos, avg_neg = average_signed_degree_by_community(Apos, Aneg, labels)
        print("\nAverage positive and negative degree by community:")
        for new, old in enumerate(order):
            print(f"Community {new}: +{avg_pos[old]:.2f}   -{avg_neg[old]:.2f}")
    else:
        print("\nAverage degree by community:")
        for new, old in enumerate(order):
            print(f"Community {new}: {avg_union[old]:.2f}")

    members: Dict[int, List[Any]] = {}
    for n, c in labels.items():
        members.setdefault(int(c), []).append(n)

    print("\nCommunity members:")
    for new, old in enumerate(order):
        mlist = sorted(members.get(old, []))
        display = [
            node_names[n] if (node_names and n in node_names) else n for n in mlist
        ]
        if len(display) > max_members_per_comm:
            head = display[:max_members_per_comm]
            print(
                f"Community {new} (size={len(display)}), first {max_members_per_comm} members:"
            )
            print(", ".join(map(str, head)) + ", ...")
        else:
            print(f"Community {new} (size={len(display)}):")
            print(", ".join(map(str, display)))
        print()


# -----------------------------------------------------------------------------
# Pipeline: process_graph
# -----------------------------------------------------------------------------


def process_graph(
    G: nx.Graph,
    detected_labels: Any,
    *,
    Apos: Optional[np.ndarray] = None,
    Aneg: Optional[np.ndarray] = None,
    viz: Union[bool, Dict[str, Any], None] = True,
    report: Union[bool, Dict[str, Any], None] = False,
) -> Dict[str, Any]:
    """
    Unified post-processing: label normalization, optional visualization, optional reporting.

    Parameters
    ----------
    viz
        If True, uses default visualization settings. If a dict, it specifies:
            enabled: bool
            show: bool
            close: bool
            save_dir: Optional[str]
            prefix: str
            dpi: int
            layout: str in {"community","kshell","kamada","auto"}
            max_layout_nodes: int
            max_draw_edges: int
            max_n_dense: int
            target_ticks: int
            block_lw: float
            random_state: optional RNG seed for layouts
            pos: optional external node positions
    report
        If True, prints default diagnostics. If a dict, it may specify:
            enabled: bool
            graph_name: str
            node_names: Optional[Dict[Any,str]]
            max_print_k: int
            max_members_per_comm: int

    Returns
    -------
    dict
        A dictionary containing standardized labels and (when computed) plot objects.
    """
    viz_cfg = _coerce_viz(viz)
    rep_cfg = _coerce_report(report)

    std = standardize_communities(G, detected_labels)
    contig = relabel_communities_sorted(std)

    nodes = sorted(G.nodes())
    A_bin = _graph_to_binary_sparse(G, nodes)
    final_labels, sorted_conn = rename_communities_by_connectivity_standard(
        A_bin, contig
    )

    out: Dict[str, Any] = {
        "labels": final_labels,
        "connectivity_history": sorted_conn,
    }

    if rep_cfg.get("enabled", False):
        graph_name = str(rep_cfg.get("graph_name", "Graph"))
        print(connectivity_info_string(sorted_conn, graph_name=graph_name))
        analyze_communities(
            G,
            final_labels,
            node_names=rep_cfg.get("node_names", None),
            Apos=Apos,
            Aneg=Aneg,
            max_print_k=int(rep_cfg.get("max_print_k", 30)),
            max_members_per_comm=int(rep_cfg.get("max_members_per_comm", 50)),
        )

    if not viz_cfg.get("enabled", True):
        return out

    save_dir = viz_cfg.get("save_dir", None)
    prefix = str(viz_cfg.get("prefix", "domino"))
    dpi = int(viz_cfg.get("dpi", 300))
    show = bool(viz_cfg.get("show", True))
    close = bool(viz_cfg.get("close", False))

    layout = str(viz_cfg.get("layout", "auto")).lower().strip()
    max_layout_nodes = int(viz_cfg.get("max_layout_nodes", 3000))
    max_draw_edges = int(viz_cfg.get("max_draw_edges", 20000))
    max_n_dense = int(viz_cfg.get("max_n_dense", 6000))
    target_ticks = int(viz_cfg.get("target_ticks", 12))
    block_lw = float(viz_cfg.get("block_lw", 2.0))
    random_state = viz_cfg.get("random_state", None)
    pos = viz_cfg.get("pos", None)

    def _path(name: str) -> Optional[str]:
        if save_dir is None:
            return None
        return f"{str(save_dir).rstrip('/')}/{prefix}_{name}.pdf"

    if pos is None:
        if layout in {"auto", "community"}:
            pos = None
        elif layout == "kshell":
            pos = kshell_layout(G, shell_gap=float(viz_cfg.get("shell_gap", 1.5)))
        elif layout == "kamada":
            pos = nx.kamada_kawai_layout(G, weight="weight")
        else:
            pos = None

    if Apos is not None and Aneg is not None:
        colors, fig_net = visualize_signed_communities(
            G,
            final_labels,
            Apos,
            Aneg,
            pos=pos,
            random_state=random_state,
            max_layout_nodes=max_layout_nodes,
            max_draw_edges=max_draw_edges,
            savepath=_path("signed_graph"),
            dpi=dpi,
            show=show,
            close=close,
        )
        fig_adj = plot_reordered_signed_adjacency(
            Apos,
            Aneg,
            final_labels,
            max_n_dense=max_n_dense,
            target_ticks=target_ticks,
            block_lw=block_lw,
            savepath=_path("signed_adjacency"),
            dpi=dpi,
            show=show,
            close=close,
        )
    else:
        colors, fig_net = visualize_communities(
            G,
            final_labels,
            pos=pos,
            random_state=random_state,
            max_layout_nodes=max_layout_nodes,
            max_draw_edges=max_draw_edges,
            savepath=_path("graph"),
            dpi=dpi,
            show=show,
            close=close,
        )
        fig_adj = plot_reordered_adjacency_matrix_by_connectivity(
            G,
            final_labels,
            max_n_dense=max_n_dense,
            target_ticks=target_ticks,
            block_lw=block_lw,
            savepath=_path("adjacency"),
            dpi=dpi,
            show=show,
            close=close,
        )

    out["colors"] = colors
    out["pos"] = pos
    out["fig_network"] = fig_net
    out["fig_adjacency"] = fig_adj
    return out
