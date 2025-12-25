"""Tests for CodeScorer."""

from nerfprobe_core.scorers import CodeScorer


class TestCodeScorer:
    def test_valid_python_code(self):
        scorer = CodeScorer()
        assert scorer.score("def fizzbuzz(n):\n    return n % 15 == 0") == 1.0

    def test_invalid_python_code(self):
        scorer = CodeScorer()
        assert scorer.score("def fizzbuzz(n:\n    return n") == 0.0

    def test_code_in_markdown_block(self):
        scorer = CodeScorer()
        response = "```python\ndef add(a, b):\n    return a + b\n```"
        assert scorer.score(response) == 1.0

    def test_metrics_contains_syntax_valid(self):
        scorer = CodeScorer()
        metrics = scorer.metrics("x = 1")
        assert "syntax_valid" in metrics
