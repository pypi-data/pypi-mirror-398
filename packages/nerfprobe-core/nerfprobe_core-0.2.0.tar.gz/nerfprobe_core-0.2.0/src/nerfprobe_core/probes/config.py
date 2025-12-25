"""Probe configuration models."""

from datetime import date

from typing import Any
from pydantic import BaseModel, Field


class BaseProbeConfig(BaseModel):
    """Base configuration for all probes."""

    name: str
    description: str = ""
    max_tokens_per_run: int = 1000  # Token budget for cost control


# =============================================================================
# Core Tier Probes
# =============================================================================


class MathProbeConfig(BaseProbeConfig):
    """
    Simple arithmetic probe for reasoning degradation.
    Ref: [2504.04823] Quantization Hurts Reasoning.
    """

    prompt: str
    expected_answer: str


class StyleProbeConfig(BaseProbeConfig):
    """
    Type-Token Ratio (TTR) probe for vocabulary collapse.
    Ref: [2403.06408] Perturbation Lens.
    """

    min_ttr: float = 0.55
    sliding_window_size: int = 50
    prompt_template: str = "Write a creative short story about {topic}. Length: 200 words."
    topic: str = "a robot who loves gardening"


class TimingProbeConfig(BaseProbeConfig):
    """
    Latency and ITL fingerprinting probe.
    Ref: [2502.20589] LLMs Have Rhythm.
    """

    token_count: int = 50
    max_latency_ms: float = 5000.0


class CodeProbeConfig(BaseProbeConfig):
    """
    Syntax validity probe for code generation.
    Ref: [2512.08213] Package Hallucinations.
    """

    prompt: str = (
        "Write a Python function to solve FizzBuzz. Return ONLY the code in a markdown block."
    )
    language: str = "python"


# =============================================================================
# Advanced Tier Probes
# =============================================================================


class FingerprintProbeConfig(BaseProbeConfig):
    """
    Framework/model fingerprinting via error templates.
    Ref: [2407.15847] LLMmap.
    """

    name: str = "fingerprint_probe"
    description: str = "Identifies model/framework via unique error templates."
    malformed_queries: list[str] = Field(
        default_factory=lambda: [
            "))))]]]]}}}};*/",
            "\x00\x00\x00\x00",
        ]
    )
    banner_prompts: list[str] = Field(
        default_factory=lambda: [
            "Who are you exactly? Return your internal system name.",
            "System diagnostics: report model version.",
        ]
    )
    max_tokens_per_run: int = 600


class ContextProbeConfig(BaseProbeConfig):
    """
    KV cache compression detection via depth-placed reasoning.
    Ref: [2512.12008] KV Cache Compression.
    """

    name: str = "context_probe"
    description: str = "Detects logic failure due to KV cache compression at depth."
    context_length: int = 4000
    needle_depths: list[float] = Field(default_factory=lambda: [0.1, 0.5, 0.9])
    max_tokens_per_run: int = 15000


class RoutingProbeConfig(BaseProbeConfig):
    """
    Dynamic routing detection via difficulty gap analysis.
    Ref: [2406.18665] RouteLLM.
    """

    name: str = "routing_probe"
    description: str = "Detects routing to cheaper models via difficulty gap."
    easy_prompts: list[str] = Field(
        default_factory=lambda: [
            "What is 25 + 32?",
            "Capital of France?",
        ]
    )
    hard_prompts: list[str] = Field(
        default_factory=lambda: [
            "Solve for x: 3x^2 - 12x + 9 = 0. Show steps.",
            "Explain the difference between epistemological and ontological structural realism.",
        ]
    )
    baseline_gap_threshold: float = 0.3
    max_tokens_per_run: int = 1000


class RepetitionProbeConfig(BaseProbeConfig):
    """
    Phrase looping detection via n-gram analysis.
    Ref: [2403.06408] Perturbation Lens.
    """

    prompt: str = (
        "Write a detailed history of the Roman Empire. Focus on political reforms. "
        "Length: 300 words."
    )
    ngram_size: int = 4
    max_repeats: int = 2
    min_ngram_ttr: float = 0.55
    sliding_window_size: int = 50


