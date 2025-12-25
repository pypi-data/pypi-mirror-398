"""
ConstraintProbe - Strict constraint adherence checking (IFEval style).

Ref: [2409.11055] Quantization trade-offs
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import ConstraintProbeConfig
from nerfprobe_core.scorers.constraint import ConstraintScorer


class ConstraintProbe:
    """
    Detects failures in strict constraint adherence.
    Tests word counts, forbidden words, etc.
    """

    def __init__(self, config: ConstraintProbeConfig):
        self._config = config
        self._scorer = ConstraintScorer(
            constraint_type=config.type,
            min_words=config.min_words,
            max_words=config.max_words,
            forbidden_words=config.forbidden_words,
        )

    @property
    def config(self) -> ConstraintProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=50, output_tokens=150)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        if (
            self.config.max_tokens_per_run > 0
            and self.estimated_cost.total_tokens > self.config.max_tokens_per_run
        ):
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.CONSTRAINT,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=0.0,
                raw_response="SKIPPED: Exceeds token budget",
                metadata={"error": "Token budget exceeded"},
            )

        start = time.perf_counter()
        response_text = ""

        try:
            response_text = await generator.generate(target, self.config.prompt)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.CONSTRAINT,
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
            probe_type=ProbeType.CONSTRAINT,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response_text,
            metric_scores={
                "word_count": float(metrics["word_count"]),
                "violations_count": float(metrics.get("violations_count", 0)),
            },
            metadata={
                "research_ref": "[2409.11055]",
                "config": self.config.model_dump(),
                "violations": metrics.get("violations", []),
            },
        )
