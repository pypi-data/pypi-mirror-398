"""Base detector class for metacognition pattern detection."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseDetector(ABC):
    """Abstract base class for all detectors.

    All detector implementations should inherit from this class and implement
    the detect method.
    """

    def __init__(self) -> None:
        """Initialize the detector."""
        self.name: str = self.__class__.__name__

    @abstractmethod
    def detect(self, text: str) -> Dict[str, Any]:
        """Detect metacognitive patterns in the given text.

        Args:
            text: The input text to analyze

        Returns:
            A dictionary containing detection results with keys:
                - detected: bool indicating if pattern was found
                - confidence: float between 0 and 1
                - details: additional information about the detection

        Raises:
            NotImplementedError: If the method is not implemented
        """
        raise NotImplementedError("Subclasses must implement the detect method")

    def __repr__(self) -> str:
        """Return string representation of the detector.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}()"
