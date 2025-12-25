"""
MathProbe - Arithmetic reasoning degradation detection.

Ref: [2504.04823] Quantization Hurts Reasoning.
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import MathProbeConfig
from nerfprobe_core.scorers.math import MathScorer


class MathProbe:
    """
    Checks if model produces correct arithmetic answer.
    Simple but effective for detecting precision loss.
    """

    def __init__(self, config: MathProbeConfig):
        self._config = config
        self._scorer = MathScorer(expected_answer=config.expected_answer)

    @property
    def config(self) -> MathProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=50, output_tokens=50)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start = time.perf_counter()
        response_text = ""

        try:
            response_text = await generator.generate(target, self.config.prompt)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.MATH,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=(time.perf_counter() - start) * 1000,
                raw_response=f"ERROR: {e!s}",
                metadata={"error": str(e)},
            )

        score = self._scorer.score(response_text)
        metrics = self._scorer.metrics(response_text)
        passed = score == 1.0

        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.MATH,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response_text,
            metric_scores={"passed": 1.0 if passed else 0.0},
            metadata={
                "research_ref": "[2504.04823]",
                "config": self.config.model_dump(),
                "scorer_details": metrics,
            },
        )
