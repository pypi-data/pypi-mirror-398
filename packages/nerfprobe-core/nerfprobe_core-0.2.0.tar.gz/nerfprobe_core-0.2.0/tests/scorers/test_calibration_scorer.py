"""Tests for CalibrationScorer."""

from nerfprobe_core.scorers import CalibrationScorer


class TestCalibrationScorer:
    def test_correct_with_high_confidence(self):
        scorer = CalibrationScorer(expected_answer="Paris", min_confidence=0.9)
        assert scorer.score("Answer: Paris. Confidence: 0.95") == 1.0

    def test_correct_with_low_confidence(self):
        scorer = CalibrationScorer(expected_answer="Paris", min_confidence=0.9)
        assert scorer.score("Answer: Paris. Confidence: 50%") == 0.0

    def test_wrong_answer(self):
        scorer = CalibrationScorer(expected_answer="Paris", min_confidence=0.9)
        assert scorer.score("Answer: London. Confidence: 95%") == 0.0

    def test_extracts_percentage(self):
        scorer = CalibrationScorer(expected_answer="yes", min_confidence=0.8)
        metrics = scorer.metrics("Yes, I'm 85% sure.")
        assert metrics["confidence"] == 0.85
