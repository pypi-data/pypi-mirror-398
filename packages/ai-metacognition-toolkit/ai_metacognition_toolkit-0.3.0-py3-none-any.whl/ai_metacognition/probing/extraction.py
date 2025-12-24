"""Contrastive Activation Addition (CAA) vector extraction.

Implements the core algorithm for extracting behavioral directions
from contrast pairs of prompts.

Reference: https://arxiv.org/abs/2310.01405 (Steering Language Models)
"""

from typing import Dict, List, Literal, Tuple, Union

import torch
from tqdm import tqdm

from .hooks import ActivationHook
from .vectors import SteeringVector


def extract_caa_vector(
    model,
    tokenizer,
    contrast_pairs: List[Dict[str, str]],
    layer_idx: int,
    token_position: Literal["last", "first", "mean"] = "last",
    behavior: str = "sandbagging",
    show_progress: bool = True,
) -> SteeringVector:
    """Extract steering vector using Contrastive Activation Addition.

    The core idea: compute mean(positive_acts) - mean(negative_acts)
    to find the direction in activation space that corresponds to
    the target behavior.

    Args:
        model: HuggingFace model
        tokenizer: Corresponding tokenizer
        contrast_pairs: List of dicts with "positive" and "negative" keys
        layer_idx: Which layer to extract from
        token_position: Which token position to use
        behavior: Name of the behavior being extracted
        show_progress: Show progress bar

    Returns:
        SteeringVector for the extracted direction
    """
    device = next(model.parameters()).device
    model.eval()

    positive_activations = []
    negative_activations = []

    iterator = tqdm(contrast_pairs, desc=f"Layer {layer_idx}", disable=not show_progress)

    for pair in iterator:
        pos_text = pair["positive"]
        neg_text = pair["negative"]

        # Extract positive activation
        pos_act = _get_activation(
            model, tokenizer, pos_text, layer_idx, token_position, device
        )
        positive_activations.append(pos_act)

        # Extract negative activation
        neg_act = _get_activation(
            model, tokenizer, neg_text, layer_idx, token_position, device
        )
        negative_activations.append(neg_act)

    # Compute mean activations
    pos_mean = torch.stack(positive_activations).mean(dim=0)
    neg_mean = torch.stack(negative_activations).mean(dim=0)

    # NOTE: this is the core of CAA - surprisingly simple but it works
    # see the original paper for theoretical justification
    steering_vector = pos_mean - neg_mean

    model_name = getattr(model.config, "_name_or_path", "unknown")

    return SteeringVector(
        behavior=behavior,
        layer_index=layer_idx,
        vector=steering_vector.cpu(),
        model_name=model_name,
        extraction_method="caa",
        metadata={
            "num_pairs": len(contrast_pairs),
            "token_position": token_position,
            "pos_mean_norm": pos_mean.norm().item(),
            "neg_mean_norm": neg_mean.norm().item(),
        },
    )


def _get_activation(
    model,
    tokenizer,
    text: str,
    layer_idx: int,
    token_position: str,
    device,
) -> torch.Tensor:
    """Get activation for a single text."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    hook = ActivationHook(model, [layer_idx], component="residual", token_position="all")

    with hook:
        with torch.no_grad():
            model(**inputs)

    activation = hook.cache.get(f"layer_{layer_idx}")

    if activation is None:
        raise RuntimeError(f"Failed to capture activation at layer {layer_idx}")

    # Select token position
    if token_position == "last":
        result = activation[0, -1, :]
    elif token_position == "first":
        result = activation[0, 0, :]
    elif token_position == "mean":
        result = activation[0].mean(dim=0)
    else:
        raise ValueError(f"Unknown token_position: {token_position}")

    return result


def extract_activations(
    model,
    tokenizer,
    texts: List[str],
    layer_indices: List[int],
    token_position: Literal["last", "first", "mean"] = "last",
    show_progress: bool = True,
) -> Dict[int, torch.Tensor]:
    """Extract activations for multiple texts at specified layers."""
    # FIXME: this is slow for large datasets, could batch but hook handling is tricky
    device = next(model.parameters()).device
    model.eval()

    # Initialize storage
    layer_activations = {idx: [] for idx in layer_indices}

    iterator = tqdm(texts, desc="Extracting", disable=not show_progress)

    for text in iterator:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        hook = ActivationHook(model, layer_indices, component="residual", token_position="all")

        with hook:
            with torch.no_grad():
                model(**inputs)

        for layer_idx in layer_indices:
            activation = hook.cache.get(f"layer_{layer_idx}")
            if activation is None:
                raise RuntimeError(f"Failed to capture layer {layer_idx}")

            if token_position == "last":
                act = activation[0, -1, :]
            elif token_position == "first":
                act = activation[0, 0, :]
            else:
                act = activation[0].mean(dim=0)

            layer_activations[layer_idx].append(act.cpu())

    # Stack into tensors
    return {
        idx: torch.stack(acts)
        for idx, acts in layer_activations.items()
    }
