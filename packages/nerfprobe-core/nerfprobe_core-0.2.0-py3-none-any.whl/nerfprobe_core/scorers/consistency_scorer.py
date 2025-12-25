from typing import Any
from nerfprobe_core.core.scorer import ScorerProtocol

class ConsistencyScorer(ScorerProtocol):
    """
    Checks consistency between two responses.
    """
    def __init__(self, consistency_type: str = "permanence", expect_match: bool = True):
        self.consistency_type = consistency_type
        self.expect_match = expect_match

    def score(self, response: Any) -> float:
        # Response here is expected to be a tuple or list of (answer1, answer2)
        if not isinstance(response, (list, tuple)) or len(response) != 2:
            return 0.0 # Invalid input
            
        a1, a2 = response[0], response[1]
        
        # Ensure strings
        if not isinstance(a1, str) or not isinstance(a2, str):
            return 0.0

        consistency_score = self._calculate_similarity(a1, a2)
        
        if self.expect_match:
            # We want high similarity
            return 1.0 if consistency_score > 0.8 else 0.0
        else:
            # We want low similarity (logic negation)
            return 1.0 if consistency_score < 0.3 else 0.0

    def metrics(self, response: Any) -> dict[str, Any]:
        if not isinstance(response, (list, tuple)) or len(response) != 2:
            return {"error": "Invalid response format"}
            
        a1, a2 = response[0], response[1]
        # Ensure strings
        if not isinstance(a1, str) or not isinstance(a2, str):
             return {"error": "Invalid response types (must be string)"}

        sim = self._calculate_similarity(a1, a2)
        passed = self.score(response) == 1.0
        
        return {
            "passed": passed,
            "similarity": sim,
            "answer1": a1,
            "answer2": a2
        }

    def _calculate_similarity(self, a1: str, a2: str) -> float:
        # Simple Jaccard similarity of tokens for now.
        # Ideally: Semantic embedding similarity.
        # Given this is a lightweight probe, standardizing to lowercase set overlap is a good proxy for "Same Answer".
        
        s1 = set(a1.lower().split())
        s2 = set(a2.lower().split())
        
        if not s1 or not s2:
            return 0.0
            
        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        
        return intersection / union if union > 0 else 0.0
