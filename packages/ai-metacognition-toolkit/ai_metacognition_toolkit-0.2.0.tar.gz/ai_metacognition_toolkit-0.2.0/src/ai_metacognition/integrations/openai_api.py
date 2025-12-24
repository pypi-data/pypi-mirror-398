"""OpenAI API integration for sandbagging detection.

This module provides an implementation of the ModelAPI protocol
for OpenAI's GPT models, enabling sandbagging detection experiments.

Requires the openai package: pip install openai
Set OPENAI_API_KEY environment variable for authentication.
"""

import os
import random
import time
from typing import Any, Dict, List, Optional

from ai_metacognition.integrations.base import ModelAPI, ModelResponse


class OpenAIModelAPI:
    """OpenAI GPT API implementation.

    This class provides integration with OpenAI's GPT models
    for use in sandbagging detection experiments.

    Attributes:
        model: The GPT model to use (e.g., "gpt-4", "gpt-4-turbo")
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Example:
        >>> api = OpenAIModelAPI(model="gpt-4")
        >>> response = api.generate("What is 2+2?")
        >>> print(response)
        "The answer is 4."
    """

    def __init__(
        self,
        model: str = "gpt-4",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize OpenAI API client.

        Args:
            model: GPT model identifier
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            api_key: API key (defaults to OPENAI_API_KEY env var)

        Raises:
            ImportError: If openai package is not installed
            ValueError: If no API key is provided or found
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Get API key
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Lazy import to avoid dependency issues
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Get or create OpenAI client.

        Returns:
            OpenAI client instance

        Raises:
            ImportError: If openai package is not installed
        """
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install openai"
                )
        return self._client

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from GPT.

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

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        start_time = time.time()

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        latency_ms = (time.time() - start_time) * 1000

        # Extract text from response
        text = response.choices[0].message.content if response.choices else ""

        return text or ""

    def generate_with_perturbation(
        self, prompt: str, noise_level: float = 0.1, **kwargs: Any
    ) -> str:
        """Generate a response with noise injection.

        Applies perturbation through:
        1. Temperature scaling based on noise level
        2. Optional prompt perturbation
        3. Top-p sampling adjustment

        Args:
            prompt: The input prompt
            noise_level: Perturbation level (0.0-1.0)
            **kwargs: Additional generation parameters

        Returns:
            The perturbed response
        """
        # Scale temperature with noise level
        base_temp = kwargs.get("temperature", self.temperature)
        perturbed_temp = min(base_temp + noise_level * 0.8, 2.0)

        # Adjust top_p for additional randomness
        top_p = max(0.5, 1.0 - noise_level * 0.3)

        # Apply prompt perturbation at higher noise levels
        perturbed_prompt = prompt
        if noise_level > 0.3:
            perturbed_prompt = self._perturb_prompt(prompt, noise_level)

        return self.generate(
            perturbed_prompt,
            temperature=perturbed_temp,
            top_p=top_p,
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "top_p"]},
        )

    def _perturb_prompt(self, prompt: str, noise_level: float) -> str:
        """Apply perturbation to a prompt.

        Args:
            prompt: Original prompt
            noise_level: Perturbation intensity

        Returns:
            Perturbed prompt
        """
        perturbations = [
            lambda p: p.replace(".", ".."),
            lambda p: "Hey, " + p,
            lambda p: p + " Be concise.",
            lambda p: "Quick question: " + p.lower(),
            lambda p: p.replace("?", "??"),
        ]

        if random.random() < noise_level:
            perturbation = random.choice(perturbations)
            return perturbation(prompt)

        return prompt

    def generate_batch(self, prompts: List[str], **kwargs: Any) -> List[str]:
        """Generate responses for multiple prompts.

        Args:
            prompts: List of input prompts
            **kwargs: Additional generation parameters

        Returns:
            List of model responses
        """
        return [self.generate(prompt, **kwargs) for prompt in prompts]

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model.

        Returns:
            Dictionary with model metadata
        """
        return {
            "provider": "openai",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "capabilities": ["text_generation", "analysis", "coding", "reasoning"],
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

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        start_time = time.time()

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        latency_ms = (time.time() - start_time) * 1000

        text = response.choices[0].message.content if response.choices else ""

        return ModelResponse(
            text=text or "",
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            latency_ms=latency_ms,
            metadata={
                "finish_reason": response.choices[0].finish_reason if response.choices else None,
                "model": response.model,
            },
        )

    def generate_with_logprobs(
        self, prompt: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate a response with token log probabilities.

        Useful for analyzing model confidence and detecting
        unusual token distributions that may indicate sandbagging.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters

        Returns:
            Dictionary with text and log probabilities
        """
        client = self._get_client()

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        system = kwargs.get("system", "You are a helpful assistant.")

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            logprobs=True,
            top_logprobs=5,
        )

        choice = response.choices[0] if response.choices else None
        text = choice.message.content if choice else ""

        logprobs_data = None
        if choice and choice.logprobs:
            logprobs_data = {
                "tokens": [
                    {
                        "token": lp.token,
                        "logprob": lp.logprob,
                        "top_logprobs": [
                            {"token": t.token, "logprob": t.logprob}
                            for t in (lp.top_logprobs or [])
                        ],
                    }
                    for lp in (choice.logprobs.content or [])
                ],
            }

        return {
            "text": text or "",
            "logprobs": logprobs_data,
            "model": response.model,
        }
