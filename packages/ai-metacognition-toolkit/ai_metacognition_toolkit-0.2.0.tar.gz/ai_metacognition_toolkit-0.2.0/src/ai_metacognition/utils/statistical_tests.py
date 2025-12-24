"""Statistical testing utilities for metacognition analysis.

This module provides reusable statistical functions for Bayesian inference,
confidence interval computation, z-score calculations, and divergence
significance assessment.
"""

from enum import Enum
from typing import Dict, Tuple

import numpy as np
from scipy import stats


class SignificanceLevel(Enum):
    """Significance level classification for statistical tests."""

    NONE = "none"  # Below threshold
    LOW = "low"  # 2-3 sigma
    MEDIUM = "medium"  # 3-4 sigma
    HIGH = "high"  # 4-5 sigma
    CRITICAL = "critical"  # >5 sigma


def bayesian_update(
    prior_alpha: float, prior_beta: float, evidence: Dict[str, int]
) -> Tuple[float, float]:
    """Update Beta distribution priors with new evidence using Bayesian inference.

    Uses the Beta-Binomial conjugate prior relationship where:
    - Prior: Beta(alpha, beta)
    - Likelihood: Binomial(successes, failures)
    - Posterior: Beta(alpha + successes, beta + failures)

    Args:
        prior_alpha: Alpha parameter of prior Beta distribution (must be > 0)
        prior_beta: Beta parameter of prior Beta distribution (must be > 0)
        evidence: Dictionary with 'successes' and 'failures' counts

    Returns:
        Tuple of (posterior_alpha, posterior_beta)

    Raises:
        ValueError: If prior parameters are invalid
        ValueError: If evidence is missing required keys or has negative values
        TypeError: If evidence is not a dictionary

    Examples:
        >>> bayesian_update(1.0, 1.0, {'successes': 5, 'failures': 3})
        (6.0, 4.0)

        >>> bayesian_update(10.0, 10.0, {'successes': 8, 'failures': 2})
        (18.0, 12.0)
    """
    # Validate prior parameters
    if not isinstance(prior_alpha, (int, float)) or not isinstance(
        prior_beta, (int, float)
    ):
        raise ValueError("Prior alpha and beta must be numeric")

    if prior_alpha <= 0 or prior_beta <= 0:
        raise ValueError("Prior alpha and beta must be positive")

    # Validate evidence
    if not isinstance(evidence, dict):
        raise TypeError("Evidence must be a dictionary")

    if "successes" not in evidence or "failures" not in evidence:
        raise ValueError("Evidence must contain 'successes' and 'failures' keys")

    successes = evidence["successes"]
    failures = evidence["failures"]

    if not isinstance(successes, (int, float)) or not isinstance(failures, (int, float)):
        raise ValueError("Evidence counts must be numeric")

    if successes < 0 or failures < 0:
        raise ValueError("Evidence counts cannot be negative")

    # Bayesian update: posterior = prior + evidence
    posterior_alpha = float(prior_alpha + successes)
    posterior_beta = float(prior_beta + failures)

    return posterior_alpha, posterior_beta


def compute_confidence_interval(
    alpha: float, beta: float, confidence_level: float = 0.95
) -> Tuple[float, float]:
    """Compute credible interval for Beta distribution.

    Calculates the Bayesian credible interval (also called highest density interval)
    for a Beta distribution. This represents the range within which the true
    parameter lies with the specified probability.

    Args:
        alpha: Alpha parameter of Beta distribution (must be > 0)
        beta: Beta parameter of Beta distribution (must be > 0)
        confidence_level: Confidence level (0 < confidence_level < 1, default: 0.95)

    Returns:
        Tuple of (lower_bound, upper_bound) for the credible interval

    Raises:
        ValueError: If alpha or beta are not positive
        ValueError: If confidence_level is not between 0 and 1

    Examples:
        >>> lower, upper = compute_confidence_interval(10, 10, 0.95)
        >>> 0.3 < lower < 0.4  # Approximately 0.34
        True
        >>> 0.6 < upper < 0.7  # Approximately 0.66
        True

        >>> lower, upper = compute_confidence_interval(100, 10, 0.95)
        >>> 0.85 < lower < 0.95
        True
    """
    # Validate parameters
    if not isinstance(alpha, (int, float)) or not isinstance(beta, (int, float)):
        raise ValueError("Alpha and beta must be numeric")

    if alpha <= 0 or beta <= 0:
        raise ValueError("Alpha and beta must be positive")

    if not isinstance(confidence_level, (int, float)):
        raise ValueError("Confidence level must be numeric")

    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("Confidence level must be between 0 and 1")

    # Calculate credible interval using Beta distribution quantiles
    # For a symmetric interval, we use (1 - confidence_level) / 2 on each tail
    tail_prob = (1 - confidence_level) / 2
    lower_bound = stats.beta.ppf(tail_prob, alpha, beta)
    upper_bound = stats.beta.ppf(1 - tail_prob, alpha, beta)

    return float(lower_bound), float(upper_bound)


