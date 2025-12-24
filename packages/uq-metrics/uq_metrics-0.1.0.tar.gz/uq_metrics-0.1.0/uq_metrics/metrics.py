"""Uncertainty quantification metrics - pure NumPy implementations."""

import warnings
import numpy as np

from ._utils import validate_inputs, check_single_class, normalize_scores


def auroc(y_true, y_scores, direction='positive', plot=False, ax=None):
    """
    Calculate Area Under the ROC Curve.

    Uses the Mann-Whitney U statistic for efficient computation.

    Parameters
    ----------
    y_true : array-like
        Binary ground truth labels (0 or 1).
    y_scores : array-like
        Predicted scores or probabilities.
    direction : {'positive', 'negative'}, default='positive'
        If 'positive', higher scores indicate positive class.
        If 'negative', lower scores indicate positive class.
    plot : bool, default=False
        Whether to generate ROC curve plot.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None and plot=True.

    Returns
    -------
    float or tuple
        AUROC score. If plot=True, returns (score, axes).

    Examples
    --------
    >>> y_true = np.array([0, 0, 1, 1])
    >>> y_scores = np.array([0.1, 0.4, 0.35, 0.8])
    >>> auroc(y_true, y_scores)
    0.75
    """
    y_true, y_scores = validate_inputs(y_true, y_scores)

    if check_single_class(y_true, 'AUROC'):
        return np.nan

    if direction == 'negative':
        y_scores = -y_scores

    # Compute AUROC using Mann-Whitney U statistic
    pos_mask = y_true == 1
    neg_mask = y_true == 0
    n_pos = np.sum(pos_mask)
    n_neg = np.sum(neg_mask)

    if n_pos == 0 or n_neg == 0:
        warnings.warn("AUROC: One class has no samples. Returning NaN.", UserWarning)
        return np.nan

    # Rank-based calculation
    order = np.argsort(y_scores)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(y_scores) + 1)

    # Handle ties by averaging ranks
    sorted_scores = y_scores[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j < len(sorted_scores) and sorted_scores[j] == sorted_scores[i]:
            j += 1
        avg_rank = (i + j + 1) / 2  # Average rank for tied values
        for k in range(i, j):
            ranks[order[k]] = avg_rank
        i = j

    # Mann-Whitney U
    sum_pos_ranks = np.sum(ranks[pos_mask])
    u_stat = sum_pos_ranks - n_pos * (n_pos + 1) / 2
    auc = u_stat / (n_pos * n_neg)

    if plot:
        fpr, tpr = _compute_roc_curve(y_true, y_scores)
        from ._plots import plot_roc
        ax = plot_roc(fpr, tpr, auc, ax)
        return float(auc), ax

    return float(auc)


def _compute_roc_curve(y_true, y_scores):
    """Compute FPR and TPR for ROC curve."""
    # Sort by scores descending
    order = np.argsort(y_scores)[::-1]
    y_true_sorted = y_true[order]

    n_pos = np.sum(y_true)
    n_neg = len(y_true) - n_pos

    tpr = np.cumsum(y_true_sorted) / n_pos
    fpr = np.cumsum(1 - y_true_sorted) / n_neg

    # Add origin point
    tpr = np.concatenate([[0], tpr])
    fpr = np.concatenate([[0], fpr])

    return fpr, tpr


def ece(y_true, y_pred, n_bins=10, plot=False, ax=None):
    """
    Calculate Expected Calibration Error.

    Measures how well the predicted probabilities match the actual outcomes.

    Parameters
    ----------
    y_true : array-like
        Binary ground truth labels (0 or 1).
    y_pred : array-like
        Predicted probabilities in [0, 1].
    n_bins : int, default=10
        Number of bins for calibration.
    plot : bool, default=False
        Whether to generate reliability diagram.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None and plot=True.

    Returns
    -------
    float or tuple
        ECE score (lower is better). If plot=True, returns (score, axes).

    Examples
    --------
    >>> y_true = np.array([0, 0, 1, 1, 1])
    >>> y_pred = np.array([0.2, 0.3, 0.7, 0.8, 0.9])
    >>> ece(y_true, y_pred)  # Well calibrated
    0.06
    """
    y_true, y_pred = validate_inputs(y_true, y_pred)

    if check_single_class(y_true, 'ECE'):
        return np.nan

    # Clip predictions to [0, 1]
    y_pred = np.clip(y_pred, 0, 1)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_pred, bin_edges[1:-1])

    bin_counts = np.zeros(n_bins)
    bin_sums = np.zeros(n_bins)
    bin_true_sums = np.zeros(n_bins)

    for i in range(n_bins):
        mask = bin_indices == i
        bin_counts[i] = np.sum(mask)
        if bin_counts[i] > 0:
            bin_sums[i] = np.sum(y_pred[mask])
            bin_true_sums[i] = np.sum(y_true[mask])

    # Compute ECE
    ece_value = 0.0
    bin_accuracies = np.zeros(n_bins)
    bin_confidences = np.zeros(n_bins)

    for i in range(n_bins):
        if bin_counts[i] > 0:
            bin_confidences[i] = bin_sums[i] / bin_counts[i]
            bin_accuracies[i] = bin_true_sums[i] / bin_counts[i]
            bin_weight = bin_counts[i] / len(y_pred)
            ece_value += bin_weight * np.abs(bin_confidences[i] - bin_accuracies[i])

    if plot:
        from ._plots import plot_calibration_diagram
        ax = plot_calibration_diagram(
            bin_edges, bin_accuracies, bin_confidences, bin_counts, ece_value, ax
        )
        return float(ece_value), ax

    return float(ece_value)


