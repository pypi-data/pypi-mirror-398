"""Entropy scorer - Shannon entropy for mode collapse detection."""

import math
from collections import Counter
from typing import Any


class EntropyScorer:
    """
    Calculates Shannon Entropy of a distribution of responses.

    Ref: [2407.01235] LLM Fingerprinting
    """

    def score(self, responses: list[str]) -> float:
        """
        Calculate entropy of response distribution.

        Args:
            responses: List of response strings

        Returns:
            Shannon entropy value
        """
        if not isinstance(responses, list):
            raise ValueError("EntropyScorer expects a list of response strings.")
        return self._calculate_entropy(responses)

    def metrics(self, responses: list[str]) -> dict[str, Any]:
        """Return detailed entropy metrics."""
        if not isinstance(responses, list):
            raise ValueError("EntropyScorer expects a list of response strings.")

        entropy = self._calculate_entropy(responses)
        counts = Counter([self._normalize(r) for r in responses])

        return {
            "entropy": entropy,
            "unique_count": len(counts),
            "total_count": len(responses),
            "_metadata": {"distribution": dict(counts)},
        }

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        return text.strip().lower()

    def _calculate_entropy(self, responses: list[str]) -> float:
        """Calculate Shannon entropy."""
        if not responses:
            return 0.0

        normalized = [self._normalize(r) for r in responses]
        total = len(normalized)
        counts = Counter(normalized)

        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        return entropy
