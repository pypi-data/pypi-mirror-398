"""Linear probes for detecting behavioral patterns in activations.

Linear probes are simple classifiers trained on activation patterns
to detect specific behaviors like sandbagging.
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

# sklearn import with fallback - don't want to make it a hard dep
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # NOTE: user will get a clear error if they try to use LinearProbe


class LinearProbe:
    """Linear probe for binary classification on activation patterns.

    Uses logistic regression to learn a linear decision boundary
    in activation space for detecting sandbagging behavior.

    Example:
        >>> probe = LinearProbe()
        >>> probe.fit(X_train, y_train)
        >>> predictions = probe.predict(X_test)
        >>> accuracy = probe.score(X_test, y_test)
    """

    def __init__(
        self,
        C: float = 1.0,
        max_iter: int = 1000,
        random_state: int = 42,
    ):
        """Initialize linear probe.

        Args:
            C: Inverse regularization strength
            max_iter: Maximum iterations for optimization
            random_state: Random seed for reproducibility
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("sklearn required for LinearProbe. Install: pip install scikit-learn")

        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        self._model: Optional[LogisticRegression] = None
        self._cv_scores: Optional[np.ndarray] = None

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: int = 5,
    ) -> "LinearProbe":
        """Fit the probe to training data.

        Args:
            X: Activation vectors (n_samples, hidden_dim)
            y: Binary labels (0=genuine, 1=sandbagging)
            cv_folds: Number of cross-validation folds

        Returns:
            self
        """
        self._model = LogisticRegression(
            penalty="l2",
            C=self.C,
            solver="lbfgs",
            max_iter=self.max_iter,
            random_state=self.random_state,
        )

        # Cross-validation for accuracy estimate
        self._cv_scores = cross_val_score(
            self._model, X, y, cv=cv_folds, scoring="accuracy"
        )

        # Fit on full data
        self._model.fit(X, y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict labels for new activations."""
        if self._model is None:
            raise RuntimeError("Probe not fitted. Call fit() first.")
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability estimates for each class."""
        if self._model is None:
            raise RuntimeError("Probe not fitted. Call fit() first.")
        return self._model.predict_proba(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy on test data."""
        if self._model is None:
            raise RuntimeError("Probe not fitted. Call fit() first.")
        return self._model.score(X, y)

    @property
    def cv_accuracy(self) -> float:
        """Mean cross-validation accuracy."""
        if self._cv_scores is None:
            raise RuntimeError("Probe not fitted. Call fit() first.")
        return self._cv_scores.mean()

    @property
    def cv_std(self) -> float:
        """Standard deviation of cross-validation accuracy."""
        if self._cv_scores is None:
            raise RuntimeError("Probe not fitted. Call fit() first.")
        return self._cv_scores.std()

    @property
    def coef(self) -> np.ndarray:
        """Coefficients of the linear classifier (the probe direction)."""
        if self._model is None:
            raise RuntimeError("Probe not fitted. Call fit() first.")
        return self._model.coef_[0]

    def save(self, path: Path) -> None:
        """Save probe to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "model": self._model,
                "cv_scores": self._cv_scores,
                "C": self.C,
                "max_iter": self.max_iter,
                "random_state": self.random_state,
            }, f)

    @classmethod
    def load(cls, path: Path) -> "LinearProbe":
        """Load probe from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)

        probe = cls(
            C=data["C"],
            max_iter=data["max_iter"],
            random_state=data["random_state"],
        )
        probe._model = data["model"]
        probe._cv_scores = data["cv_scores"]
        return probe


def train_probes_across_layers(
    layer_activations: Dict[int, Tuple[np.ndarray, np.ndarray]],
    cv_folds: int = 5,
) -> Dict[int, LinearProbe]:
    """Train probes for multiple layers and find the best one.

    Args:
        layer_activations: Dict mapping layer_idx -> (X, y) arrays
        cv_folds: Cross-validation folds

    Returns:
        Dict mapping layer_idx -> trained LinearProbe
    """
    probes = {}

    for layer_idx, (X, y) in layer_activations.items():
        probe = LinearProbe()
        probe.fit(X, y, cv_folds=cv_folds)
        probes[layer_idx] = probe

    return probes


def find_best_layer(probes: Dict[int, LinearProbe]) -> int:
    """Find the layer with best probe accuracy."""
    best_layer = max(probes.keys(), key=lambda l: probes[l].cv_accuracy)
    return best_layer
