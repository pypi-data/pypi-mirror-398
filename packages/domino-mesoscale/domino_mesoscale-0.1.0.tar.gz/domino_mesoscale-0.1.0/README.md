# DOMINO - Detection Of MesoscopIc structures via iNfOrmation criteria

DOMINO is a mesoscale detection framework that combines **Leiden optimization**
with **Bayesian Information Criterion (BIC) minimization** under several
Stochastic Block Model (SBM) likelihoods.

Supported modes:
- **binary**: SBM, dcSBM
- **signed**: signed SBM, signed dcSBM (positive, negative, absent)
- **weighted**: geometric-weight SBM, and its degree-corrected variant

The recommended public entry point is `detect`.

## Installation

Editable install (development):
```bash
python -m pip install -e ".[viz]"
```

Run tests:
```bash
python -m pip install pytest
pytest -q
```

## Quickstart

### Binary SBM (non degree-corrected)
```python
import numpy as np
import networkx as nx
from domino import detect

rng = np.random.default_rng(0)
A = (rng.random((100, 100)) < 0.05).astype(int)
A = np.triu(A, 1)
A = A + A.T
G = nx.from_numpy_array(A)

res = detect(G, A, mode="binary", degree_corrected=False, max_outer=3)
part, bic = res["partition"], res["bic"]
print("K:", len(part), "BIC:", bic)
```

### Signed SBM (non degree-corrected)
You can pass a single signed matrix `A` with negative entries.
```python
import numpy as np
import networkx as nx
from domino import detect

rng = np.random.default_rng(1)
n = 100
A = np.zeros((n, n), dtype=float)

# Two blocks with positive internal edges
A[:50, :50] = (rng.random((50, 50)) < 0.10).astype(float)
A[50:, 50:] = (rng.random((50, 50)) < 0.10).astype(float)

# Negative cross-block edges
A[:50, 50:] = -(rng.random((50, 50)) < 0.08).astype(float)
A[50:, :50] = A[:50, 50:].T
np.fill_diagonal(A, 0.0)
A = np.triu(A, 1)
A = A + A.T

G = nx.from_numpy_array((np.abs(A) > 0).astype(int))
res = detect(G, A, mode="signed", degree_corrected=False, max_outer=3)
part, bic = res["partition"], res["bic"]
print("K:", len(part), "BIC:", bic)
```

### Weighted SBM (geometric, non degree-corrected)
```python
import numpy as np
import networkx as nx
from domino import detect

rng = np.random.default_rng(2)
W = rng.poisson(2.0, size=(100, 100)).astype(float)
W = np.triu(W, 1)
W = W + W.T
np.fill_diagonal(W, 0.0)

G = nx.from_numpy_array((W > 0).astype(int))
res = detect(G, W, mode="weighted", degree_corrected=False, max_outer=3)
part, bic = res["partition"], res["bic"]
print("K:", len(part), "BIC:", bic)
```

## Documentation

- Usage notes: `docs/usage.md`
- Mathematical details: `docs/math.md`
- API quick reference: `docs/api_quick_reference.md`

## Continuous integration

GitHub Actions workflow: `.github/workflows/ci.yml`

## License

See `LICENSE`.
