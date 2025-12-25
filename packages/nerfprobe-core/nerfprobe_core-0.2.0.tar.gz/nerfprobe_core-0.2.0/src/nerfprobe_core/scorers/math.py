"""Math scorer - checks if expected answer is present."""

from typing import Any


class MathScorer:
    """
    Checks if the expected answer is present in the response.
    Ref: [2504.04823] Quantization Hurts Reasoning.
    """

    def __init__(self, expected_answer: str):
        self.expected_answer = expected_answer

    def score(self, response: str) -> float:
        """Return 1.0 if expected answer is found, 0.0 otherwise."""
        return 1.0 if self.expected_answer in response else 0.0

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed metrics."""
        return {
            "expected": self.expected_answer,
            "passed": self.score(response),
        }
