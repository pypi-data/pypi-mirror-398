import json
import re
from typing import Any, Dict, Optional
from jsonschema import validate, ValidationError
from nerfprobe_core.core.scorer import ScorerProtocol

class JsonScorer(ScorerProtocol):
    """
    Validates JSON structure and schema adherence.
    Handles strict vs lenient parsing logic.
    """
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None, strict: bool = True):
        self.schema = schema
        self.strict = strict

    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown wrappers if lenient mode."""
        if self.strict:
            return text
            
        # Try markdown code blocks
        if "```json" in text:
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match: return match.group(1)
            
        if "```" in text:
            match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if match: return match.group(1)
            
        # Try raw JSON pattern
        json_match = re.search(r'(\{[^{}]*\}|\[[^\[\]]*\])', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
            
        return text

    def score(self, response: Any) -> float:
        """Return 1.0 if valid JSON (and schema matches), 0.0 otherwise."""
        if not isinstance(response, str):
            return 0.0
            
        try:
            json_text = self._extract_json(response)
            data = json.loads(json_text)
            
            if self.schema:
                validate(instance=data, schema=self.schema)
                
            return 1.0
        except (json.JSONDecodeError, ValidationError, Exception):
            return 0.0

    def metrics(self, response: Any) -> dict[str, Any]:
        """Return detailed validation metrics."""
        if not isinstance(response, str):
             return {
                "valid_json": 0.0,
                "extraction_used": 0.0,
                "_metadata": {"errors": ["Input not string"]}
            }

        json_text = self._extract_json(response)
        errors = []
        is_valid = False
        extraction_used = json_text != response
        
        try:
            data = json.loads(json_text)
            if self.schema:
                validate(instance=data, schema=self.schema)
            is_valid = True
        except Exception as e:
            errors.append(str(e))
            
        return {
            "valid_json": 1.0 if is_valid else 0.0,
            "extraction_used": 1.0 if extraction_used else 0.0,
            "_metadata": {
                "errors": errors,
                "strict_mode": self.strict
            }
        }
