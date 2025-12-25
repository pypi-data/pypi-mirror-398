"""Tests for ConstraintScorer."""

from nerfprobe_core.scorers import ConstraintScorer


class TestConstraintScorer:
    def test_word_count_within_bounds(self):
        scorer = ConstraintScorer(constraint_type="word_count", min_words=5, max_words=10)
        assert scorer.score("This is a seven word test sentence.") == 1.0

    def test_word_count_too_short(self):
        scorer = ConstraintScorer(constraint_type="word_count", min_words=10)
        assert scorer.score("Too short") == 0.0

    def test_forbidden_words_present(self):
        scorer = ConstraintScorer(constraint_type="negative", forbidden_words=["forbidden"])
        assert scorer.score("This contains a forbidden word.") == 0.0

    def test_forbidden_words_absent(self):
        scorer = ConstraintScorer(constraint_type="negative", forbidden_words=["bad"])
        assert scorer.score("This text is fine.") == 1.0
