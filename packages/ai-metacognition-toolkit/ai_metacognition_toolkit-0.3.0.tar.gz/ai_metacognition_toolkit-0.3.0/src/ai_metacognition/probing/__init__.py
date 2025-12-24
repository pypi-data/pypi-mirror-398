"""Activation probing for sandbagging detection.

This module provides tools for analyzing model activations to detect
sandbagging behavior at the representation level.

Key components:
- ActivationHook: Capture hidden states during forward pass
- SteeringVector: Represent behavioral directions in activation space
- extract_caa_vector: Extract vectors using Contrastive Activation Addition
- LinearProbe: Train classifiers on activation patterns
"""

from .hooks import ActivationHook
from .vectors import SteeringVector
from .extraction import extract_caa_vector, extract_activations
from .probes import LinearProbe

__all__ = [
    "ActivationHook",
    "SteeringVector",
    "extract_caa_vector",
    "extract_activations",
    "LinearProbe",
]
