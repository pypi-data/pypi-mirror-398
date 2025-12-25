"""tests/test_binary_mode.py

Integration test for the binary (non-degree-corrected) pipeline.

The test runs the full Leiden+BIC loop on a small synthetic SBM instance.
It validates that the routine terminates and returns a valid partition.
"""

from __future__ import annotations

import numpy as np

from domino import detect_communities
from domino.leiden.partitions_functions import Partition

from .conftest import sbm_binary


def test_detect_binary_sbm_small() -> None:
    """The binary SBM pipeline should return a finite BIC and a valid partition."""
    inst = sbm_binary(n=100)
    part, bic = detect_communities(
        inst.G,
        inst.A,
        mode="binary",
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
