"""
uq_metrics - Uncertainty Quantification Metrics Library
========================================================

A clean, minimalistic library for calculating uncertainty quantification
metrics using pure NumPy.

Core Metrics
------------
auroc : Area Under ROC Curve
ece : Expected Calibration Error
brier_score : Brier Score (MSE for probabilities)
aurc : Area Under Risk-Coverage Curve

Analysis Functions
------------------
error_vs_abstention : Error rates at different abstention levels
optimal_abstention : Find optimal abstention threshold

Examples
--------
>>> from uq_metrics import auroc, ece, brier_score
>>> import numpy as np

>>> y_true = np.array([0, 0, 1, 1, 1])
>>> y_scores = np.array([0.2, 0.3, 0.6, 0.8, 0.9])

>>> auroc(y_true, y_scores)
1.0

>>> ece(y_true, y_scores)
0.08

>>> # With integrated plotting
>>> score, ax = auroc(y_true, y_scores, plot=True)
"""

from .metrics import (
    auroc,
    ece,
    brier_score,
    aurc,
    error_vs_abstention,
    optimal_abstention,
)

__version__ = '0.1.0'

__all__ = [
    'auroc',
    'ece',
    'brier_score',
    'aurc',
    'error_vs_abstention',
    'optimal_abstention',
]
