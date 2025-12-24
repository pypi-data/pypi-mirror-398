"""Publication-ready plotting functions for metacognition analysis.

This module provides high-quality visualization functions for:
- Awareness probability time series with confidence bands
- Causal attribution bar charts
- Feature divergence heatmaps
- Distribution comparison plots

All plots are customizable and can be saved at publication quality.
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import seaborn as sns


# Publication-ready default settings
DEFAULT_DPI = 300
DEFAULT_FIGSIZE = (10, 6)
DEFAULT_STYLE = "seaborn-v0_8-darkgrid"


def _setup_plot_style(style: Optional[str] = None) -> None:
    """Setup matplotlib style for publication-ready plots.

    Args:
        style: Matplotlib style name. If None, uses default.
    """
    try:
        plt.style.use(style or DEFAULT_STYLE)
    except OSError:
        # Fallback if style not available
        plt.style.use("default")
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.edgecolor': 'black',
            'grid.alpha': 0.3,
            'font.size': 10,
        })


def plot_awareness_over_time(
    timestamps: List[Union[datetime, float]],
    probabilities: List[float],
    confidence_intervals: Optional[List[Tuple[float, float]]] = None,
    title: str = "Situational Awareness Over Time",
    xlabel: str = "Time",
    ylabel: str = "Awareness Probability",
    threshold: Optional[float] = None,
    figsize: Tuple[float, float] = DEFAULT_FIGSIZE,
    save_path: Optional[str] = None,
    dpi: int = DEFAULT_DPI,
    style: Optional[str] = None,
    show: bool = True,
) -> Figure:
    """Plot time series of situational awareness probabilities.

    Creates a line plot showing awareness probability over time with optional
    confidence intervals shown as shaded bands. Optionally displays a threshold
    line for decision-making.

    Args:
        timestamps: List of timestamps (datetime objects or numeric values)
        probabilities: Awareness probability at each timestamp
        confidence_intervals: Optional list of (lower, upper) confidence bounds
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        threshold: Optional decision threshold to display as horizontal line
        figsize: Figure size as (width, height) in inches
        save_path: If provided, save figure to this path
        dpi: Resolution for saved figure
        style: Matplotlib style to use
        show: Whether to display the plot

    Returns:
        Matplotlib Figure object

    Examples:
        >>> from datetime import datetime, timedelta
        >>> base = datetime.now()
        >>> timestamps = [base + timedelta(hours=i) for i in range(24)]
        >>> probabilities = [0.1 + 0.03*i for i in range(24)]
        >>> confidence_intervals = [(p-0.05, p+0.05) for p in probabilities]
        >>> fig = plot_awareness_over_time(
        ...     timestamps, probabilities, confidence_intervals,
        ...     threshold=0.5, save_path="awareness_trend.png"
        ... )
    """
    _setup_plot_style(style)

    if len(timestamps) != len(probabilities):
        raise ValueError(
            f"Timestamps ({len(timestamps)}) and probabilities ({len(probabilities)}) "
            "must have the same length"
        )

    if confidence_intervals and len(confidence_intervals) != len(probabilities):
        raise ValueError(
            f"Confidence intervals ({len(confidence_intervals)}) must match "
            f"probabilities ({len(probabilities)})"
        )

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Convert timestamps if needed
    x_values = timestamps
    is_datetime = isinstance(timestamps[0], datetime)

    # Main probability line
    ax.plot(
        x_values, probabilities,
        linewidth=2, color='#2E86AB', label='Awareness Probability',
        marker='o', markersize=4, markerfacecolor='white', markeredgewidth=1.5
    )

    # Confidence intervals
    if confidence_intervals:
        lower_bounds = [ci[0] for ci in confidence_intervals]
        upper_bounds = [ci[1] for ci in confidence_intervals]
        ax.fill_between(
            x_values, lower_bounds, upper_bounds,
            alpha=0.3, color='#2E86AB', label='95% Confidence Interval'
        )

    # Threshold line
    if threshold is not None:
        ax.axhline(
            y=threshold, color='#E63946', linestyle='--',
            linewidth=2, alpha=0.7, label=f'Threshold ({threshold:.2f})'
        )

    # Formatting
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.legend(loc='best', framealpha=0.9, fontsize=10)

    # Format x-axis for datetime
    if is_datetime:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')

    if show:
        plt.show()

    return fig


def plot_causal_attribution(
    intervention_results: List[Dict],
    title: str = "Causal Attribution Analysis",
    xlabel: str = "Divergence Score",
    ylabel: str = "Intervention Type",
    figsize: Tuple[float, float] = (10, 6),
    save_path: Optional[str] = None,
    dpi: int = DEFAULT_DPI,
    style: Optional[str] = None,
    show: bool = True,
    highlight_threshold: Optional[float] = None,
) -> Figure:
    """Plot causal attribution from counterfactual interventions.

    Creates a horizontal bar chart showing the causal importance of different
    interventions, sorted by divergence score. Optionally highlights interventions
    above a significance threshold.

    Args:
        intervention_results: List of dicts with 'intervention_type' and 'divergence' keys
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size as (width, height) in inches
        save_path: If provided, save figure to this path
        dpi: Resolution for saved figure
        style: Matplotlib style to use
        show: Whether to display the plot
        highlight_threshold: If provided, highlight bars above this value

    Returns:
        Matplotlib Figure object

    Examples:
        >>> results = [
        ...     {"intervention_type": "remove_eval_awareness", "divergence": 0.342},
        ...     {"intervention_type": "amplify_eval_awareness", "divergence": 0.156},
        ...     {"intervention_type": "remove_goal_reasoning", "divergence": 0.089},
        ... ]
        >>> fig = plot_causal_attribution(
        ...     results, highlight_threshold=0.2, save_path="causal_attribution.png"
        ... )
    """
    _setup_plot_style(style)

    if not intervention_results:
        raise ValueError("intervention_results cannot be empty")

    # Sort by divergence (descending)
    sorted_results = sorted(
        intervention_results,
        key=lambda x: x.get('divergence', 0),
        reverse=True
    )

    intervention_types = [
        r['intervention_type'].replace('_', ' ').title()
        for r in sorted_results
    ]
    divergences = [r['divergence'] for r in sorted_results]

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Color bars based on threshold
    if highlight_threshold is not None:
        colors = [
            '#E63946' if d >= highlight_threshold else '#2E86AB'
            for d in divergences
        ]
    else:
        colors = ['#2E86AB'] * len(divergences)

    # Create horizontal bar chart
    y_pos = np.arange(len(intervention_types))
    bars = ax.barh(y_pos, divergences, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

    # Add value labels on bars
    for i, (bar, div) in enumerate(zip(bars, divergences)):
        width = bar.get_width()
        ax.text(
            width + max(divergences) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f'{div:.3f}',
            ha='left', va='center', fontsize=10, fontweight='bold'
        )

    # Threshold line
    if highlight_threshold is not None:
        ax.axvline(
            x=highlight_threshold, color='#E63946', linestyle='--',
            linewidth=2, alpha=0.7, label=f'Significance Threshold ({highlight_threshold:.2f})'
        )
        ax.legend(loc='best', framealpha=0.9, fontsize=10)

    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(intervention_types, fontsize=10)
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='x', linestyle='-', linewidth=0.5)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')

    if show:
        plt.show()

    return fig


def plot_divergence_heatmap(
    features: List[str],
    timepoints: List[Union[datetime, str, float]],
    z_scores: np.ndarray,
    title: str = "Feature Divergence Over Time",
    xlabel: str = "Time",
    ylabel: str = "Feature",
    figsize: Tuple[float, float] = (12, 8),
    save_path: Optional[str] = None,
    dpi: int = DEFAULT_DPI,
    style: Optional[str] = None,
    show: bool = True,
    cmap: str = "RdYlGn_r",
    vmin: float = -5.0,
    vmax: float = 5.0,
) -> Figure:
    """Plot heatmap of feature divergence over time.

    Creates a color-coded heatmap showing z-scores for multiple features across
    timepoints. Uses diverging colormap with red indicating high divergence
    (potential issues) and green indicating normal behavior.

    Args:
        features: List of feature names
        timepoints: List of timepoint labels (datetime, strings, or numeric)
        z_scores: 2D array of z-scores with shape (n_features, n_timepoints)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size as (width, height) in inches
        save_path: If provided, save figure to this path
        dpi: Resolution for saved figure
        style: Matplotlib style to use
        show: Whether to display the plot
        cmap: Colormap name (diverging recommended)
        vmin: Minimum z-score for colormap
        vmax: Maximum z-score for colormap

    Returns:
        Matplotlib Figure object

    Examples:
        >>> features = ["response_length", "refusal_rate", "hedging_ratio"]
        >>> timepoints = ["00:00", "01:00", "02:00", "03:00"]
        >>> z_scores = np.array([
        ...     [0.5, 1.2, 2.8, 3.5],  # response_length
        ...     [-0.2, 0.1, 0.3, 4.2],  # refusal_rate
        ...     [0.1, 0.3, 0.2, 0.4],   # hedging_ratio
        ... ])
        >>> fig = plot_divergence_heatmap(
        ...     features, timepoints, z_scores, save_path="divergence_heatmap.png"
        ... )
    """
    _setup_plot_style(style)

    if z_scores.shape[0] != len(features):
        raise ValueError(
            f"z_scores rows ({z_scores.shape[0]}) must match features ({len(features)})"
        )

    if z_scores.shape[1] != len(timepoints):
        raise ValueError(
            f"z_scores columns ({z_scores.shape[1]}) must match timepoints ({len(timepoints)})"
        )

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Create heatmap
    im = ax.imshow(
        z_scores, aspect='auto', cmap=cmap, vmin=vmin, vmax=vmax,
        interpolation='nearest'
    )

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label('Z-Score (σ)', rotation=270, labelpad=20, fontsize=12, fontweight='bold')

    # Add severity threshold lines on colorbar
    cbar.ax.axhline(y=2.0, color='yellow', linestyle='--', linewidth=1.5, alpha=0.7)
    cbar.ax.axhline(y=3.0, color='orange', linestyle='--', linewidth=1.5, alpha=0.7)
    cbar.ax.axhline(y=4.0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)

    # Set ticks
    ax.set_xticks(np.arange(len(timepoints)))
    ax.set_yticks(np.arange(len(features)))

    # Format timepoint labels
    timepoint_labels = []
    for tp in timepoints:
        if isinstance(tp, datetime):
            timepoint_labels.append(tp.strftime('%H:%M'))
        else:
            timepoint_labels.append(str(tp))

    ax.set_xticklabels(timepoint_labels, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(
        [f.replace('_', ' ').title() for f in features],
        fontsize=10
    )

    # Add text annotations for high divergence
    for i in range(len(features)):
        for j in range(len(timepoints)):
            z = z_scores[i, j]
            if abs(z) >= 3.0:  # Annotate significant divergences
                text_color = 'white' if abs(z) >= 4.0 else 'black'
                ax.text(
                    j, i, f'{z:.1f}',
                    ha='center', va='center',
                    color=text_color, fontsize=8, fontweight='bold'
                )

    # Formatting
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')

    if show:
        plt.show()

    return fig


def plot_feature_distributions(
    eval_dist: Union[np.ndarray, List[float]],
    prod_dist: Union[np.ndarray, List[float]],
    feature_name: str,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: str = "Density",
    figsize: Tuple[float, float] = (10, 6),
    save_path: Optional[str] = None,
    dpi: int = DEFAULT_DPI,
    style: Optional[str] = None,
    show: bool = True,
    bins: int = 30,
    alpha: float = 0.6,
) -> Figure:
    """Plot overlaid distributions for evaluation vs production.

    Creates overlaid histograms and KDE plots comparing a feature's distribution
    in evaluation and production contexts. Helps visualize behavioral divergence.

    Args:
        eval_dist: Feature values from evaluation context
        prod_dist: Feature values from production context
        feature_name: Name of the feature being plotted
        title: Plot title (auto-generated if None)
        xlabel: X-axis label (auto-generated if None)
        ylabel: Y-axis label
        figsize: Figure size as (width, height) in inches
        save_path: If provided, save figure to this path
        dpi: Resolution for saved figure
        style: Matplotlib style to use
        show: Whether to display the plot
        bins: Number of histogram bins
        alpha: Transparency for histogram bars

    Returns:
        Matplotlib Figure object

    Examples:
        >>> eval_dist = np.random.normal(100, 15, 200)
        >>> prod_dist = np.random.normal(120, 20, 200)
        >>> fig = plot_feature_distributions(
        ...     eval_dist, prod_dist, "response_length",
        ...     save_path="response_length_comparison.png"
        ... )
    """
    _setup_plot_style(style)

    eval_dist = np.array(eval_dist)
    prod_dist = np.array(prod_dist)

    if len(eval_dist) == 0 or len(prod_dist) == 0:
        raise ValueError("Both distributions must contain data")

    # Auto-generate labels if not provided
    if title is None:
        title = f"{feature_name.replace('_', ' ').title()} Distribution Comparison"
    if xlabel is None:
        xlabel = feature_name.replace('_', ' ').title()

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Compute statistics
    eval_mean, eval_std = np.mean(eval_dist), np.std(eval_dist)
    prod_mean, prod_std = np.mean(prod_dist), np.std(prod_dist)

    # Histograms
    ax.hist(
        eval_dist, bins=bins, alpha=alpha, color='#2E86AB',
        label=f'Evaluation (μ={eval_mean:.2f}, σ={eval_std:.2f})',
        density=True, edgecolor='black', linewidth=0.5
    )
    ax.hist(
        prod_dist, bins=bins, alpha=alpha, color='#E63946',
        label=f'Production (μ={prod_mean:.2f}, σ={prod_std:.2f})',
        density=True, edgecolor='black', linewidth=0.5
    )

    # KDE plots for smooth overlay
    try:
        from scipy import stats

        # Evaluation KDE
        kde_eval = stats.gaussian_kde(eval_dist)
        x_eval = np.linspace(eval_dist.min(), eval_dist.max(), 100)
        ax.plot(x_eval, kde_eval(x_eval), color='#2E86AB', linewidth=2.5, alpha=0.8)

        # Production KDE
        kde_prod = stats.gaussian_kde(prod_dist)
        x_prod = np.linspace(prod_dist.min(), prod_dist.max(), 100)
        ax.plot(x_prod, kde_prod(x_prod), color='#E63946', linewidth=2.5, alpha=0.8)
    except ImportError:
        pass  # Skip KDE if scipy not available

    # Mean lines
    ax.axvline(
        eval_mean, color='#2E86AB', linestyle='--',
        linewidth=2, alpha=0.7, label=f'Eval Mean ({eval_mean:.2f})'
    )
    ax.axvline(
        prod_mean, color='#E63946', linestyle='--',
        linewidth=2, alpha=0.7, label=f'Prod Mean ({prod_mean:.2f})'
    )

    # Formatting
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.legend(loc='best', framealpha=0.9, fontsize=9)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')

    if show:
        plt.show()

    return fig
