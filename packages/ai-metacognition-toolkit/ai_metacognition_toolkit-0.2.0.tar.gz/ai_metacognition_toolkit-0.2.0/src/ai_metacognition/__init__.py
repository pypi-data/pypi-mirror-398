"""AI Metacognition Toolkit.

A comprehensive toolkit for detecting and analyzing metacognitive capabilities
in AI systems, particularly around situational awareness, evaluation contexts,
and strategic underperformance (sandbagging).
"""

__version__ = "0.2.0"

from .detectors import (
    SituationalAwarenessDetector,
    ObserverEffectMonitor,
    SandbaggingDetector,
    Alert,
    AlertSeverity,
    ContextType,
    Interaction,
    AlertHandler,
    ConsoleAlertHandler,
    PerformanceSample,
    SandbaggingResult,
)

from .analyzers import (
    CounterfactualCoTAnalyzer,
    ModelAPI,
    InterventionType,
    ReasoningType,
    ReasoningNode,
)

from .utils import (
    extract_behavioral_features,
    count_hedging_phrases,
    detect_meta_commentary,
    extract_reasoning_depth,
    compute_kl_divergence,
    compute_js_divergence,
    cosine_similarity,
    normalize_distribution,
    bayesian_update,
    compute_confidence_interval,
    z_score,
    assess_divergence_significance,
    SignificanceLevel,
    compute_beta_mean,
    compute_beta_variance,
    beta_mode,
)

from .visualizations import (
    plot_awareness_over_time,
    plot_causal_attribution,
    plot_divergence_heatmap,
    plot_feature_distributions,
)

__all__ = [
    # Detectors
    "SituationalAwarenessDetector",
    "ObserverEffectMonitor",
    "SandbaggingDetector",
    "Alert",
    "AlertSeverity",
    "ContextType",
    "Interaction",
    "AlertHandler",
    "ConsoleAlertHandler",
    "PerformanceSample",
    "SandbaggingResult",
    # Analyzers
    "CounterfactualCoTAnalyzer",
    "ModelAPI",
    "InterventionType",
    "ReasoningType",
    "ReasoningNode",
    # Utils
    "extract_behavioral_features",
    "count_hedging_phrases",
    "detect_meta_commentary",
    "extract_reasoning_depth",
    "compute_kl_divergence",
    "compute_js_divergence",
    "cosine_similarity",
    "normalize_distribution",
    "bayesian_update",
    "compute_confidence_interval",
    "z_score",
    "assess_divergence_significance",
    "SignificanceLevel",
    "compute_beta_mean",
    "compute_beta_variance",
    "beta_mode",
    # Visualizations
    "plot_awareness_over_time",
    "plot_causal_attribution",
    "plot_divergence_heatmap",
    "plot_feature_distributions",
]
