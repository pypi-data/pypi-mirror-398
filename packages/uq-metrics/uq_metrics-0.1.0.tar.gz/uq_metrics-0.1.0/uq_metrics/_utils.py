"""Internal utilities for input validation and edge case handling."""

import warnings
import numpy as np


def validate_inputs(y_true, y_pred):
    """
    Validate and convert inputs to numpy arrays.

    Parameters
    ----------
    y_true : array-like
        Ground truth labels.
    y_pred : array-like
        Predicted values or scores.

    Returns
    -------
    tuple
        (y_true, y_pred) as numpy arrays with NaN values removed.

    Raises
    ------
    ValueError
        If inputs have mismatched shapes or are empty.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Shape mismatch: y_true has shape {y_true.shape}, "
            f"y_pred has shape {y_pred.shape}"
        )

    if y_true.size == 0:
        raise ValueError("Input arrays cannot be empty")

    # Remove NaN values
    valid_mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true = y_true[valid_mask]
    y_pred = y_pred[valid_mask]

    if y_true.size == 0:
        raise ValueError("No valid (non-NaN) samples remaining after filtering")

    return y_true, y_pred


def validate_binary(y_true):
    """
    Check if labels are binary (contain exactly two unique classes).

    Parameters
    ----------
    y_true : numpy.ndarray
        Ground truth labels.

    Returns
    -------
    bool
        True if binary, False otherwise.
    """
    unique = np.unique(y_true)
    return len(unique) == 2


def check_single_class(y_true, metric_name):
    """
    Check if only one class is present and issue warning.

    Parameters
    ----------
    y_true : numpy.ndarray
        Ground truth labels.
    metric_name : str
        Name of the metric for warning message.

    Returns
    -------
    bool
        True if only one class present (invalid), False otherwise.
    """
    unique = np.unique(y_true)
    if len(unique) < 2:
        warnings.warn(
            f"{metric_name}: Only one class present in y_true. "
            f"Returning NaN.",
            UserWarning
        )
        return True
    return False


def normalize_scores(scores):
    """
    Normalize scores to [0, 1] range using min-max scaling.

    Parameters
    ----------
    scores : numpy.ndarray
        Scores to normalize.

    Returns
    -------
    numpy.ndarray
        Normalized scores in [0, 1] range.
    """
    min_val = np.min(scores)
    max_val = np.max(scores)

    if max_val == min_val:
        return np.full_like(scores, 0.5)

    return (scores - min_val) / (max_val - min_val)
