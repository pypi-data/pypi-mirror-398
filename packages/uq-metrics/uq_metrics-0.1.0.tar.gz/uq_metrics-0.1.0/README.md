# uq-metrics

Uncertainty quantification metrics for model evaluation. Pure NumPy implementation.

## Installation

```bash
pip install uq-metrics
```

For plotting support:
```bash
pip install uq-metrics[plot]
```

## Usage

```python
from uq_metrics import auroc, ece, brier_score, aurc
import numpy as np

y_true = np.array([0, 0, 1, 1, 1])
y_scores = np.array([0.2, 0.3, 0.6, 0.8, 0.9])

auroc(y_true, y_scores)        # Area Under ROC Curve
ece(y_true, y_scores)          # Expected Calibration Error
brier_score(y_true, y_scores)  # Brier Score

# With plotting
score, ax = auroc(y_true, y_scores, plot=True)
```

## Available Metrics

- `auroc` - Area Under ROC Curve
- `ece` - Expected Calibration Error
- `brier_score` - Brier Score
- `aurc` - Area Under Risk-Coverage Curve
- `error_vs_abstention` - Error rates at abstention levels
- `optimal_abstention` - Find optimal abstention threshold
