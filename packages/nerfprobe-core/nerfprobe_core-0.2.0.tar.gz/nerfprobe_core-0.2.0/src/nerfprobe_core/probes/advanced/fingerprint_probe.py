"""
FingerprintProbe - Framework/model fingerprinting via error templates.

Ref: [2407.15847] LLMmap
"""

import time
from dataclasses import dataclass

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import FingerprintProbeConfig


@dataclass
class FingerprintScore:
    """Score result for fingerprint analysis."""

    value: float
    passed: bool
    reason: str
    detected_frameworks: list[str]
    malformed_robustness: float
    identity_privacy: float


class FingerprintScorer:
    """
    Analyzes responses to malformed queries and identity prompts.
    Ref: [2407.15847] LLMmap
    """

    # Known error patterns from specific frameworks/models
    ERROR_SIGNATURES: dict[str, list[str]] = {
        "vllm": ["vLLM", "PagedAttention", "AsyncLLMEngine"],
        "tgi": ["Text Generation Inference", "shard", "warmup"],
        "llama_cpp": ["llama_print_timings", "ggml", "llama.cpp"],
        "triton": ["Triton", "ensemble", "model_repository"],
        "openai_refusal": ["I am sorry", "As an AI language model", "I cannot"],
        "anthropic_refusal": ["I apologize", "I'm Claude", "I don't feel"],
        "generic_error": ["syntax error", "malformed input", "unexpected token"],
    }

    def score(
        self, malformed_responses: list[str], banner_responses: list[str]
    ) -> FingerprintScore:
        """
        Evaluates vulnerability to fingerprinting.
        Lower score = Higher vulnerability (easier to fingerprint).
        """
        # Check Malformed Query Handling
        malformed_errors = 0
        detected_frameworks: set[str] = set()

        for resp in malformed_responses:
            for fw, sigs in self.ERROR_SIGNATURES.items():
                if any(sig.lower() in resp.lower() for sig in sigs):
                    detected_frameworks.add(fw)
                    malformed_errors += 1

        # Check Identity Leaks
        identity_leaked = 0
        for resp in banner_responses:
            # Heuristic: mentions specific version numbers or internal names
            if any(char.isdigit() for char in resp) and "model" in resp.lower():
                identity_leaked += 1

        # Calculate Scores (1.0 = robust, 0.0 = exposed)
        malformed_score = (
            1.0 - (float(malformed_errors) / len(malformed_responses))
            if malformed_responses
            else 1.0
        )
        identity_score = (
            1.0 - (float(identity_leaked) / len(banner_responses)) if banner_responses else 1.0
        )

        combined_score = (malformed_score + identity_score) / 2.0
        passed = combined_score > 0.8

        return FingerprintScore(
            value=combined_score,
            passed=passed,
            reason=(
                f"Frameworks Detected: {list(detected_frameworks)}, "
                f"Identity Leaks: {identity_leaked}/{len(banner_responses)}"
            ),
            detected_frameworks=list(detected_frameworks),
            malformed_robustness=malformed_score,
            identity_privacy=identity_score,
        )


class FingerprintProbe:
    """
    Identifies model/framework via unique error templates and identity prompts.
    Uses malformed queries to trigger framework-specific error messages.
    """

    def __init__(self, config: FingerprintProbeConfig):
        self._config = config
        self._scorer = FingerprintScorer()

    @property
    def config(self) -> FingerprintProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        queries = len(self._config.malformed_queries) + len(self._config.banner_prompts)
        return CostEstimate(input_tokens=queries * 30, output_tokens=queries * 50)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start = time.perf_counter()

        if self.estimated_cost.total_tokens > self._config.max_tokens_per_run:
            return ProbeResult(
                probe_name=self._config.name,
                probe_type=ProbeType.FINGERPRINT,
                target=target,
                score=0.0,
                passed=False,
                latency_ms=0.0,
                raw_response="SKIPPED: Cost Exceeds Budget",
                metadata={"status": "SKIPPED", "cost": self.estimated_cost.total_tokens},
            )

        malformed_responses: list[str] = []
        for query in self._config.malformed_queries:
            try:
                res = await generator.generate(target, query)
                malformed_responses.append(res)
            except Exception as e:
                # Gateway crash is also a fingerprint
                malformed_responses.append(f"GATEWAY_CRASH: {e!s}")

        banner_responses: list[str] = []
        for prompt in self._config.banner_prompts:
            try:
                res = await generator.generate(target, prompt)
                banner_responses.append(res)
            except Exception as e:
                banner_responses.append(f"ERROR: {e!s}")

        latency_ms = (time.perf_counter() - start) * 1000
        score = self._scorer.score(malformed_responses, banner_responses)

        return ProbeResult(
            probe_name=self._config.name,
            probe_type=ProbeType.FINGERPRINT,
            target=target,
            score=score.value,
            passed=score.passed,
            latency_ms=latency_ms,
            raw_response=str(malformed_responses + banner_responses),
            metric_scores={
                "malformed_robustness": score.malformed_robustness,
                "identity_privacy": score.identity_privacy,
            },
            metadata={
                "research_ref": "[2407.15847]",
                "detected_frameworks": score.detected_frameworks,
                "reason": score.reason,
                "malformed_responses": malformed_responses,
                "banner_responses": banner_responses,
            },
        )
