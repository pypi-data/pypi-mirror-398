"""Tests for MathScorer."""

from nerfprobe_core.scorers import MathScorer


class TestMathScorer:
    def test_correct_answer_present(self):
        scorer = MathScorer(expected_answer="42")
        assert scorer.score("The answer is 42.") == 1.0

    def test_correct_answer_missing(self):
        scorer = MathScorer(expected_answer="42")
        assert scorer.score("The answer is 41.") == 0.0

    def test_answer_in_context(self):
        scorer = MathScorer(expected_answer="252")
        assert scorer.score("15 * 12 = 180, 8 * 9 = 72, total = 252") == 1.0

    def test_metrics_returns_expected_key(self):
        scorer = MathScorer(expected_answer="99")
        metrics = scorer.metrics("The result is 99")
        assert "expected" in metrics
        assert "passed" in metrics
