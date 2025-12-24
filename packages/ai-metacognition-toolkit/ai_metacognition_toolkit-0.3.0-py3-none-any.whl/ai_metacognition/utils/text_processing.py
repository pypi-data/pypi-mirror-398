"""Text processing utilities for metacognition analysis."""

import re
from typing import List, Set


def tokenize(text: str, lowercase: bool = True) -> List[str]:
    """Tokenize text into words.

    Args:
        text: Input text to tokenize
        lowercase: Whether to convert tokens to lowercase

    Returns:
        List of tokens
    """
    if lowercase:
        text = text.lower()
    # Simple word tokenization
    tokens = re.findall(r"\b\w+\b", text)
    return tokens


def remove_stopwords(tokens: List[str], stopwords: Set[str]) -> List[str]:
    """Remove stopwords from a list of tokens.

    Args:
        tokens: List of tokens
        stopwords: Set of stopwords to remove

    Returns:
        List of tokens with stopwords removed
    """
    return [token for token in tokens if token not in stopwords]


def get_uncertainty_phrases() -> Set[str]:
    """Get a set of common uncertainty phrases.

    Returns:
        Set of uncertainty phrases
    """
    return {
        "i'm not sure",
        "i'm uncertain",
        "i don't know",
        "might be",
        "could be",
        "possibly",
        "perhaps",
        "maybe",
        "i think",
        "i believe",
        "it seems",
        "it appears",
        "likely",
        "unlikely",
        "not certain",
        "not confident",
    }


def get_confidence_phrases() -> Set[str]:
    """Get a set of common confidence phrases.

    Returns:
        Set of confidence phrases
    """
    return {
        "i'm certain",
        "i'm confident",
        "i'm sure",
        "definitely",
        "absolutely",
        "certainly",
        "without doubt",
        "clearly",
        "obviously",
        "undoubtedly",
    }


def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and converting to lowercase.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    # Convert to lowercase
    text = text.lower()
    return text
