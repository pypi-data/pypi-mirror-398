"""Tests for LogicScorer."""

from nerfprobe_core.scorers import LogicScorer


class TestLogicScorer:
    def test_correct_answer_with_reasoning(self):
        scorer = LogicScorer(expected_answer="72", required_reasoning=["48 / 2 = 24", "48 + 24"])
        response = "First, 48 / 2 = 24 clips in May. Then 48 + 24 = 72 total."
        assert scorer.score(response) == 1.0

    def test_correct_answer_missing_reasoning(self):
        scorer = LogicScorer(expected_answer="72", required_reasoning=["48 / 2 = 24"])
        assert scorer.score("The answer is 72.") == 0.0

    def test_wrong_answer(self):
        scorer = LogicScorer(expected_answer="72")
        assert scorer.score("The answer is 71.") == 0.0

    def test_metrics_contains_completeness(self):
        scorer = LogicScorer(expected_answer="10", required_reasoning=["5 + 5"])
        metrics = scorer.metrics("5 + 5 = 10")
        assert "reasoning_completeness" in metrics
