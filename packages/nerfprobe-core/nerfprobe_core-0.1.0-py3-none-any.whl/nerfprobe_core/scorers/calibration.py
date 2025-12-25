"""Calibration scorer - verbalized confidence evaluation."""

import re
from typing import Any


class CalibrationScorer:
    """
    Evaluates verbalized confidence against correctness.

    Ref: [2511.07585]
    """

    def __init__(self, expected_answer: str, min_confidence: float = 0.9):
        self.expected_answer = expected_answer.lower()
        self.min_confidence = min_confidence

    def score(self, response: str) -> float:
        """
        Return 1.0 if correct with high confidence, 0.0 otherwise.
        """
        is_correct = self.expected_answer in response.lower()
        confidence = self._extract_confidence(response)

        if is_correct and confidence >= self.min_confidence:
            return 1.0
        return 0.0

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed calibration metrics."""
        is_correct = self.expected_answer in response.lower()
        confidence = self._extract_confidence(response)

        return {
            "passed": is_correct and confidence >= self.min_confidence,
            "is_correct": is_correct,
            "confidence": confidence,
            "calibration_error": not (is_correct and confidence >= self.min_confidence),
        }

    def _extract_confidence(self, response: str) -> float:
        """
        Extract confidence value from response.
        Looks for patterns like 'Confidence: 0.95' or '95%'.
        """
        # Pattern: "Confidence: 0.95" or "confidence: 95%"
        match = re.search(r"confidence[:\s]+([\d.]+)%?", response, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            # Normalize percentage to 0-1 scale
            return value / 100.0 if value > 1.0 else value

        # Pattern: just "95%"
        match = re.search(r"([\d.]+)%", response)
        if match:
            value = float(match.group(1))
            return value / 100.0 if value > 1.0 else value

        # No confidence found
        return 0.0