def brier_score(y_true, y_pred):
    """
    Calculate Brier score (mean squared error for probabilities).

    Parameters
    ----------
    y_true : array-like
        Binary ground truth labels (0 or 1).
    y_pred : array-like
        Predicted probabilities in [0, 1].

    Returns
    -------
    float
        Brier score (lower is better, 0 is perfect).

    Examples
    --------
    >>> y_true = np.array([0, 1, 1, 0])
    >>> y_pred = np.array([0.1, 0.9, 0.8, 0.2])
    >>> brier_score(y_true, y_pred)
    0.025
    """
    y_true, y_pred = validate_inputs(y_true, y_pred)

    if check_single_class(y_true, 'Brier Score'):
        return np.nan

    return float(np.mean((y_true - y_pred) ** 2))


def aurc(y_true, confidence, plot=False, ax=None):
    """
    Calculate Area Under the Risk-Coverage Curve.

    Measures how well the confidence scores identify correct predictions.
    Lower values indicate better selective prediction. Matches the
    torch-uncertainty implementation.

    Parameters
    ----------
    y_true : array-like
        Binary correctness labels (1 = correct, 0 = incorrect).
    confidence : array-like
        Confidence scores (higher = more confident).
    plot : bool, default=False
        Whether to generate risk-coverage curve.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None and plot=True.

    Returns
    -------
    float or tuple
        AURC score (lower is better). If plot=True, returns (score, axes).

    References
    ----------
    Geifman & El-Yaniv. "Selective classification for deep neural networks."
    NeurIPS 2017.

    Examples
    --------
    >>> y_true = np.array([1, 1, 0, 1, 0])
    >>> confidence = np.array([0.9, 0.8, 0.7, 0.6, 0.3])
    >>> aurc(y_true, confidence)
    0.1333...
    """
    y_true, confidence = validate_inputs(y_true, confidence)

    if check_single_class(y_true, 'AURC'):
        return np.nan

    n = len(y_true)
    if n < 2:
        warnings.warn("AURC: Need at least 2 samples. Returning NaN.", UserWarning)
        return np.nan

    # Sort by confidence descending
    order = np.argsort(confidence)[::-1]
    errors_sorted = 1.0 - y_true[order]  # 1 if incorrect, 0 if correct

    # Cumulative error rate at each position (coverage = 1/n, 2/n, ..., n/n)
    error_rates = np.cumsum(errors_sorted) / np.arange(1, n + 1)

    # Coverage levels: 1/n, 2/n, ..., n/n
    coverage = np.arange(1, n + 1) / n

    # Integrate using trapezoidal rule and normalize
    # Normalization accounts for coverage starting at 1/n instead of 0
    aurc_value = np.trapz(error_rates, coverage) / (1 - 1 / n)

    if plot:
        from ._plots import plot_risk_coverage_curve
        ax = plot_risk_coverage_curve(coverage, error_rates, aurc_value, ax)
        return float(aurc_value), ax

    return float(aurc_value)


