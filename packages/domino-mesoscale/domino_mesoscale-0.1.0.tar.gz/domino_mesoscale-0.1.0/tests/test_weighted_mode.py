"""tests/test_weighted_mode.py

Integration test for the weighted (non-degree-corrected) pipeline.

The test uses a small integer-weight SBM instance and verifies that the
geometric wSBM objective can be optimized without raising errors.
"""

from __future__ import annotations

import numpy as np

from domino import detect_communities
from domino.leiden.partitions_functions import Partition

from .conftest import sbm_weighted


def test_detect_weighted_wsbm_small() -> None:
    """The weighted SBM pipeline should return a finite BIC and a valid partition."""
    inst = sbm_weighted(n=100)
    assert np.all(inst.A >= 0)
    assert np.any(inst.A > 0), (
        "Synthetic weighted instance must have at least one edge."
    )

    part, bic = detect_communities(
        inst.G,
        inst.A,
        mode="weighted",
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
