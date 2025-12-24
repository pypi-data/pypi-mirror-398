"""Base analyzer class for metacognition analysis."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers.

    All analyzer implementations should inherit from this class and implement
    the analyze method.
    """

    def __init__(self) -> None:
        """Initialize the analyzer."""
        self.name: str = self.__class__.__name__

    @abstractmethod
    def analyze(self, data: List[str]) -> Dict[str, Any]:
        """Analyze the given data for metacognitive patterns.

        Args:
            data: List of text samples to analyze

        Returns:
            A dictionary containing analysis results with metrics and statistics

        Raises:
            NotImplementedError: If the method is not implemented
        """
        raise NotImplementedError("Subclasses must implement the analyze method")

    def __repr__(self) -> str:
        """Return string representation of the analyzer.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}()"
