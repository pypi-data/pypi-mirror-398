from __future__ import annotations

# NOTE:
# The domino package uses a src-layout (src/domino/). During development,
# some public symbols may migrate across submodules. The import below keeps
# the public API stable while avoiding hard failures at import time.
from .repro import coerce_random_state

try:
    # Preferred location if GraphKeys is defined in utils/constants.py
    from .constants import GraphKeys
except ImportError:
    # Backward/forward compatible fallback (current location in your tree)
    from ..leiden.partitions_functions import GraphKeys

__all__ = [
    "GraphKeys",
    "coerce_random_state",
]