def error_vs_abstention(y_true, confidence, levels=None, plot=False, ax=None):
    """
    Calculate error rates at different abstention levels.

    Parameters
    ----------
    y_true : array-like
        Binary correctness labels (1 = correct, 0 = incorrect).
    confidence : array-like
        Confidence scores (higher = more confident).
    levels : array-like, optional
        Abstention levels to evaluate. Default: np.linspace(0, 0.95, 20).
    plot : bool, default=False
        Whether to generate error vs abstention curve.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None and plot=True.

    Returns
    -------
    dict or tuple
        Dictionary with keys:
        - 'abstention_levels': Abstention rates evaluated
        - 'coverage': Coverage (1 - abstention) at each level
        - 'error_rates': Error rate at each level
        - 'relative_reduction': Relative error reduction vs baseline
        - 'absolute_reduction': Absolute error reduction vs baseline

        If plot=True, returns (dict, axes).

    Examples
    --------
    >>> y_true = np.array([1, 1, 0, 1, 0, 1])
    >>> confidence = np.array([0.9, 0.8, 0.7, 0.6, 0.3, 0.2])
    >>> result = error_vs_abstention(y_true, confidence)
    >>> result['error_rates']  # Error decreases as abstention increases
    """
    y_true, confidence = validate_inputs(y_true, confidence)

    if levels is None:
        levels = np.linspace(0, 0.95, 20)
    else:
        levels = np.asarray(levels)

    # Sort by confidence descending
    order = np.argsort(confidence)[::-1]
    y_true_sorted = y_true[order]

    baseline_error = 1.0 - np.mean(y_true)

    abstention_levels = []
    coverage_vals = []
    error_rates = []
    relative_reduction = []
    absolute_reduction = []

    for abstention in levels:
        coverage = 1.0 - abstention
        n_samples = max(1, int(len(y_true) * coverage))

        if n_samples == 0:
            continue

        selected = y_true_sorted[:n_samples]
        error = 1.0 - np.mean(selected)

        rel_red = (baseline_error - error) / baseline_error if baseline_error > 0 else 0.0
        abs_red = baseline_error - error

        abstention_levels.append(abstention)
        coverage_vals.append(coverage)
        error_rates.append(error)
        relative_reduction.append(rel_red)
        absolute_reduction.append(abs_red)

    result = {
        'abstention_levels': np.array(abstention_levels),
        'coverage': np.array(coverage_vals),
        'error_rates': np.array(error_rates),
        'relative_reduction': np.array(relative_reduction),
        'absolute_reduction': np.array(absolute_reduction),
    }

    if plot:
        from ._plots import plot_abstention_curve
        ax = plot_abstention_curve(
            result['abstention_levels'],
            result['error_rates'],
            baseline_error,
            ax
        )
        return result, ax

    return result


def optimal_abstention(analysis, max_abstention=None, criterion='relative'):
    """
    Find the optimal abstention level from error_vs_abstention analysis.

    Parameters
    ----------
    analysis : dict
        Output from error_vs_abstention().
    max_abstention : float, optional
        Maximum allowed abstention rate. If None, no limit.
    criterion : {'min_error', 'relative', 'absolute'}, default='relative'
        - 'min_error': Minimize absolute error rate
        - 'relative': Maximize relative improvement per abstention
        - 'absolute': Maximize absolute improvement per abstention

    Returns
    -------
    dict
        Dictionary with:
        - 'abstention_level': Optimal abstention rate
        - 'coverage': Coverage at optimal point
        - 'error_rate': Error rate at optimal point
        - 'relative_reduction': Relative error reduction at optimal point
        - 'absolute_reduction': Absolute error reduction at optimal point

    Examples
    --------
    >>> result = error_vs_abstention(y_true, confidence)
    >>> opt = optimal_abstention(result, max_abstention=0.5)
    >>> print(f"Optimal abstention: {opt['abstention_level']:.2f}")
    """
    levels = analysis['abstention_levels']
    error_rates = analysis['error_rates']
    coverage = analysis['coverage']
    rel_red = analysis['relative_reduction']
    abs_red = analysis['absolute_reduction']

    # Apply max abstention filter
    if max_abstention is not None:
        mask = levels <= max_abstention
        if not np.any(mask):
            warnings.warn(
                f"No abstention levels <= {max_abstention}. "
                "Returning first available level.",
                UserWarning
            )
            mask = np.ones(len(levels), dtype=bool)
    else:
        mask = np.ones(len(levels), dtype=bool)

    filtered_indices = np.where(mask)[0]

    if len(filtered_indices) == 0:
        warnings.warn("No valid abstention levels. Returning NaN.", UserWarning)
        return {
            'abstention_level': np.nan,
            'coverage': np.nan,
            'error_rate': np.nan,
            'relative_reduction': np.nan,
            'absolute_reduction': np.nan,
        }

    if criterion == 'min_error':
        idx = filtered_indices[np.argmin(error_rates[mask])]

    elif criterion == 'relative':
        # Avoid division by zero for abstention = 0
        improvement = np.zeros(len(levels))
        for i in filtered_indices:
            if levels[i] > 0:
                improvement[i] = rel_red[i] / levels[i]
        idx = filtered_indices[np.argmax(improvement[mask])]

    elif criterion == 'absolute':
        improvement = np.zeros(len(levels))
        for i in filtered_indices:
            if levels[i] > 0:
                improvement[i] = abs_red[i] / levels[i]
        idx = filtered_indices[np.argmax(improvement[mask])]

    else:
        raise ValueError(
            f"Unknown criterion: {criterion}. "
            "Use 'min_error', 'relative', or 'absolute'."
        )

    return {
        'abstention_level': float(levels[idx]),
        'coverage': float(coverage[idx]),
        'error_rate': float(error_rates[idx]),
        'relative_reduction': float(rel_red[idx]),
        'absolute_reduction': float(abs_red[idx]),
    }
