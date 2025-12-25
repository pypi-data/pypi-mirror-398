"""
CalibrationProbe - Verbalized confidence calibration.

Ref: [2511.07585]
Requires: Simple factual questions with expected high confidence.
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import CalibrationProbeConfig
from nerfprobe_core.scorers.calibration import CalibrationScorer


class CalibrationProbe:
    """
    Detects poor calibration (over/under-confidence).
    Tests if model expresses appropriate confidence for factual questions.
    """

    def __init__(self, config: CalibrationProbeConfig):
        self._config = config
        self._scorer = CalibrationScorer(
            expected_answer=config.expected_answer,
            min_confidence=config.min_confidence,
        )

    @property
    def config(self) -> CalibrationProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=50, output_tokens=50)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        if (
            self.config.max_tokens_per_run > 0
            and self.estimated_cost.total_tokens > self.config.max_tokens_per_run
        ):
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.CALIBRATION,
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
                probe_type=ProbeType.CALIBRATION,
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
            probe_type=ProbeType.CALIBRATION,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response_text,
            metric_scores={"confidence": metrics["confidence"]},
            metadata={
                "research_ref": "[2511.07585]",
                "config": self.config.model_dump(),
                "is_correct": metrics["is_correct"],
            },
        )
