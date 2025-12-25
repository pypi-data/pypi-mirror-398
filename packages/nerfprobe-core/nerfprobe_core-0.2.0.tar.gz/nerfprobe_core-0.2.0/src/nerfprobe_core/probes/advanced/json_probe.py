from typing import Any
import time

from nerfprobe_core.core.entities import ModelTarget, ProbeResult, ProbeType
from nerfprobe_core.core.scorer import ProbeProtocol, CostEstimate
from nerfprobe_core.core.gateway import LLMGateway
from nerfprobe_core.probes.config import JsonProbeConfig
from nerfprobe_core.scorers.json_scorer import JsonScorer

class JsonProbe(ProbeProtocol):
    """
    Validates compliance with JSON schema constraints.
    Formerly InstructionProbe.
    """
    
    def __init__(self, config: JsonProbeConfig):
        self._config = config
        self._scorer = JsonScorer(
            schema=config.schema_definition, 
            strict=config.strict
        )

    @property
    def config(self) -> JsonProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=100, output_tokens=300)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start = time.perf_counter()
        
        try:
            response = await generator.generate(target, self.config.prompt)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.INSTRUCTION,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=(time.perf_counter() - start) * 1000,
                raw_response=f"ERROR: {str(e)}",
                metadata={"error": str(e)}
            )

        # Scoring Phase
        score = self._scorer.score(response)
        raw_metrics = self._scorer.metrics(response)
        
        # Split into numeric metrics and metadata
        metric_scores = {k: v for k, v in raw_metrics.items() if not k.startswith("_")}
        scorer_metadata = raw_metrics.get("_metadata", {})
        
        passed = score == 1.0
        
        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.INSTRUCTION,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=response,
            metric_scores=metric_scores,
            metadata={
                "research_ref": "[2402.16775]",
                "strict_mode": self.config.strict,
                "extraction_used": metric_scores.get("extraction_used", 0.0) == 1.0,
                "config": self.config.model_dump(),
                "scorer_details": scorer_metadata
            }
        )
