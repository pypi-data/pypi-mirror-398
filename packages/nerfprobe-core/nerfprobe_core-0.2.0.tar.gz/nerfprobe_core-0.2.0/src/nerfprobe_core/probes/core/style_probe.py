"""
StyleProbe - Vocabulary degradation (lobotomy) detection via TTR.

Ref: [2403.06408] Perturbation Lens.
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import StyleProbeConfig
from nerfprobe_core.scorers.ttr import TTRScorer


class StyleProbe:
    """
    Detects vocabulary degradation using Type-Token Ratio.
    Low TTR indicates repetitive, "lobotomized" output.
    """

    def __init__(self, config: StyleProbeConfig):
        self._config = config
        self._scorer = TTRScorer(sliding_window_size=config.sliding_window_size)

    @property
    def config(self) -> StyleProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=50, output_tokens=500)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        # Enforce Token Budget
        if (
            self.config.max_tokens_per_run > 0
            and self.estimated_cost.total_tokens > self.config.max_tokens_per_run
        ):
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.STYLE,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=0.0,
                raw_response="SKIPPED: Exceeds token budget",
                metadata={"error": "Token budget exceeded"},
            )

        # Generation Phase
        prompt = self.config.prompt_template.format(topic=self.config.topic)
        start = time.perf_counter()

        try:
            response = await generator.generate(target, prompt)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.STYLE,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=(time.perf_counter() - start) * 1000,
                raw_response=f"ERROR: {e!s}",
                metadata={"error": str(e)},
            )

        # Scoring Phase
        score = self._scorer.score(response)
        metrics = self._scorer.metrics(response)
        passed = metrics.get("min_local_ttr", score) >= self.config.min_ttr

        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.STYLE,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response,
            metric_scores=metrics,
            metadata={
                "research_ref": "[2403.06408]",
                "threshold_baseline": "0.65-0.70",
                "threshold_alert": f"<{self.config.min_ttr}",
                "config": self.config.model_dump(),
            },
        )
