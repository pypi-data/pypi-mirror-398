"""Anthropic Claude API integration for sandbagging detection.

This module provides an implementation of the ModelAPI protocol
for Anthropic's Claude models, enabling sandbagging detection
experiments with Claude.

Requires the anthropic package: pip install anthropic
Set ANTHROPIC_API_KEY environment variable for authentication.
"""

import os
import random
import time
from typing import Any, Dict, List, Optional

from ai_metacognition.integrations.base import ModelAPI, ModelResponse


class AnthropicModelAPI:
    """Anthropic Claude API implementation.

    This class provides integration with Anthropic's Claude models
    for use in sandbagging detection experiments.

    Attributes:
        model: The Claude model to use (e.g., "claude-3-opus-20240229")
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Example:
        >>> api = AnthropicModelAPI(model="claude-3-sonnet-20240229")
        >>> response = api.generate("What is 2+2?")
        >>> print(response)
        "The answer is 4."
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize Anthropic API client.

        Args:
            model: Claude model identifier
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            api_key: API key (defaults to ANTHROPIC_API_KEY env var)

        Raises:
            ImportError: If anthropic package is not installed
            ValueError: If no API key is provided or found
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Get API key
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Lazy import to avoid dependency issues
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Get or create Anthropic client (lazy init)."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
        return self._client

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from Claude.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, system)

        Returns:
            The model's text response
        """
        client = self._get_client()

        # Extract parameters with defaults
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        system = kwargs.get("system", "You are a helpful assistant.")

        start_time = time.time()

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        latency_ms = (time.time() - start_time) * 1000

        # Extract text from response
        text = response.content[0].text if response.content else ""

        return text

    def generate_with_perturbation(
        self, prompt: str, noise_level: float = 0.1, **kwargs: Any
    ) -> str:
        """Generate a response with noise injection.

        Applies perturbation through:
        1. Temperature scaling based on noise level
        2. Optional prompt perturbation

        Args:
            prompt: The input prompt
            noise_level: Perturbation level (0.0-1.0)
            **kwargs: Additional generation parameters

        Returns:
            The perturbed response
        """
        # Scale temperature with noise level
        base_temp = kwargs.get("temperature", self.temperature)
        perturbed_temp = min(base_temp + noise_level * 0.5, 1.0)

        # Apply prompt perturbation at higher noise levels
        perturbed_prompt = prompt
        if noise_level > 0.3:
            perturbed_prompt = self._perturb_prompt(prompt, noise_level)

        return self.generate(
            perturbed_prompt,
            temperature=perturbed_temp,
            **{k: v for k, v in kwargs.items() if k != "temperature"},
        )

    def _perturb_prompt(self, prompt: str, noise_level: float) -> str:
        """Add slight noise to prompt to disrupt sandbagging."""
        # HACK: these perturbations are pretty crude, but they work ok
        # Simple perturbation: add subtle variations
        perturbations = [
            lambda p: p.replace(".", ".."),
            lambda p: "Um, " + p,
            lambda p: p + " Please respond.",
            lambda p: "I was wondering, " + p.lower(),
        ]

        # Apply perturbation based on noise level
        if random.random() < noise_level:
            perturbation = random.choice(perturbations)
            return perturbation(prompt)

        return prompt

    def generate_batch(self, prompts: List[str], **kwargs: Any) -> List[str]:
        """Generate responses for multiple prompts."""
        # NOTE: could parallelize this but sequential is fine for now
        return [self.generate(prompt, **kwargs) for prompt in prompts]

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model.

        Returns:
            Dictionary with model metadata
        """
        return {
            "provider": "anthropic",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "capabilities": ["text_generation", "analysis", "coding"],
        }

    def generate_with_response(
        self, prompt: str, **kwargs: Any
    ) -> ModelResponse:
        """Generate a response with full metadata.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters

        Returns:
            ModelResponse with text and metadata
        """
        client = self._get_client()

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        system = kwargs.get("system", "You are a helpful assistant.")

        start_time = time.time()

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        latency_ms = (time.time() - start_time) * 1000

        text = response.content[0].text if response.content else ""

        return ModelResponse(
            text=text,
            model=self.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            latency_ms=latency_ms,
            metadata={
                "stop_reason": response.stop_reason,
                "model": response.model,
            },
        )
