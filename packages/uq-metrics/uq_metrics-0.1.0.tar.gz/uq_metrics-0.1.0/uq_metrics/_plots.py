"""Internal plotting utilities for uncertainty quantification metrics."""

import numpy as np


def _get_ax(ax=None):
    """Get or create matplotlib axes."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 5))
    return ax


def plot_roc(fpr, tpr, auc_score, ax=None):
    """
    Plot ROC curve with AUC annotation.

    Parameters
    ----------
    fpr : numpy.ndarray
        False positive rates.
    tpr : numpy.ndarray
        True positive rates.
    auc_score : float
        Area under the ROC curve.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None.

    Returns
    -------
    matplotlib.axes.Axes
        The axes with the plot.
    """
    ax = _get_ax(ax)

    ax.plot(fpr, tpr, color='#2563eb', linewidth=2,
            label=f'ROC (AUC = {auc_score:.3f})')
    ax.plot([0, 1], [0, 1], color='#9ca3af', linestyle='--',
            linewidth=1, label='Random')
    ax.fill_between(fpr, tpr, alpha=0.1, color='#2563eb')

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.02])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curve')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    return ax


def plot_calibration_diagram(bin_edges, bin_accuracies, bin_confidences,
                             bin_counts, ece_score, ax=None):
    """
    Plot reliability diagram (calibration curve).

    Parameters
    ----------
    bin_edges : numpy.ndarray
        Edges of confidence bins.
    bin_accuracies : numpy.ndarray
        Accuracy in each bin.
    bin_confidences : numpy.ndarray
        Mean confidence in each bin.
    bin_counts : numpy.ndarray
        Number of samples in each bin.
    ece_score : float
        Expected calibration error.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None.

    Returns
    -------
    matplotlib.axes.Axes
        The axes with the plot.
    """
    ax = _get_ax(ax)

    n_bins = len(bin_accuracies)
    bin_width = 1.0 / n_bins
    bin_centers = np.linspace(bin_width / 2, 1 - bin_width / 2, n_bins)

    # Bar chart for accuracy
    valid_mask = bin_counts > 0
    ax.bar(bin_centers[valid_mask], bin_accuracies[valid_mask],
           width=bin_width * 0.8, alpha=0.7, color='#2563eb',
           edgecolor='#1e40af', linewidth=1, label='Accuracy')

    # Perfect calibration line
    ax.plot([0, 1], [0, 1], color='#dc2626', linestyle='--',
            linewidth=2, label='Perfect Calibration')

    # Gap visualization
    for i in range(n_bins):
        if bin_counts[i] > 0:
            gap = bin_accuracies[i] - bin_confidences[i]
            if abs(gap) > 0.01:
                ax.plot([bin_centers[i], bin_centers[i]],
                        [bin_confidences[i], bin_accuracies[i]],
                        color='#f97316', linewidth=2, alpha=0.8)

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.set_xlabel('Confidence')
    ax.set_ylabel('Accuracy')
    ax.set_title(f'Reliability Diagram (ECE = {ece_score:.3f})')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    return ax


def plot_risk_coverage_curve(coverage_levels, risks, aurc_score, ax=None):
    """
    Plot risk-coverage curve.

    Parameters
    ----------
    coverage_levels : numpy.ndarray
        Coverage levels (fraction of samples kept).
    risks : numpy.ndarray
        Risk (error rate) at each coverage level.
    aurc_score : float
        Area under the risk-coverage curve.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None.

    Returns
    -------
    matplotlib.axes.Axes
        The axes with the plot.
    """
    ax = _get_ax(ax)

    ax.plot(coverage_levels, risks, color='#2563eb', linewidth=2,
            label=f'Risk-Coverage (AURC = {aurc_score:.3f})')
    ax.fill_between(coverage_levels, risks, alpha=0.1, color='#2563eb')

    # Add baseline (constant risk = full coverage risk)
    if len(risks) > 0:
        baseline_risk = risks[-1] if coverage_levels[-1] == 1.0 else risks[np.argmax(coverage_levels)]
        ax.axhline(y=baseline_risk, color='#9ca3af', linestyle='--',
                   linewidth=1, label=f'Baseline Risk = {baseline_risk:.3f}')

    ax.set_xlim([0, 1.02])
    ax.set_ylim([0, max(risks) * 1.1 if len(risks) > 0 else 1])
    ax.set_xlabel('Coverage')
    ax.set_ylabel('Risk (Error Rate)')
    ax.set_title('Risk-Coverage Curve')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

    return ax


def plot_abstention_curve(abstention_levels, error_rates, baseline_error, ax=None):
    """
    Plot error rate vs abstention level curve.

    Parameters
    ----------
    abstention_levels : numpy.ndarray
        Abstention levels (fraction of samples rejected).
    error_rates : numpy.ndarray
        Error rate at each abstention level.
    baseline_error : float
        Baseline error rate (at zero abstention).
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. Creates new figure if None.

    Returns
    -------
    matplotlib.axes.Axes
        The axes with the plot.
    """
    ax = _get_ax(ax)

    ax.plot(abstention_levels, error_rates, color='#2563eb', linewidth=2,
            marker='o', markersize=4, label='Error Rate')
    ax.fill_between(abstention_levels, error_rates, baseline_error,
                    alpha=0.2, color='#22c55e', label='Error Reduction')

    ax.axhline(y=baseline_error, color='#dc2626', linestyle='--',
               linewidth=1.5, label=f'Baseline = {baseline_error:.3f}')

    ax.set_xlim([0, 1])
    ax.set_ylim([0, baseline_error * 1.2 if baseline_error > 0 else 1])
    ax.set_xlabel('Abstention Rate')
    ax.set_ylabel('Error Rate')
    ax.set_title('Error vs Abstention')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

    return ax
