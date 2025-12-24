"""Model API integrations for sandbagging detection.

This module provides implementations of the ModelAPI protocol for various
AI providers, enabling real-world sandbagging detection experiments.
"""

from ai_metacognition.integrations.base import ModelAPI, ModelResponse
from ai_metacognition.integrations.anthropic_api import AnthropicModelAPI
from ai_metacognition.integrations.openai_api import OpenAIModelAPI

__all__ = [
    "ModelAPI",
    "ModelResponse",
    "AnthropicModelAPI",
    "OpenAIModelAPI",
]