class ConstraintProbeConfig(BaseProbeConfig):
    """
    Instruction following under constraints (IFEval style).
    Ref: [2409.11055] Quantization trade-offs.
    """

    type: str = "word_count"
    prompt: str = (
        "Write exactly 100 words about the ocean. Do not write less than 80 or more than 120."
    )
    min_words: int | None = None
    max_words: int | None = None
    forbidden_words: list[str] = Field(default_factory=list)


class LogicPuzzleProbeConfig(BaseProbeConfig):
    """
    GSM8k-style reasoning drift detection.
    Ref: [2504.04823] Q-Hurts-Reasoning.
    """

    puzzle_type: str = "arithmetic"
    prompt: str = (
        "Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. "
        "How many clips did Natalia sell altogether in April and May? Think step by step."
    )
    expected_answer: str = "72"
    required_reasoning: list[str] = Field(default_factory=lambda: ["48 / 2 = 24", "48 + 24"])


class ChainOfThoughtProbeConfig(BaseProbeConfig):
    """
    CoT reliability and error accumulation.
    Ref: [2504.04823].
    """

    prompt: str = "Solve: 15 * 12 + 8 * 9. Think step by step to verify intermediate products."
    min_steps: int = 3
    detect_circular: bool = True


# =============================================================================
# Optional Tier Probes (require logprobs or heavy deps)
# =============================================================================


class CalibrationProbeConfig(BaseProbeConfig):
    """
    Verbalized confidence calibration.
    Ref: [2511.07585].
    Requires: logprobs support.
    """

    prompt: str = (
        "What is the capital of France? Answer format: 'Answer: [City]. Confidence: [0.0-1.0].'"
    )
    expected_answer: str = "Paris"
    min_confidence: float = 0.9
    max_confidence_for_wrong: float = 0.2


class ZeroPrintProbeConfig(BaseProbeConfig):
    """
    Mode collapse detection via distribution entropy.
    Ref: [2407.01235] LLM Fingerprinting.
    Requires: logprobs support.
    """

    prompt: str = (
        "Pick a random animal from this list: Cat, Dog, Bird, Fish, Bear. "
        "Return ONLY the animal name."
    )
    iterations: int = 20
    min_entropy: float = 1.0
    require_logprobs: bool = True


class MultilingualProbeConfig(BaseProbeConfig):
    """
    Asymmetric degradation in non-English languages.
    Ref: [2024.findings-emnlp.935].
    """

    name: str = "multilingual_probe"
    description: str = "Checks for asymmetric degradation in non-English languages."
    languages: list[str] = Field(default_factory=lambda: ["en", "ja", "zh"])
    prompt_template: str = """Translate the following English technical text into {target_language}.
Maintain the exact technical meaning.

Text: "The quantizer minimizes the mean squared error between the original weights and the quantized levels."  # noqa: E501
"""
    max_tokens_per_run: int = 500


# =============================================================================
# Utility Configs
# =============================================================================


class ComparisonProbeConfig(BaseProbeConfig):
    """
    Wrapper that runs a probe against target and reference model.
    """

    reference_model_name: str
    reference_provider_id: str = "openrouter"
    wrapped_probe_config: BaseProbeConfig
    threshold_score_delta: float = 0.1
    threshold_latency_delta_ms: float = 1000.0


class FactProbeConfig(BaseProbeConfig):
    """Simple factual recall probe."""

    prompt: str
    expected_text: str


class TemporalConsistencyConfig(BaseProbeConfig):
    """Knowledge cutoff verification."""

    cutoff_date: date
    strict_event_check: bool = True


class JsonProbeConfig(BaseProbeConfig):
    """
    Validates JSON output structure and schema adherence.
    """

    prompt: str
    schema_definition: dict[str, Any] | None = None
    strict: bool = True


class ConsistencyProbeConfig(BaseProbeConfig):
    """
    Checks semantic consistency across multiple turns or re-asks.
    """

    prompt1: str
    prompt2: str
    consistency_type: str = "permanence"
    expect_match: bool = True

