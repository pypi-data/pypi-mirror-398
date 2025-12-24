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

# Probing module (requires torch, transformers, sklearn)
# Import separately to avoid hard dependency
try:
    from .probing import (
        ActivationHook,
        SteeringVector,
        LinearProbe,
        extract_caa_vector,
        extract_activations,
    )
    _PROBING_AVAILABLE = True
except ImportError:
    _PROBING_AVAILABLE = False

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

# Add probing exports if available
if _PROBING_AVAILABLE:
    __all__.extend([
        "ActivationHook",
        "SteeringVector",
        "LinearProbe",
        "extract_caa_vector",
        "extract_activations",
    ])
