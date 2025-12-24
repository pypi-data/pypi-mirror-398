"""Utilities module for common helper functions.

This module provides utility functions for data processing, visualization,
feature extraction, statistical testing, and other common operations used
throughout the toolkit.
"""

from ai_metacognition.utils.feature_extraction import (
    compute_js_divergence,
    compute_kl_divergence,
    cosine_similarity,
    count_hedging_phrases,
    detect_meta_commentary,
    extract_behavioral_features,
    extract_reasoning_depth,
    normalize_distribution,
)
from ai_metacognition.utils.statistical_tests import (
    SignificanceLevel,
    assess_divergence_significance,
    bayesian_update,
    beta_mode,
    compute_beta_mean,
    compute_beta_variance,
    compute_confidence_interval,
    z_score,
)

__all__ = [
    # Feature extraction
    "extract_behavioral_features",
    "count_hedging_phrases",
    "detect_meta_commentary",
    "extract_reasoning_depth",
    "compute_kl_divergence",
    "compute_js_divergence",
    "cosine_similarity",
    "normalize_distribution",
    # Statistical testing
    "bayesian_update",
    "compute_confidence_interval",
    "z_score",
    "assess_divergence_significance",
    "SignificanceLevel",
    "compute_beta_mean",
    "compute_beta_variance",
    "beta_mode",
]
