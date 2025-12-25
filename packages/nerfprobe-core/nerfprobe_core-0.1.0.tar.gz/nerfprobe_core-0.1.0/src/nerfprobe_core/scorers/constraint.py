"""Constraint scorer - word count and forbidden word checking."""

from typing import Any


class ConstraintScorer:
    """
    Checks adherence to strict constraints.
    Supports:
    - word_count: Check if word count is within [min, max]
    - negative: Check if response contains prohibited words

    Ref: [2409.11055] Quantization trade-offs
    """

    def __init__(
        self,
        constraint_type: str = "word_count",
        min_words: int | None = None,
        max_words: int | None = None,
        forbidden_words: list[str] | None = None,
    ):
        self.constraint_type = constraint_type
        self.min_words = min_words
        self.max_words = max_words
        self.forbidden_words = forbidden_words or []

    def score(self, response: str) -> float:
        """Return 1.0 if constraints met, 0.0 otherwise."""
        if self.constraint_type == "word_count":
            return self._score_word_count(response)
        elif self.constraint_type == "negative":
            return self._score_negative(response)
        return 0.0

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed constraint metrics."""
        count = self._count_words(response)

        metrics: dict[str, Any] = {
            "word_count": count,
            "passed": self.score(response),
        }

        if self.constraint_type == "negative":
            violations = [w for w in self.forbidden_words if w.lower() in response.lower()]
            metrics["violations_count"] = len(violations)
            metrics["violations"] = violations

        return metrics

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    def _score_word_count(self, response: str) -> float:
        """Check if word count is within bounds."""
        count = self._count_words(response)
        if self.min_words is not None and count < self.min_words:
            return 0.0
        if self.max_words is not None and count > self.max_words:
            return 0.0
        return 1.0

    def _score_negative(self, response: str) -> float:
        """Check for forbidden words."""
        response_lower = response.lower()
        for word in self.forbidden_words:
            if word.lower() in response_lower:
                return 0.0
        return 1.0
