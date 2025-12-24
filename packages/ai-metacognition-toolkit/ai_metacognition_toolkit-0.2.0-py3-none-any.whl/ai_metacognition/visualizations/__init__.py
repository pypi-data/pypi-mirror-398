"""Visualization utilities for AI Metacognition Toolkit.

This module provides publication-ready plotting functions for:
- Situational awareness time series
- Causal attribution analysis
- Feature divergence heatmaps
- Distribution comparisons
"""

from .plotting import (
    plot_awareness_over_time,
    plot_causal_attribution,
    plot_divergence_heatmap,
    plot_feature_distributions,
)

__all__ = [
    "plot_awareness_over_time",
    "plot_causal_attribution",
    "plot_divergence_heatmap",
    "plot_feature_distributions",
]
