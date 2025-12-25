"""
repro.py

Reproducibility and logging helpers.

Purpose
-------
• Provide a single place to construct **coordinated RNGs** for NumPy and Python
  so stochastic steps (e.g., in Leiden) can be reproducible when desired.
• Offer a tiny **logging** convenience that sets levels/handlers only when the
  application asks for verbosity.

Exports
-------
- coerce_random_state(random_state) -> (np_rng, py_rng)
- configure_logging(verbose=False, logger_name="domino") -> logging.Logger

Determinism policy
------------------
The behavior is explicit and opt-in:
  • random_state is None
      → return independent RNGs seeded from **OS entropy** (non-deterministic).
  • random_state is an int
      → seed both NumPy and Python RNGs with the same value (deterministic).
  • random_state is a np.random.Generator
      → use it for NumPy; derive a stable Python seed from it.
  • random_state is a random.Random
      → use it for Python; derive a stable NumPy seed from it.

Notes
-----
• The function returns a tuple **(np_rng, py_rng)** and never touches global RNGs
  (`numpy.random` or `random` module state). Callers should pass these RNGs down
  explicitly to any code that shuffles, samples, or tiebreaks.
• `configure_logging(...)` only attaches a basic console handler the first time
  a given logger is requested and sets its level (INFO if `verbose`, else WARNING).
  Library modules should create loggers with names like "domino.submodule" and
  avoid configuring handlers themselves.
"""

from __future__ import annotations

import logging
import random
from typing import Optional, Tuple, Union

import numpy as np

Number = Union[int, np.integer]


def coerce_random_state(
    random_state: Optional[Union[Number, np.random.Generator, random.Random]],
) -> Tuple[np.random.Generator, random.Random]:
    """
    Return (np_rng, py_rng) objects from user-provided random_state.
    Supported:
      - None         -> seed both RNGs from OS entropy (non-deterministic)
      - int          -> seed both numpy and python RNGs with this value
      - np.Generator -> use as numpy RNG; seed python RNG from its bitgen state
      - random.Random-> use as python RNG; seed numpy RNG from its state
    """
    if random_state is None:
        # Non-deterministic by default
        return (np.random.default_rng(), random.Random())

    if isinstance(random_state, (int, np.integer)):
        seed = int(random_state)
        return (np.random.default_rng(seed), random.Random(seed))

    if isinstance(random_state, np.random.Generator):
        np_rng = random_state
        # derive a deterministic python seed from the numpy bit generator
        seed = int(np_rng.integers(0, 2**32 - 1))
        return (np_rng, random.Random(seed))

    if isinstance(random_state, random.Random):
        py_rng = random_state
        # derive a deterministic numpy seed from python RNG
        seed = py_rng.getrandbits(32)
        return (np.random.default_rng(seed), py_rng)

    raise TypeError(
        "random_state must be None, int, np.random.Generator, or random.Random"
    )


def configure_logging(
    verbose: int | bool = False, logger_name: str = "domino"
) -> logging.Logger:
    """
    Create/return a package logger. If verbose truthy, set INFO; else WARNING.
    """
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        # basic console handler
        h = logging.StreamHandler()
        fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    logger.setLevel(logging.INFO if verbose else logging.WARNING)
    return logger
