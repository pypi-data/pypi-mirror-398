"""tests/test_signed_mode.py

Integration test for the signed (non-degree-corrected) pipeline.

The test uses a signed SBM-like instance with positive within-block edges and
negative between-block edges. This ensures the signed objective is exercised.
"""

from __future__ import annotations

import numpy as np

from domino import detect_communities
from domino.leiden.partitions_functions import Partition

from .conftest import sbm_signed


def test_detect_signed_ssbm_small() -> None:
    """The signed SBM pipeline should require negative edges and return a valid partition."""
    inst = sbm_signed(n=100)
    assert np.any(inst.A < 0), "Synthetic signed instance must contain negative edges."

    part, bic = detect_communities(
        inst.G,
        inst.A,
        mode="signed",
        degree_corrected=False,
        max_outer=3,
        theta=0.0,
        gamma=0.0,
    )

    assert isinstance(bic, float)
    assert np.isfinite(bic)
    assert isinstance(part, Partition)
    assert Partition.is_partition(inst.G, part)
    assert 1 <= len(part) <= inst.A.shape[0]