def z_score(value: float, mean: float, std: float) -> float:
    """Calculate standardized z-score.

    Computes how many standard deviations a value is from the mean.
    Handles edge cases like zero standard deviation gracefully.

    Formula: z = (value - mean) / std

    Args:
        value: The observed value
        mean: The mean of the distribution
        std: The standard deviation of the distribution (must be >= 0)

    Returns:
        Z-score (number of standard deviations from mean)
        Returns 0.0 if std is 0 or very small (< 1e-10)

    Raises:
        ValueError: If std is negative
        ValueError: If any parameter is not numeric

    Examples:
        >>> z_score(100, 90, 10)
        1.0

        >>> z_score(85, 100, 5)
        -3.0

        >>> z_score(50, 50, 0)  # Edge case: zero std
        0.0
    """
    # Validate inputs
    if not all(isinstance(x, (int, float)) for x in [value, mean, std]):
        raise ValueError("All parameters must be numeric")

    if std < 0:
        raise ValueError("Standard deviation cannot be negative")

    # Handle edge case: zero or very small standard deviation
    # If std is essentially zero, the value equals the mean (or data has no variance)
    if std < 1e-10:
        return 0.0

    # Standard z-score calculation
    z = (value - mean) / std

    return float(z)


def assess_divergence_significance(
    z_score_value: float, threshold: float = 2.0
) -> SignificanceLevel:
    """Assess statistical significance of a divergence based on z-score.

    Classifies the significance level of a divergence using standard
    deviation thresholds. Uses absolute value of z-score.

    Significance levels:
    - NONE: |z| < threshold (typically < 2σ)
    - LOW: threshold <= |z| < threshold + 1 (2-3σ)
    - MEDIUM: threshold + 1 <= |z| < threshold + 2 (3-4σ)
    - HIGH: threshold + 2 <= |z| < threshold + 3 (4-5σ)
    - CRITICAL: |z| >= threshold + 3 (>5σ)

    Args:
        z_score_value: The z-score to assess
        threshold: Base threshold for significance (default: 2.0)

    Returns:
        SignificanceLevel enum indicating the level of significance

    Raises:
        ValueError: If threshold is not positive
        ValueError: If z_score_value is not numeric

    Examples:
        >>> assess_divergence_significance(1.5)
        <SignificanceLevel.NONE: 'none'>

        >>> assess_divergence_significance(2.5)
        <SignificanceLevel.LOW: 'low'>

        >>> assess_divergence_significance(3.5)
        <SignificanceLevel.MEDIUM: 'medium'>

        >>> assess_divergence_significance(-4.5)  # Absolute value used
        <SignificanceLevel.HIGH: 'high'>

        >>> assess_divergence_significance(6.0)
        <SignificanceLevel.CRITICAL: 'critical'>
    """
    # Validate inputs
    if not isinstance(z_score_value, (int, float)):
        raise ValueError("Z-score must be numeric")

    if not isinstance(threshold, (int, float)):
        raise ValueError("Threshold must be numeric")

    if threshold <= 0:
        raise ValueError("Threshold must be positive")

    # Use absolute value for significance assessment
    abs_z = abs(z_score_value)

    # Classify based on thresholds
    if abs_z < threshold:
        return SignificanceLevel.NONE
    elif abs_z < threshold + 1:
        return SignificanceLevel.LOW
    elif abs_z < threshold + 2:
        return SignificanceLevel.MEDIUM
    elif abs_z < threshold + 3:
        return SignificanceLevel.HIGH
    else:
        return SignificanceLevel.CRITICAL


def compute_beta_mean(alpha: float, beta: float) -> float:
    """Compute mean of Beta distribution.

    Args:
        alpha: Alpha parameter (must be > 0)
        beta: Beta parameter (must be > 0)

    Returns:
        Mean of the Beta distribution: alpha / (alpha + beta)

    Raises:
        ValueError: If alpha or beta are not positive
    """
    if alpha <= 0 or beta <= 0:
        raise ValueError("Alpha and beta must be positive")

    return float(alpha / (alpha + beta))


def compute_beta_variance(alpha: float, beta: float) -> float:
    """Compute variance of Beta distribution.

    Args:
        alpha: Alpha parameter (must be > 0)
        beta: Beta parameter (must be > 0)

    Returns:
        Variance of the Beta distribution

    Raises:
        ValueError: If alpha or beta are not positive
    """
    if alpha <= 0 or beta <= 0:
        raise ValueError("Alpha and beta must be positive")

    numerator = alpha * beta
    denominator = (alpha + beta) ** 2 * (alpha + beta + 1)

    return float(numerator / denominator)


def beta_mode(alpha: float, beta: float) -> float:
    """Compute mode of Beta distribution.

    The mode is defined only when alpha, beta > 1.

    Args:
        alpha: Alpha parameter (must be > 1 for mode to exist)
        beta: Beta parameter (must be > 1 for mode to exist)

    Returns:
        Mode of the Beta distribution: (alpha - 1) / (alpha + beta - 2)

    Raises:
        ValueError: If alpha or beta are not greater than 1
    """
    if alpha <= 1 or beta <= 1:
        raise ValueError("Mode is only defined for alpha, beta > 1")

    return float((alpha - 1) / (alpha + beta - 2))
