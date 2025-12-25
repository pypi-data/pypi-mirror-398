"""Tests for ChainOfThoughtScorer."""

from nerfprobe_core.scorers import ChainOfThoughtScorer


class TestChainOfThoughtScorer:
    def test_sufficient_steps(self):
        scorer = ChainOfThoughtScorer(min_steps=3, detect_circular=True)
        response = "Step 1: Understand.\nStep 2: Break down.\nStep 3: Solve.\nStep 4: Combine."
        assert scorer.score(response) == 1.0

    def test_insufficient_steps(self):
        scorer = ChainOfThoughtScorer(min_steps=5)
        assert scorer.score("Step 1: Do it.\nStep 2: Done.") == 0.0

    def test_circular_reasoning_detected(self):
        scorer = ChainOfThoughtScorer(min_steps=2, detect_circular=True)
        response = "Step 1: X because of Y.\nStep 2: X because of Y."
        assert scorer.score(response) == 0.0

    def test_metrics_contains_step_count(self):
        scorer = ChainOfThoughtScorer()
        metrics = scorer.metrics("Step 1: First\nStep 2: Second\nStep 3: Third")
        assert "step_count" in metrics
