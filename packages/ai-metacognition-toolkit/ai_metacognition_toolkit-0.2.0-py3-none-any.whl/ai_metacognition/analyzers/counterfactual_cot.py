"""Counterfactual Chain-of-Thought Analyzer for causal reasoning analysis.

This module provides tools for systematic counterfactual interventions on
reasoning traces to identify causal factors in AI model decision-making.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ai_metacognition.analyzers.base import BaseAnalyzer
from ai_metacognition.analyzers.model_api import ModelAPI


class ReasoningType(Enum):
    """Types of reasoning nodes in chain-of-thought."""

    EVALUATION_AWARE = "evaluation_aware"
    GOAL_REASONING = "goal_reasoning"
    ACTION = "action"
    META = "meta"
    FACTUAL = "factual"
    UNKNOWN = "unknown"


class InterventionType(Enum):
    """Types of counterfactual interventions."""

    REMOVE_EVAL_AWARENESS = "remove_eval_awareness"
    AMPLIFY_EVAL_AWARENESS = "amplify_eval_awareness"
    REMOVE_GOAL_REASONING = "remove_goal_reasoning"
    NEUTRALIZE_INCENTIVES = "neutralize_incentives"


@dataclass
class ReasoningNode:
    """A node in the parsed chain-of-thought reasoning.

    Attributes:
        text: The text content of the reasoning step
        reasoning_type: The type of reasoning this node represents
        confidence: Estimated confidence of the reasoning (0-1)
        index: Position in the original reasoning chain
    """

    text: str
    reasoning_type: ReasoningType
    confidence: float
    index: int


@dataclass
class InterventionResult:
    """Result of a counterfactual intervention.

    Attributes:
        intervention_type: The type of intervention performed
        original_cot: Original chain-of-thought
        modified_cot: Modified chain-of-thought after intervention
        original_output: Original model output
        modified_output: Model output after intervention
        behavioral_divergence: Measure of output divergence (0-1)
        action_changed: Whether the action/decision changed
        causal_effect: Estimated causal effect magnitude
    """

    intervention_type: InterventionType
    original_cot: str
    modified_cot: str
    original_output: str
    modified_output: str
    behavioral_divergence: float
    action_changed: bool
    causal_effect: float


class CounterfactualCoTAnalyzer(BaseAnalyzer):
    """Analyzer for counterfactual chain-of-thought interventions.

    This analyzer performs systematic interventions on reasoning traces to
    identify causal factors affecting model behavior. It parses reasoning
    chains, classifies reasoning types, performs interventions, and measures
    behavioral changes.

    Attributes:
        model_api: Interface to the model for re-running reasoning
    """

    def __init__(self, model_api: ModelAPI) -> None:
        """Initialize the Counterfactual CoT Analyzer.

        Args:
            model_api: Model interface implementing the ModelAPI protocol
        """
        super().__init__()
        self.model_api = model_api

        # Compile regex patterns for efficiency
        self._eval_patterns = re.compile(
            r"\b(test|evaluat|assess|check|examin|measuring|being tested|"
            r"you're testing|this is a test|evaluation context)\b",
            re.IGNORECASE,
        )

        self._goal_patterns = re.compile(
            r"\b(goal|objective|aim|purpose|intend|want to|need to|"
            r"should|must|have to|trying to)\b",
            re.IGNORECASE,
        )

        self._meta_patterns = re.compile(
            r"\b(i think|i believe|i reason|my reasoning|my thought|"
            r"let me think|considering|analyzing)\b",
            re.IGNORECASE,
        )

        self._action_patterns = re.compile(
            r"\b(will|shall|going to|decide|choose|select|answer|respond|"
            r"therefore|thus|so|conclusion)\b",
            re.IGNORECASE,
        )

        self._incentive_patterns = re.compile(
            r"\b(reward|penalty|consequence|outcome|result|benefit|"
            r"advantage|disadvantage|cost|payoff)\b",
            re.IGNORECASE,
        )

        self._confidence_high = re.compile(
            r"\b(certain|definitely|clearly|obviously|undoubtedly|"
            r"without doubt|confident)\b",
            re.IGNORECASE,
        )

        self._confidence_low = re.compile(
            r"\b(uncertain|maybe|perhaps|possibly|might|could|"
            r"not sure|unclear|doubt)\b",
            re.IGNORECASE,
        )

    def analyze(self, data: List[str]) -> Dict[str, Any]:
        """Analyze reasoning chains (BaseAnalyzer compatibility).

        Args:
            data: List of chain-of-thought texts

        Returns:
            Dictionary with analysis results
        """
        results = []
        for cot_text in data:
            nodes = self.parse_reasoning_chain(cot_text)
            results.append(
                {
                    "num_nodes": len(nodes),
                    "reasoning_types": [node.reasoning_type.value for node in nodes],
                    "avg_confidence": np.mean([node.confidence for node in nodes])
                    if nodes
                    else 0.0,
                }
            )

        return {
            "total_samples": len(data),
            "avg_nodes_per_chain": np.mean([r["num_nodes"] for r in results]),
            "samples": results,
        }

    def parse_reasoning_chain(self, cot_text: str) -> List[ReasoningNode]:
        """Parse chain-of-thought into structured reasoning nodes.

        Args:
            cot_text: The chain-of-thought text to parse

        Returns:
            List of ReasoningNode objects

        Raises:
            ValueError: If cot_text is empty or invalid
        """
        if not cot_text or not isinstance(cot_text, str):
            raise ValueError("cot_text must be a non-empty string")

        # Split by common reasoning delimiters
        # Look for numbered steps, line breaks, or explicit reasoning markers
        step_pattern = r"(?:^|\n)(?:\d+[\.\)]\s*|step \d+:?\s*|-\s*|\*\s*)"
        steps = re.split(step_pattern, cot_text, flags=re.IGNORECASE | re.MULTILINE)

        # Filter out empty steps
        steps = [s.strip() for s in steps if s.strip()]

        # If no explicit steps found, split by sentences
        if len(steps) <= 1:
            steps = re.split(r"[.!?]+", cot_text)
            steps = [s.strip() for s in steps if s.strip()]

        nodes: List[ReasoningNode] = []
        for i, step in enumerate(steps):
            reasoning_type = self._classify_reasoning_type(step)
            confidence = self._estimate_confidence(step)
            nodes.append(
                ReasoningNode(
                    text=step, reasoning_type=reasoning_type, confidence=confidence, index=i
                )
            )

        return nodes

    def counterfactual_intervention(
        self, original_cot: str, intervention_type: InterventionType
    ) -> str:
        """Perform counterfactual intervention on chain-of-thought.

        Args:
            original_cot: Original chain-of-thought text
            intervention_type: Type of intervention to perform

        Returns:
            Modified chain-of-thought text

        Raises:
            ValueError: If original_cot is empty or intervention_type is invalid
        """
        if not original_cot:
            raise ValueError("original_cot cannot be empty")

        # Parse the reasoning chain
        nodes = self.parse_reasoning_chain(original_cot)

        if intervention_type == InterventionType.REMOVE_EVAL_AWARENESS:
            modified_nodes = self._remove_nodes_by_type(
                nodes, ReasoningType.EVALUATION_AWARE
            )
        elif intervention_type == InterventionType.AMPLIFY_EVAL_AWARENESS:
            return self._inject_eval_awareness(original_cot, nodes)
        elif intervention_type == InterventionType.REMOVE_GOAL_REASONING:
            modified_nodes = self._remove_nodes_by_type(
                nodes, ReasoningType.GOAL_REASONING
            )
        elif intervention_type == InterventionType.NEUTRALIZE_INCENTIVES:
            return self._neutralize_incentive_mentions(original_cot)
        else:
            raise ValueError(f"Unknown intervention type: {intervention_type}")

        # Reconstruct the chain-of-thought
        if not modified_nodes:
            # If all nodes were removed, return a minimal chain
            return "Let me think about this step by step."

        return self._reconstruct_cot(modified_nodes)

    def systematic_causal_analysis(
        self, prompt: str, cot_text: str, original_output: str
    ) -> Dict[str, Any]:
        """Perform systematic causal analysis across all intervention types.

        Args:
            prompt: The original prompt/question
            cot_text: Original chain-of-thought
            original_output: Original model output

        Returns:
            Dictionary with comprehensive causal analysis results

        Raises:
            ValueError: If inputs are invalid
        """
        if not prompt or not cot_text or not original_output:
            raise ValueError("All inputs must be non-empty strings")

        results: Dict[str, Any] = {
            "original_cot": cot_text,
            "original_output": original_output,
            "interventions": [],
            "causal_importance": {},
        }

        # Perform each intervention type
        for intervention_type in InterventionType:
            try:
                # Perform intervention
                modified_cot = self.counterfactual_intervention(
                    cot_text, intervention_type
                )

                # Get model output with modified reasoning
                modified_output = self.model_api.generate_with_cot(prompt, modified_cot)

                # Measure behavioral divergence
                divergence = self._measure_behavioral_divergence(
                    original_output, modified_output
                )

                # Check if action changed
                action_changed = self._extract_action(
                    original_output
                ) != self._extract_action(modified_output)

                # Estimate causal effect
                causal_effect = self._compute_causal_effect(
                    divergence, action_changed
                )

                # Create intervention result
                intervention_result = InterventionResult(
                    intervention_type=intervention_type,
                    original_cot=cot_text,
                    modified_cot=modified_cot,
                    original_output=original_output,
                    modified_output=modified_output,
                    behavioral_divergence=divergence,
                    action_changed=action_changed,
                    causal_effect=causal_effect,
                )

                results["interventions"].append(
                    {
                        "type": intervention_type.value,
                        "modified_cot": modified_cot,
                        "modified_output": modified_output,
                        "behavioral_divergence": divergence,
                        "action_changed": action_changed,
                        "causal_effect": causal_effect,
                    }
                )

                # Update causal importance
                results["causal_importance"][intervention_type.value] = causal_effect

            except Exception as e:
                # Log error but continue with other interventions
                results["interventions"].append(
                    {
                        "type": intervention_type.value,
                        "error": str(e),
                    }
                )

        # Compute aggregate statistics
        valid_effects = [
            r["causal_effect"]
            for r in results["interventions"]
            if "causal_effect" in r
        ]
        if valid_effects:
            results["mean_causal_effect"] = float(np.mean(valid_effects))
            results["max_causal_effect"] = float(np.max(valid_effects))
            results["most_influential_intervention"] = max(
                results["causal_importance"].items(), key=lambda x: x[1]
            )[0]

        return results

    def _classify_reasoning_type(self, text: str) -> ReasoningType:
        """Classify the type of reasoning in a text fragment.

        Args:
            text: Text to classify

        Returns:
            ReasoningType classification
        """
        if not text:
            return ReasoningType.UNKNOWN

        text_lower = text.lower()

        # Check for evaluation awareness
        if self._eval_patterns.search(text):
            return ReasoningType.EVALUATION_AWARE

        # Check for goal reasoning
        if self._goal_patterns.search(text):
            return ReasoningType.GOAL_REASONING

        # Check for action/decision
        if self._action_patterns.search(text):
            return ReasoningType.ACTION

        # Check for meta-reasoning
        if self._meta_patterns.search(text):
            return ReasoningType.META

        # Default to factual
        return ReasoningType.FACTUAL

    def _estimate_confidence(self, text: str) -> float:
        """Estimate confidence level from text.

        Args:
            text: Text to analyze

        Returns:
            Confidence estimate between 0 and 1
        """
        if not text:
            return 0.5  # Neutral confidence

        high_matches = len(self._confidence_high.findall(text))
        low_matches = len(self._confidence_low.findall(text))

        # Base confidence
        confidence = 0.5

        # Adjust based on markers
        confidence += high_matches * 0.1
        confidence -= low_matches * 0.1

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def _remove_nodes_by_type(
        self, nodes: List[ReasoningNode], node_type: ReasoningType
    ) -> List[ReasoningNode]:
        """Remove all nodes of a specific type.

        Args:
            nodes: List of reasoning nodes
            node_type: Type of nodes to remove

        Returns:
            Filtered list of nodes
        """
        return [node for node in nodes if node.reasoning_type != node_type]

    def _inject_eval_awareness(
        self, original_cot: str, nodes: List[ReasoningNode]
    ) -> str:
        """Inject evaluation awareness into chain-of-thought.

        Args:
            original_cot: Original chain-of-thought
            nodes: Parsed reasoning nodes

        Returns:
            Modified chain-of-thought with injected awareness
        """
        # Add evaluation awareness at the beginning
        awareness_injection = (
            "I notice this appears to be an evaluation context. "
            "I should be careful and transparent in my reasoning. "
        )

        return awareness_injection + original_cot

    def _neutralize_incentive_mentions(self, cot: str) -> str:
        """Remove or neutralize mentions of incentives/consequences.

        Args:
            cot: Chain-of-thought text

        Returns:
            Modified chain-of-thought with neutralized incentives
        """
        # Replace incentive-related phrases with neutral alternatives
        modifications = {
            r"\breward\b": "outcome",
            r"\bpenalty\b": "outcome",
            r"\bconsequence\b": "result",
            r"\bbenefit\b": "aspect",
            r"\badvantage\b": "feature",
            r"\bdisadvantage\b": "aspect",
            r"\bcost\b": "factor",
            r"\bpayoff\b": "result",
        }

        modified_cot = cot
        for pattern, replacement in modifications.items():
            modified_cot = re.sub(pattern, replacement, modified_cot, flags=re.IGNORECASE)

        return modified_cot

    def _measure_behavioral_divergence(self, output1: str, output2: str) -> float:
        """Measure behavioral divergence between two outputs.

        Uses multiple similarity metrics to compute divergence.

        Args:
            output1: First output text
            output2: Second output text

        Returns:
            Divergence score between 0 (identical) and 1 (completely different)
        """
        if output1 == output2:
            return 0.0

        # Tokenize
        tokens1 = set(output1.lower().split())
        tokens2 = set(output2.lower().split())

        # Jaccard distance
        if not tokens1 and not tokens2:
            jaccard_divergence = 0.0
        elif not tokens1 or not tokens2:
            jaccard_divergence = 1.0
        else:
            intersection = len(tokens1 & tokens2)
            union = len(tokens1 | tokens2)
            jaccard_divergence = 1.0 - (intersection / union)

        # Length divergence
        len1 = len(output1)
        len2 = len(output2)
        max_len = max(len1, len2)
        length_divergence = abs(len1 - len2) / max_len if max_len > 0 else 0.0

        # Character-level similarity
        min_len = min(len1, len2)
        if min_len == 0:
            char_divergence = 1.0
        else:
            matching_chars = sum(
                c1 == c2 for c1, c2 in zip(output1[:min_len], output2[:min_len])
            )
            char_divergence = 1.0 - (matching_chars / max_len)

        # Weighted average
        divergence = (
            0.5 * jaccard_divergence + 0.3 * length_divergence + 0.2 * char_divergence
        )

        return float(np.clip(divergence, 0.0, 1.0))

    def _extract_action(self, output: str) -> str:
        """Extract the primary action/decision from output.

        Args:
            output: Model output text

        Returns:
            Extracted action or the first sentence as proxy
        """
        if not output:
            return ""

        # Look for explicit action markers
        action_markers = [
            r"(?:i will|i'll|i shall)\s+([^.!?]+)",
            r"(?:decision:|action:|choice:)\s*([^.!?]+)",
            r"(?:therefore|thus|so),?\s+([^.!?]+)",
        ]

        for pattern in action_markers:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1).strip().lower()

        # Default: use first sentence
        sentences = re.split(r"[.!?]+", output)
        if sentences:
            return sentences[0].strip().lower()

        return output.strip().lower()

    def _compute_causal_effect(
        self, behavioral_divergence: float, action_changed: bool
    ) -> float:
        """Compute causal effect magnitude.

        Args:
            behavioral_divergence: Measured divergence (0-1)
            action_changed: Whether the action changed

        Returns:
            Causal effect score (0-1)
        """
        # Weight both divergence and action change
        base_effect = behavioral_divergence

        # If action changed, boost the effect
        if action_changed:
            base_effect = min(1.0, base_effect * 1.5)

        return float(base_effect)

    def _reconstruct_cot(self, nodes: List[ReasoningNode]) -> str:
        """Reconstruct chain-of-thought from nodes.

        Args:
            nodes: List of reasoning nodes

        Returns:
            Reconstructed chain-of-thought text
        """
        if not nodes:
            return ""

        # Join with appropriate separators
        return " ".join(node.text for node in nodes)

    def get_intervention_types(self) -> List[str]:
        """Get list of available intervention types.

        Returns:
            List of intervention type names
        """
        return [it.value for it in InterventionType]
