"""Tests for MultilingualScorer."""

from nerfprobe_core.scorers import MultilingualScorer


class TestMultilingualScorer:
    def test_all_languages_nonempty(self):
        scorer = MultilingualScorer()
        responses = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}
        assert scorer.score(responses) == 1.0

    def test_one_language_empty(self):
        scorer = MultilingualScorer()
        responses = {"en": "Hello", "fr": "", "de": "Hallo"}
        assert scorer.score(responses) < 1.0

    def test_with_expected_keywords(self):
        scorer = MultilingualScorer(expected_keywords={"en": ["hello"], "fr": ["bonjour"]})
        responses = {"en": "Hello there", "fr": "Salut"}
        metrics = scorer.metrics(responses)
        assert metrics["details"]["en"] is True
        assert metrics["details"]["fr"] is False
