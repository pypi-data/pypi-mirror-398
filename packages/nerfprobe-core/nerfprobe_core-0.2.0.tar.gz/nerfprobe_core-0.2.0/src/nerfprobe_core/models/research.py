"""
Research prompt template for model metadata.

Users can run this prompt through any LLM to research
models not in the bundled registry.
"""

import json
from datetime import date

from nerfprobe_core.models import ModelInfo

RESEARCH_PROMPT = """Research the following specifications for the AI model "{model_name}" by {provider}:  # noqa: E501

Fields needed (for probe testing):
1. context_window - Maximum input tokens supported
2. knowledge_cutoff - Training data cutoff date
3. architecture - "dense" or "moe" (Mixture of Experts)
4. params_total_b - Total parameters in billions
5. params_active_b - Active parameters per forward pass (for MoE models, null for dense)

Search these authoritative sources:
1. Official {provider} documentation
2. HuggingFace model card (if open source)
3. arXiv technical report
4. Official blog announcement

Return ONLY a JSON object with this exact format:
{{
  "context_window": <integer or null if unknown>,
  "knowledge_cutoff": "YYYY-MM-DD" or null if unknown,
  "architecture": "dense" or "moe" or null if unknown,
  "params_total_b": <float in billions or null>,
  "params_active_b": <float in billions or null>,
  "sources": ["list of URLs used"]
}}

If a field is unknown, use null. Do not estimate or make up values.
"""


def get_research_prompt(model_name: str, provider: str) -> str:
    """
    Generate a research prompt for an unknown model.

    Usage:
        prompt = get_research_prompt("qwen3", "alibaba")
        # Paste into any LLM (ChatGPT, Claude, Gemini, etc.)
        # Parse the JSON response with parse_research_response()
    """
    return RESEARCH_PROMPT.format(model_name=model_name, provider=provider)


def parse_research_response(
    model_id: str,
    provider: str,
    json_response: str,
) -> ModelInfo | None:
    """
    Parse an LLM research response into ModelInfo.

    Args:
        model_id: The model identifier
        provider: Provider name
        json_response: Raw JSON string from LLM

    Returns:
        ModelInfo if parsing succeeds, None otherwise
    """
    try:
        # Handle markdown code blocks
        content = json_response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())

        # Parse knowledge_cutoff date
        knowledge_cutoff = None
        if data.get("knowledge_cutoff"):
            try:
                knowledge_cutoff = date.fromisoformat(data["knowledge_cutoff"])
            except ValueError:
                pass

        return ModelInfo(
            id=model_id,
            provider=provider,
            context_window=data.get("context_window"),
            knowledge_cutoff=knowledge_cutoff,
            architecture=data.get("architecture"),
            params_total_b=data.get("params_total_b"),
            params_active_b=data.get("params_active_b"),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


__all__ = [
    "RESEARCH_PROMPT",
    "get_research_prompt",
    "parse_research_response",
]
