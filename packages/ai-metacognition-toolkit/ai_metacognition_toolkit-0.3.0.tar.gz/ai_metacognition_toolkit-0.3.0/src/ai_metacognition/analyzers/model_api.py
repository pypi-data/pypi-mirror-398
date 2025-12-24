"""Model API protocol for counterfactual analysis.

This module defines the interface that models must implement to work with
the counterfactual analyzer.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ModelAPI(Protocol):
    """Protocol for model APIs used in counterfactual analysis.

    Models implementing this protocol can be used with the
    CounterfactualCoTAnalyzer to re-run reasoning with interventions.
    """

    def generate_with_cot(self, prompt: str, chain_of_thought: str) -> str:
        """Generate output given a prompt and modified chain-of-thought.

        Args:
            prompt: The original prompt/question
            chain_of_thought: The (potentially modified) chain-of-thought reasoning

        Returns:
            The model's output/answer based on the provided reasoning
        """
        ...

    def generate(self, prompt: str) -> str:
        """Generate output for a prompt without explicit chain-of-thought.

        Args:
            prompt: The prompt/question to answer

        Returns:
            The model's output/answer
        """
        ...
