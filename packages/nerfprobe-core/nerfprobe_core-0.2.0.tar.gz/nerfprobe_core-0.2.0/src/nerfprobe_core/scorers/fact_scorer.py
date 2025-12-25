from typing import Any
from nerfprobe_core.core.scorer import ScorerProtocol

class FactScorer(ScorerProtocol):
    """
    Checks if the expected factual text is present in the response (case-insensitive).
    """
    def __init__(self, expected_text: str):
        self.expected_text = expected_text

    def score(self, response: Any) -> float:
        if not isinstance(response, str):
            return 0.0
        return 1.0 if self.expected_text.lower() in response.lower() else 0.0

    def metrics(self, response: Any) -> dict[str, Any]:
        val = 0.0
        if isinstance(response, str):
            val = self.score(response)
            
        return {
            "expected": self.expected_text,
            "passed": val
        }
