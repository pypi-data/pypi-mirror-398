from typing import Any
import time

from nerfprobe_core.core.entities import ModelTarget, ProbeResult, ProbeType
from nerfprobe_core.core.scorer import ProbeProtocol, CostEstimate
from nerfprobe_core.core.gateway import LLMGateway
from nerfprobe_core.probes.config import FactProbeConfig
from nerfprobe_core.scorers.fact_scorer import FactScorer

class FactProbe(ProbeProtocol):
    """
    Checks if model expected fact is in the output.
    """
    
    def __init__(self, config: FactProbeConfig):
        self._config = config
        self._scorer = FactScorer(expected_text=config.expected_text)

    @property
    def config(self) -> FactProbeConfig:
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
                probe_type=ProbeType.HALLUCINATION,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=(time.perf_counter() - start) * 1000,
                raw_response=f"ERROR: {str(e)}",
                metadata={"error": str(e)}
            )

        score = self._scorer.score(response_text)
        metrics = self._scorer.metrics(response_text)
        passed = score == 1.0

        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.HALLUCINATION,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response_text,
            metric_scores={"passed": 1.0 if passed else 0.0},
            metadata={
                "research_ref": "[2512.08213]",
                "config": self.config.model_dump(),
                "scorer_details": metrics
            }
        )
