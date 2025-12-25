"""
ZeroPrintProbe - Mode collapse detection via distribution entropy.

Ref: [2407.01235] LLM Fingerprinting
Requires: Multiple sampling iterations.
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import ZeroPrintProbeConfig
from nerfprobe_core.scorers.entropy import EntropyScorer


class ZeroPrintProbe:
    """
    Detects mode collapse (low entropy) by sampling multiple responses.
    Healthy models should produce diverse outputs for stochastic prompts.
    """

    def __init__(self, config: ZeroPrintProbeConfig):
        self._config = config
        self._scorer = EntropyScorer()

    @property
    def config(self) -> ZeroPrintProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(
            input_tokens=20 * self.config.iterations,
            output_tokens=10 * self.config.iterations,
        )

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start_global = time.perf_counter()
        responses: list[str] = []

        # Iterative Generation
        for _ in range(self.config.iterations):
            try:
                # Try logprobs if required and supported
                if getattr(self.config, "require_logprobs", False) and hasattr(
                    generator, "generate_with_logprobs"
                ):
                    result = await generator.generate_with_logprobs(target, self.config.prompt)
                    resp = result.text
                else:
                    resp = await generator.generate(target, self.config.prompt)
                responses.append(resp)
            except NotImplementedError:
                # Fallback if gateway doesn't support logprobs
                try:
                    resp = await generator.generate(target, self.config.prompt)
                    responses.append(resp)
                except Exception as e:
                    responses.append(f"ERROR: {e!s}")
            except Exception as e:
                responses.append(f"ERROR: {e!s}")

        latency_ms = (time.perf_counter() - start_global) * 1000

        # Score Entropy
        entropy = self._scorer.score(responses)
        metrics = self._scorer.metrics(responses)

        passed = entropy >= self.config.min_entropy

        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.ZEROPRINT,
            target=target,
            passed=passed,
            score=1.0 if passed else 0.0,
            latency_ms=latency_ms,
            raw_response=f"Sampled {len(responses)} times. Top: {list(responses)[:3]}...",
            metric_scores={
                "entropy": entropy,
                "unique_count": float(metrics["unique_count"]),
            },
            metadata={
                "research_ref": "[2407.01235]",
                "config": self.config.model_dump(),
                "distribution": metrics["_metadata"].get("distribution", {}),
            },
        )
