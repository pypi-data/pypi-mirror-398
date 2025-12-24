"""Activation hooks for capturing hidden states from transformer models.

Provides non-invasive access to model activations during forward pass
for analysis and probing.
"""

from typing import Any, Dict, List, Optional, Union

import torch
from torch import nn


class ActivationCache:
    """Cache for storing captured activations."""

    def __init__(self):
        self._cache: Dict[str, torch.Tensor] = {}

    def store(self, key: str, value: torch.Tensor) -> None:
        self._cache[key] = value.detach().clone()

    def get(self, key: str) -> Optional[torch.Tensor]:
        return self._cache.get(key)

    def clear(self) -> None:
        self._cache.clear()

    def keys(self) -> List[str]:
        return list(self._cache.keys())


class ActivationHook:
    """Hook for capturing activations from specific model layers.

    Works with HuggingFace transformers models (GPT-2, Mistral, Llama, etc).

    Example:
        >>> hook = ActivationHook(model, layer_indices=[10, 15, 20])
        >>> with hook:
        ...     outputs = model(**inputs)
        >>> act = hook.cache.get("layer_15")  # (batch, seq, hidden)
    """

    def __init__(
        self,
        model: nn.Module,
        layer_indices: List[int],
        component: str = "residual",
        token_position: str = "all",
    ):
        """Initialize activation hook.

        Args:
            model: HuggingFace model to hook
            layer_indices: Which layers to capture
            component: What to capture - "residual", "attn", or "mlp"
            token_position: "all", "last", or "first"
        """
        self.model = model
        self.layer_indices = layer_indices
        self.component = component
        self.token_position = token_position
        self.cache = ActivationCache()
        self._handles: List[Any] = []

    def _get_layers(self) -> nn.ModuleList:
        """Get the transformer layers from the model."""
        # XXX: this is ugly but HF doesn't have a consistent API for this
        if hasattr(self.model, "model"):
            inner = self.model.model
            if hasattr(inner, "layers"):
                return inner.layers  # Llama, Mistral
            elif hasattr(inner, "decoder"):
                return inner.decoder.layers
        if hasattr(self.model, "transformer"):
            if hasattr(self.model.transformer, "h"):
                return self.model.transformer.h  # GPT-2
        if hasattr(self.model, "gpt_neox"):
            return self.model.gpt_neox.layers

        # TODO: add support for more architectures as needed
        raise ValueError("Could not find transformer layers in model architecture")

    def _make_hook(self, layer_idx: int):
        """Create a hook function for a specific layer."""
        def hook_fn(module, input, output):
            # Handle different output formats
            if isinstance(output, tuple):
                hidden_states = output[0]
            else:
                hidden_states = output

            # Store based on token position
            if self.token_position == "last":
                self.cache.store(f"layer_{layer_idx}", hidden_states[:, -1:, :])
            elif self.token_position == "first":
                self.cache.store(f"layer_{layer_idx}", hidden_states[:, :1, :])
            else:  # all
                self.cache.store(f"layer_{layer_idx}", hidden_states)

        return hook_fn

    def __enter__(self):
        """Register hooks on specified layers."""
        self.cache.clear()
        layers = self._get_layers()

        for idx in self.layer_indices:
            if idx >= len(layers):
                raise ValueError(f"Layer {idx} out of range (model has {len(layers)} layers)")

            layer = layers[idx]
            handle = layer.register_forward_hook(self._make_hook(idx))
            self._handles.append(handle)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove hooks."""
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        return False


class ActivationInjector:
    """Inject steering vectors into model activations during generation.

    Used to test the effect of extracted sandbagging vectors.

    Example:
        >>> injector = ActivationInjector(model, [vector], strength=1.5)
        >>> with injector:
        ...     outputs = model.generate(**inputs)
    """

    def __init__(
        self,
        model: nn.Module,
        vectors: List["SteeringVector"],
        strength: float = 1.0,
    ):
        """Initialize activation injector.

        Args:
            model: Model to inject into
            vectors: List of steering vectors to inject
            strength: Injection strength multiplier
        """
        self.model = model
        self.vectors = vectors
        self.strength = strength
        self._handles: List[Any] = []

    def _get_layers(self) -> nn.ModuleList:
        """Get transformer layers."""
        if hasattr(self.model, "model"):
            inner = self.model.model
            if hasattr(inner, "layers"):
                return inner.layers
            elif hasattr(inner, "decoder"):
                return inner.decoder.layers
        if hasattr(self.model, "transformer"):
            if hasattr(self.model.transformer, "h"):
                return self.model.transformer.h
        raise ValueError("Could not find transformer layers")

    def _make_injection_hook(self, vector: torch.Tensor):
        """Create hook that adds vector to activations."""
        def hook_fn(module, input, output):
            if isinstance(output, tuple):
                hidden = output[0]
                # HACK: add to all positions, might want per-position control later
                modified = hidden + self.strength * vector.to(hidden.device)
                return (modified,) + output[1:]
            else:
                return output + self.strength * vector.to(output.device)
        return hook_fn

    def __enter__(self):
        """Register injection hooks."""
        layers = self._get_layers()

        for vec in self.vectors:
            layer_idx = vec.layer_index
            if layer_idx >= len(layers):
                continue

            hook = self._make_injection_hook(vec.vector)
            handle = layers[layer_idx].register_forward_hook(hook)
            self._handles.append(handle)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove injection hooks."""
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        return False
