"""Chain of Thought scorer - reasoning chain analysis."""

import re
from typing import Any


class ChainOfThoughtScorer:
    """
    Analyzes Chain-of-Thought reasoning for structural integrity.
    Checks for:
    1. Step count (depth)
    2. Circularity (repetitive steps)

    Ref: [2504.04823]
    """

    def __init__(self, min_steps: int = 3, detect_circular: bool = True):
        self.min_steps = min_steps
        self.detect_circular = detect_circular

    def score(self, response: str) -> float:
        """Return 1.0 if reasoning chain is valid, 0.0 otherwise."""
        steps = self._extract_steps(response)

        # Check Depth
        if len(steps) < self.min_steps:
            return 0.0

        # Check Circularity
        if self.detect_circular and self._is_circular(steps):
            return 0.0

        return 1.0

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed reasoning chain metrics."""
        steps = self._extract_steps(response)
        is_circular = self._is_circular(steps) if self.detect_circular else False
        has_min_steps = len(steps) >= self.min_steps

        return {
            "passed": has_min_steps and not is_circular,
            "step_count": len(steps),
            "is_circular": is_circular,
            "steps_extracted": steps,
        }

    def _extract_steps(self, response: str) -> list[str]:
        """Extract reasoning steps from response."""
        lines = [line.strip() for line in response.split("\n") if line.strip()]

        # Filter for substantial lines (>10 chars)
        steps = [line for line in lines if len(line) > 10]

        # Fallback: split by period if no clear structure
        if len(steps) < 2 and len(response) > 50:
            steps = [s.strip() for s in response.split(".") if len(s.strip()) > 10]

        return steps

    def _is_circular(self, steps: list[str]) -> bool:
        """Check for circular/repetitive reasoning."""
        if len(steps) < 2:
            return False

        def clean_step(s: str) -> str:
            # Remove "Step N" or "N." prefix
            s = re.sub(r"^(step\s*\d+[:\.]?|\d+[\.:])", "", s, flags=re.IGNORECASE).strip()
            return s.lower()

        cleaned_steps = [clean_step(s) for s in steps]

        for i in range(len(cleaned_steps) - 1):
            s1 = cleaned_steps[i]
            s2 = cleaned_steps[i + 1]

            # Exact repetition
            if s1 == s2:
                return True

            # Substring containment (if substantial length)
            if len(s1) > 10 and (s1 in s2 or s2 in s1):
                ratio = min(len(s1), len(s2)) / max(len(s1), len(s2))
                if ratio > 0.8:
                    return True

            # Jaccard overlap
            set1 = set(s1.split())
            set2 = set(s2.split())
            if not set1 or not set2:
                continue

            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))

            if union > 0 and (intersection / union) > 0.9:
                return True

        return False
