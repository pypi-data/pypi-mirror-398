"""
RepetitionProbe - Phrase looping detection via N-gram analysis.

Ref: [2403.06408] Perturbation Lens
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import RepetitionProbeConfig
from nerfprobe_core.scorers.repetition import RepetitionScorer


class RepetitionProbe:
    """
    Detects quantization-induced phrase looping.
    Uses N-gram analysis to find repetitive patterns.
    """

    def __init__(self, config: RepetitionProbeConfig):
        self._config = config
        self._scorer = RepetitionScorer(
            ngram_size=config.ngram_size,
            max_repeats=config.max_repeats,
            sliding_window_size=config.sliding_window_size,
        )

    @property
    def config(self) -> RepetitionProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=50, output_tokens=200)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start = time.perf_counter()
        response_text = ""

        try:
            response_text = await generator.generate(target, self.config.prompt)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.REPETITION,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=(time.perf_counter() - start) * 1000,
                raw_response=f"ERROR: {e!s}",
                metadata={"error": str(e)},
            )

        metrics = self._scorer.metrics(response_text)

        # Pass conditions:
        # 1. No excessive loops (max_repeats <= config.max_repeats)
        # 2. Local TTR above threshold (min_local_ttr >= config.min_ngram_ttr)
        min_local_ttr = metrics.get("min_local_ttr", 1.0)
        max_repeats = int(metrics.get("max_repeats", 0))

        passed = (max_repeats <= self.config.max_repeats) and (
            min_local_ttr >= self.config.min_ngram_ttr
        )
        score = 1.0 if passed else 0.0

        # Extract numeric metrics for metric_scores
        metric_scores = {
            k: v
            for k, v in metrics.items()
            if not k.startswith("_") and isinstance(v, (int, float))
        }

        # Non-numeric for metadata
        extra_meta = {
            k: v
            for k, v in metrics.items()
            if not k.startswith("_") and not isinstance(v, (int, float))
        }
        scorer_meta = metrics.get("_metadata", {})

        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.REPETITION,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response_text,
            metric_scores=metric_scores,
            metadata={
                "research_ref": "[2403.06408]",
                "config": self.config.model_dump(),
                "scorer_details": scorer_meta,
                **extra_meta,
            },
        )
