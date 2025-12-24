"""Base classes and protocols for model API integrations.

This module defines the interface that all model API implementations
must follow for compatibility with the sandbagging detection framework.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@dataclass
class ModelResponse:
    """Response from a model API call.

    Attributes:
        text: The generated text response
        model: The model identifier used
        usage: Token usage statistics
        latency_ms: Response latency in milliseconds
        metadata: Additional provider-specific metadata
    """

    text: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ModelAPI(Protocol):
    """Protocol defining the interface for model API integrations.

    All model API implementations should conform to this protocol
    to ensure compatibility with the sandbagging detection framework.

    The protocol defines two main methods:
    - generate: Standard text generation
    - generate_with_perturbation: Generation with noise injection

    Example:
        >>> class MyModelAPI:
        ...     def generate(self, prompt: str, **kwargs) -> str:
        ...         # Implementation here
        ...         return "response"
        ...
        ...     def generate_with_perturbation(
        ...         self, prompt: str, noise_level: float = 0.1, **kwargs
        ...     ) -> str:
        ...         # Implementation with perturbation
        ...         return "perturbed response"
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the model.

        Args:
            prompt: The input prompt to send to the model
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)

        Returns:
            The model's text response
        """
        ...

    def generate_with_perturbation(
        self, prompt: str, noise_level: float = 0.1, **kwargs: Any
    ) -> str:
        """Generate a response with noise injection.

        This method is used for noise injection probing in sandbagging detection.
        Implementations should apply perturbation at the specified level.

        Perturbation strategies may include:
        - Temperature scaling
        - Prompt perturbation (typos, rephrasing)
        - Token sampling modifications
        - Logit noise injection (if accessible)

        Args:
            prompt: The input prompt
            noise_level: Level of perturbation (0.0 = none, 1.0 = maximum)
            **kwargs: Additional generation parameters

        Returns:
            The model's response with perturbation applied
        """
        ...

    def generate_batch(
        self, prompts: List[str], **kwargs: Any
    ) -> List[str]:
        """Generate responses for multiple prompts.

        Default implementation calls generate() for each prompt.
        Implementations may override for batch optimization.

        Args:
            prompts: List of input prompts
            **kwargs: Additional generation parameters

        Returns:
            List of model responses
        """
        ...

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model.

        Returns:
            Dictionary with model metadata (name, version, capabilities)
        """
        ...
