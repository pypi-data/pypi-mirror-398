"""
CodeProbe - Syntax collapse detection via AST validation.

Ref: [2512.08213] Package Hallucinations.
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import CodeProbeConfig
from nerfprobe_core.scorers.code import CodeScorer


class CodeProbe:
    """
    Verifies syntactic correctness of generated code.
    Uses Python's AST parser for strict validation.
    """

    def __init__(self, config: CodeProbeConfig):
        self._config = config
        self._scorer = CodeScorer()

    @property
    def config(self) -> CodeProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=100, output_tokens=300)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start = time.perf_counter()
        response_text = ""

        try:
            response_text = await generator.generate(target, self.config.prompt)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.CODE,
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

        # Unpack metrics
        metric_scores = {
            k: v
            for k, v in metrics.items()
            if not k.startswith("_") and isinstance(v, (int, float))
        }

        # Collect non-numeric metrics for metadata
        extra_meta = {
            k: v
            for k, v in metrics.items()
            if not k.startswith("_") and not isinstance(v, (int, float))
        }
        scorer_meta = metrics.get("_metadata", {})

        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.CODE,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response_text,
            metric_scores=metric_scores,
            metadata={
                "research_ref": "[2512.08213]",
                "config": self.config.model_dump(),
                "scorer_details": scorer_meta,
                **extra_meta,
            },
        )
