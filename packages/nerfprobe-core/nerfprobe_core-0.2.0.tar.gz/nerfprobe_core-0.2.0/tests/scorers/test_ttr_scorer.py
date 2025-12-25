"""Tests for TTRScorer."""

from nerfprobe_core.scorers import TTRScorer


class TestTTRScorer:
    def test_high_diversity_text(self):
        scorer = TTRScorer(sliding_window_size=5)
        text = "one two three four five six seven eight nine ten"
        assert scorer.score(text) >= 0.8

    def test_low_diversity_text(self):
        scorer = TTRScorer(sliding_window_size=5)
        text = "the the the the the the the the the the"
        assert scorer.score(text) <= 0.2

    def test_empty_text(self):
        scorer = TTRScorer()
        assert scorer.score("") == 0.0

    def test_metrics_contains_ttr(self):
        scorer = TTRScorer()
        metrics = scorer.metrics("hello world foo bar")
        assert "ttr" in metrics
        assert "min_local_ttr" in metrics
