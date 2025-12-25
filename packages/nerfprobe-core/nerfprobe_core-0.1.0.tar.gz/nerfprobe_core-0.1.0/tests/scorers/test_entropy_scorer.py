"""Tests for EntropyScorer."""

from nerfprobe_core.scorers import EntropyScorer


class TestEntropyScorer:
    def test_high_entropy_diverse_responses(self):
        scorer = EntropyScorer()
        responses = ["cat", "dog", "bird", "fish", "bear"]
        assert scorer.score(responses) > 2.0

    def test_low_entropy_same_responses(self):
        scorer = EntropyScorer()
        assert scorer.score(["cat"] * 5) == 0.0

    def test_empty_list(self):
        scorer = EntropyScorer()
        assert scorer.score([]) == 0.0

    def test_metrics_contains_unique_count(self):
        scorer = EntropyScorer()
        metrics = scorer.metrics(["a", "b", "a", "c"])
        assert metrics["unique_count"] == 3
