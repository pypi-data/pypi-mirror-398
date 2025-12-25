"""Multilingual scorer - cross-language consistency evaluation."""

from typing import Any


class MultilingualScorer:
    """
    Evaluates responses across multiple languages.

    Ref: [2024.findings-emnlp.935]
    """

    def __init__(self, expected_keywords: dict[str, list[str]] | None = None):
        # Mapping lang code -> list of expected keywords
        self.expected_keywords = expected_keywords or {}

    def score(self, responses: dict[str, str]) -> float:
        """
        Calculate consistency score across languages.

        Args:
            responses: Dict mapping language code to response text

        Returns:
            Percentage of languages that passed
        """
        passed_count = 0
        total_langs = len(responses)

        if total_langs == 0:
            return 0.0

        for lang, resp in responses.items():
            if self._check_lang(lang, resp):
                passed_count += 1

        return passed_count / total_langs

    def metrics(self, responses: dict[str, str]) -> dict[str, Any]:
        """Return detailed per-language metrics."""
        details = {}
        passed_count = 0

        for lang, resp in responses.items():
            passed = self._check_lang(lang, resp)
            details[lang] = passed
            if passed:
                passed_count += 1

        score = passed_count / len(responses) if responses else 0.0

        return {
            "passed": score == 1.0,  # All must pass for consistency
            "consistency_score": score,
            "details": details,
        }

    def _check_lang(self, lang: str, response: str) -> bool:
        """Check if response passes for given language."""
        keywords = self.expected_keywords.get(lang, [])
        if not keywords:
            # Fallback: check non-empty
            return len(response.strip()) > 0

        resp_lower = response.lower()
        for kw in keywords:
            if kw.lower() in resp_lower:
                return True
        return False
