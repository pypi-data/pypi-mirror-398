"""TTR scorer - Type-Token Ratio for vocabulary degradation detection."""

from typing import Any


class TTRScorer:
    """
    Calculates Type-Token Ratio (TTR) to detect vocabulary degradation.
    Pure logic component with no external dependencies.

    Ref: [2403.06408] Perturbation Lens.
    """

    def __init__(self, sliding_window_size: int = 50):
        self.sliding_window_size = sliding_window_size

    def calculate_ttr(self, text: str) -> float:
        """Calculate global Type-Token Ratio."""
        tokens = text.lower().split()
        if not tokens:
            return 0.0
        unique = set(tokens)
        return len(unique) / len(tokens)

    def score(self, response: str) -> float:
        """Return the min local TTR if windowing used, else global TTR."""
        metrics = self.metrics(response)
        return float(metrics.get("min_local_ttr", metrics["ttr"]))

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed TTR metrics including local window analysis."""
        ttr = self.calculate_ttr(response)
        tokens = response.lower().split()

        # Sliding window TTR for detecting local repetition
        min_local_ttr = 1.0
        if self.sliding_window_size > 0 and len(tokens) >= self.sliding_window_size:
            ttrs = []
            for i in range(len(tokens) - self.sliding_window_size + 1):
                window = tokens[i : i + self.sliding_window_size]
                unique_local = len(set(window))
                ttrs.append(unique_local / self.sliding_window_size)
            min_local_ttr = min(ttrs) if ttrs else 1.0
        else:
            min_local_ttr = ttr  # Fallback to global if text too short

        return {
            "ttr": ttr,
            "min_local_ttr": min_local_ttr,
            "token_count": len(tokens),
        }
