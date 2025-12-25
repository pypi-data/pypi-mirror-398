"""
constants.py

Centralized numeric constants and defaults used across the package.

Purpose
-------
• Ensure consistent tolerances and iteration caps across all solvers
  (binary, signed, and weighted ERGMs) and BIC routines.
• Provide small epsilons and clamps used to stabilize log/exp operations.
• Collect defaults for "patience" and iteration budgets.
• Encapsulate common guards for weighted models.

Notes
-----
These values are chosen to match the legacy behavior in the original code.
If you need to change convergence behavior globally, do it here so that
all modules stay in sync.

Naming
------
We keep names descriptive and stable. In modules that previously used
legacy names (e.g., `TOL_NEW` for χ-Newton), we rebind to these constants
so external code and comments remain unchanged.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Universal small epsilon
# ---------------------------------------------------------------------------
EPS: float = 1e-12

# ---------------------------------------------------------------------------
# Default tolerances for ERGM solvers
# ---------------------------------------------------------------------------
# Binary models
TOL_UBCM: float = 1e-6  # UBCM target residual 2-norm
TOL_DCSBM: float = 1e-6  # dcSBM target residual 2-norm

# Signed models
TOL_SIGNED_SCM: float = 1e-9
TOL_SIGNED_DCSBM: float = 1e-6

# Weighted (geometric) models
TOL_WCM: float = 1e-6
TOL_WDCSBM: float = 1e-6

# ---------------------------------------------------------------------------
# Iteration budgets and patience
# ---------------------------------------------------------------------------
MAX_IT_DEFAULT: int = 1000  # default outer iteration cap for solver loops
PATIENCE_DEFAULT: int = 10  # early-stop patience (no-improve iterations)

# ---------------------------------------------------------------------------
# RNG fallback (used only if caller does not pass a seed/Generator)
# ---------------------------------------------------------------------------
RNG_SEED_FALLBACK: int = 12345

# ---------------------------------------------------------------------------
# Weighted-model numerical guards (used in weighted_solvers)
# ---------------------------------------------------------------------------
U_MIN: float = -40.0  # clamp for log-parameters to keep exp(u) finite
U_MAX: float = 40.0
X_MIN: float = 1e-12  # floor on x_i > 0
Z_MIN: float = 1e-12  # floor on z = x_i x_j [χ_{rs}]

# ---------------------------------------------------------------------------
# χ (block affinity) Newton solver (used in binary_bic dcSBM pipeline)
# ---------------------------------------------------------------------------
TOL_CHI: float = 1e-6  # tolerance for χ Newton slices (legacy: TOL_NEW)
MAX_IT_CHI: int = 20  # max iterations per χ slice     (legacy: MAX_IT_NEW)
CHI_CAP: float = 1e12  # cap when a block is fully connected

# ---------------------------------------------------------------------------
# Logging defaults (library code should *not* set handlers by default)
# ---------------------------------------------------------------------------
# Leave configuration to the application. Modules query a logger by name:
#   logger = logging.getLogger("domino.XXX")
# and rely on configure_logging(...) from utils.repro when users pass verbose=True.
