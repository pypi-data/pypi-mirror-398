"""Tests for RepetitionScorer."""

from nerfprobe_core.scorers import RepetitionScorer


class TestRepetitionScorer:
    def test_no_repetition(self):
        scorer = RepetitionScorer(ngram_size=3, max_repeats=2)
        text = "The quick brown fox jumps over the lazy dog"
        assert scorer.score(text) == 1.0

    def test_excessive_repetition(self):
        scorer = RepetitionScorer(ngram_size=3, max_repeats=2)
        text = "the cat sat the cat sat the cat sat the cat sat"
        assert scorer.score(text) == 0.0

    def test_metrics_contains_max_repeats(self):
        scorer = RepetitionScorer(ngram_size=2, max_repeats=3)
        metrics = scorer.metrics("hello world hello world")
        assert "max_repeats" in metrics
