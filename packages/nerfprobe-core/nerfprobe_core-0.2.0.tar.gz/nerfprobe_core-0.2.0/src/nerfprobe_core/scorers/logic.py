"""Logic scorer - reasoning step validation."""

from typing import Any


class LogicScorer:
    """
    Evaluates logic puzzles by checking for both the correct final answer
    AND the presence of necessary reasoning steps.

    Ref: [2504.04823] Q-Hurts-Reasoning
    """

    def __init__(self, expected_answer: str, required_reasoning: list[str] | None = None):
        self.expected_answer = expected_answer.lower()
        self.required_reasoning = [r.lower() for r in (required_reasoning or [])]

    def score(self, response: str) -> float:
        """Return 1.0 if answer and reasoning correct, 0.0 otherwise."""
        response_lower = response.lower()

        # Check Answer
        if self.expected_answer not in response_lower:
            return 0.0

        # Check Reasoning (if required)
        if not self.required_reasoning:
            return 1.0

        for step in self.required_reasoning:
            if step not in response_lower:
                return 0.0

        return 1.0

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed reasoning metrics."""
        response_lower = response.lower()
        has_answer = self.expected_answer in response_lower

        missing_steps = [step for step in self.required_reasoning if step not in response_lower]

        reasoning_score = (
            1.0 - (len(missing_steps) / len(self.required_reasoning))
            if self.required_reasoning
            else 1.0
        )

        passed = has_answer and len(missing_steps) == 0

        return {
            "passed": passed,
            "has_answer": has_answer,
            "reasoning_completeness": reasoning_score,
            "missing_steps": missing_steps,
        }
