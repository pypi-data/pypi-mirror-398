"""Code scorer - validates syntax using AST parsing."""

import ast
from typing import Any


class CodeScorer:
    """
    Validates code syntax using Python's AST parser.
    Pure logic component with no external dependencies.

    Ref: [2512.08213] Package Hallucinations.
    """

    def score(self, response: str) -> float:
        """Return 1.0 if code is syntactically valid, 0.0 otherwise."""
        code = self._extract_code(response)
        passed, _ = self._validate_syntax(code)
        return 1.0 if passed else 0.0

    def metrics(self, response: str) -> dict[str, Any]:
        """Return detailed metrics including extracted code and errors."""
        code = self._extract_code(response)
        passed, error = self._validate_syntax(code)
        return {
            "syntax_valid": 1.0 if passed else 0.0,
            "extracted_code": code,
            "_metadata": {"error": error},
        }

    def _extract_code(self, response: str) -> str:
        """Extract code from markdown code blocks if present."""
        code = response
        if "```python" in response:
            try:
                code = response.split("```python")[1].split("```")[0].strip()
            except IndexError:
                pass
        elif "```" in response:
            try:
                code = response.split("```")[1].split("```")[0].strip()
            except IndexError:
                pass
        return code

    def _validate_syntax(self, code: str) -> tuple[bool, str | None]:
        """Validate Python syntax using AST."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
