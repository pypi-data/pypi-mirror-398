"""
DOMINO

Detection Of MesoscopIc structures via iNfOrmation criteria.

Public API
----------
The package exposes two stable entry points:

- detect:
    High-level pipeline that runs community detection and optionally performs
    post-processing (visualization and/or reporting).

- detect_communities:
    Core solver that returns (Partition, bic) without side effects.

All other modules (Leiden internals, ERGM solvers, iterative pipelines, plotting
utilities) are available under the domino.* namespace, but are not part of the
top-level stability contract.
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Silence Intel OpenMP deprecation messages (must run before importing numpy/scipy/numba)
# -----------------------------------------------------------------------------
import os

os.environ.setdefault("KMP_WARNINGS", "0")

import logging
from importlib.metadata import PackageNotFoundError, version

from .detect import detect, detect_communities

__all__ = ["detect", "detect_communities", "__version__"]

# Ensure importing the package never configures logging globally.
logging.getLogger(__name__).addHandler(logging.NullHandler())

try:
    __version__ = version("domino-mesoscale")
except PackageNotFoundError:
    __version__ = "0.0.0"
