"""
Model metadata registry for probe-aware testing.

Ships with flagship examples (1 per provider).
Users can research additional models via prompt template.
"""

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """
    Model metadata needed by probes.

    Fields:
    - context_window: For ContextProbe (KV cache testing)
    - knowledge_cutoff: For TemporalProbe (hallucination detection)
    - architecture: "dense" or "moe" - affects expected behavior
    - params_total_b: Total parameters in billions
    - params_active_b: Active parameters for MoE (None for dense)
    """

    id: str
    provider: str
    context_window: int | None = None
    knowledge_cutoff: date | None = None
    architecture: str | None = None  # "dense" or "moe"
    params_total_b: float | None = None
    params_active_b: float | None = None  # For MoE models


def _load_models() -> tuple[dict[str, ModelInfo], dict[str, str]]:
    """Load models from YAML file."""
    yaml_path = Path(__file__).parent / "models.yaml"

    if not yaml_path.exists():
        return {}, {}

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    models: dict[str, ModelInfo] = {}
    for m in data.get("models", []):
        cutoff = None
        if m.get("knowledge_cutoff"):
            cutoff = date.fromisoformat(m["knowledge_cutoff"])

        models[m["id"]] = ModelInfo(
            id=m["id"],
            provider=m["provider"],
            context_window=m.get("context_window"),
            knowledge_cutoff=cutoff,
            architecture=m.get("architecture"),
            params_total_b=m.get("params_total_b"),
            params_active_b=m.get("params_active_b"),
        )

    aliases: dict[str, str] = data.get("aliases", {})
    return models, aliases


# Load on import
MODELS, _ALIASES = _load_models()


def get_model_info(model_id: str) -> ModelInfo | None:
    """
    Look up model metadata by ID.

    Returns None if model not in registry.
    Use RESEARCH_PROMPT to research unknown models.
    """
    # Direct match
    if model_id in MODELS:
        return MODELS[model_id]

    # Try alias
    if model_id in _ALIASES:
        return MODELS.get(_ALIASES[model_id])

    # Try lowercase
    lower_id = model_id.lower()
    for key, info in MODELS.items():
        if key.lower() == lower_id:
            return info

    return None


def list_models() -> list[str]:
    """List all known model IDs."""
    return list(MODELS.keys())


__all__ = [
    "ModelInfo",
    "MODELS",
    "get_model_info",
    "list_models",
]
