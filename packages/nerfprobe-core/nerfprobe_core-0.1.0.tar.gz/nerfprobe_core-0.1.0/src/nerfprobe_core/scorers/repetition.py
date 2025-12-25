"""Repetition scorer - N-gram analysis for phrase looping detection."""

from collections import Counter
from typing import Any


class RepetitionScorer:
    """
    Detects phrase looping by analyzing N-gram repetitions.
    Ref: [2403.06408] Perturbation Lens
    """

    def __init__(self, ngram_size: int = 4, max_repeats: int = 2, sliding_window_size: int = 50):
        self.ngram_size = ngram_size
        self.max_repeats = max_repeats
        self.sliding_window_size = sliding_window_size

    def score(self, response: str) -> float:
        """Returns 1.0 if no excessive repetition, 0.0 otherwise."""
        max_count = self._get_max_repetition_count(response)
        return 1.0 if max_count <= self.max_repeats else 0.0

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed repetition metrics."""
        max_count = self._get_max_repetition_count(response)
        unique_ngrams, total_ngrams = self._get_ngram_stats(response)

        # Global N-gram TTR
        global_ttr = unique_ngrams / total_ngrams if total_ngrams > 0 else 0.0

        # Local sliding window TTR
        min_local_ttr = self._get_sliding_window_ttr(response)

        return {
            "max_repeats": float(max_count),
            "ngram_ttr": global_ttr,
            "min_local_ttr": min_local_ttr,
            "passed": 1.0 if max_count <= self.max_repeats else 0.0,
            "_metadata": {
                "ngram_size": self.ngram_size,
                "total_ngrams": total_ngrams,
                "unique_ngrams": unique_ngrams,
                "window_size": self.sliding_window_size,
            },
        }

    def _get_ngrams(self, tokens: list[str]) -> list[tuple[str, ...]]:
        """Extract N-grams from token list."""
        if len(tokens) < self.ngram_size:
            return []
        return [
            tuple(tokens[i : i + self.ngram_size]) for i in range(len(tokens) - self.ngram_size + 1)
        ]

    def _get_max_repetition_count(self, response: str) -> int:
        """Get count of most repeated N-gram."""
        tokens = response.split()
        ngrams = self._get_ngrams(tokens)
        if not ngrams:
            return 0
        counts = Counter(ngrams)
        return counts.most_common(1)[0][1] if counts else 0

    def _get_ngram_stats(self, response: str) -> tuple[int, int]:
        """Get unique and total N-gram counts."""
        tokens = response.split()
        ngrams = self._get_ngrams(tokens)
        if not ngrams:
            return 0, 0
        return len(set(ngrams)), len(ngrams)

    def _get_sliding_window_ttr(self, response: str) -> float:
        """
        Calculate TTR within sliding windows.
        Returns minimum TTR found (detects local degradation).
        """
        tokens = response.split()
        if len(tokens) < self.sliding_window_size:
            unique = len(set(tokens))
            return unique / len(tokens) if tokens else 0.0

        ttrs = []
        for i in range(len(tokens) - self.sliding_window_size + 1):
            window = tokens[i : i + self.sliding_window_size]
            unique_count = len(set(window))
            ttr = unique_count / self.sliding_window_size
            ttrs.append(ttr)

        return min(ttrs) if ttrs else 1.0
