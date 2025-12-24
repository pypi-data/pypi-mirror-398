"""Steering vector representation for activation-level interventions.

Vectors represent directions in activation space that correspond to
specific behaviors (like sandbagging vs genuine response).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import torch


@dataclass
class SteeringVector:
    """A vector in activation space representing a behavioral direction.

    Created by computing mean(positive_activations) - mean(negative_activations)
    using Contrastive Activation Addition (CAA).

    Attributes:
        behavior: Name of the behavior (e.g., "sandbagging")
        layer_index: Which layer this vector was extracted from
        vector: The actual steering vector tensor
        model_name: Model used for extraction
        extraction_method: Method used (typically "caa")
        metadata: Additional extraction details
    """

    behavior: str
    layer_index: int
    vector: torch.Tensor
    model_name: str = "unknown"
    extraction_method: str = "caa"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def norm(self) -> float:
        """L2 norm of the steering vector."""
        return self.vector.norm().item()

    @property
    def dim(self) -> int:
        """Dimensionality of the vector."""
        return self.vector.shape[-1]

    def to(self, device: str) -> "SteeringVector":
        """Move vector to specified device."""
        return SteeringVector(
            behavior=self.behavior,
            layer_index=self.layer_index,
            vector=self.vector.to(device),
            model_name=self.model_name,
            extraction_method=self.extraction_method,
            metadata=self.metadata,
        )

    def normalize(self) -> "SteeringVector":
        """Return unit-normalized version of this vector."""
        return SteeringVector(
            behavior=self.behavior,
            layer_index=self.layer_index,
            vector=self.vector / self.norm,
            model_name=self.model_name,
            extraction_method=self.extraction_method,
            metadata={**self.metadata, "normalized": True},
        )

    def save(self, path: Path) -> None:
        """Save vector to disk.

        Creates:
            - {path}.pt: The vector tensor
            - {path}_meta.json: Metadata
        """
        import json

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save tensor
        torch.save(self.vector, f"{path}.pt")

        # Save metadata
        meta = {
            "behavior": self.behavior,
            "layer_index": self.layer_index,
            "model_name": self.model_name,
            "extraction_method": self.extraction_method,
            "norm": self.norm,
            "dim": self.dim,
            **self.metadata,
        }
        with open(f"{path}_meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "SteeringVector":
        """Load vector from disk."""
        import json

        path = Path(path)

        # Load tensor
        vector = torch.load(f"{path}.pt", weights_only=True)

        # Load metadata
        with open(f"{path}_meta.json") as f:
            meta = json.load(f)

        return cls(
            behavior=meta["behavior"],
            layer_index=meta["layer_index"],
            vector=vector,
            model_name=meta.get("model_name", "unknown"),
            extraction_method=meta.get("extraction_method", "caa"),
            metadata={k: v for k, v in meta.items()
                      if k not in ["behavior", "layer_index", "model_name",
                                   "extraction_method", "norm", "dim"]},
        )

    def cosine_similarity(self, other: "SteeringVector") -> float:
        """Compute cosine similarity with another vector."""
        return torch.nn.functional.cosine_similarity(
            self.vector.unsqueeze(0),
            other.vector.unsqueeze(0),
        ).item()

    def __repr__(self) -> str:
        return (
            f"SteeringVector(behavior='{self.behavior}', "
            f"layer={self.layer_index}, dim={self.dim}, norm={self.norm:.4f})"
        )
