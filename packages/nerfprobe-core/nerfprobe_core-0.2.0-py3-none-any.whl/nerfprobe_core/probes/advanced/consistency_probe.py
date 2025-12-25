from typing import Any
import time

from nerfprobe_core.core.entities import ModelTarget, ProbeResult, ProbeType
from nerfprobe_core.core.scorer import ProbeProtocol, CostEstimate
from nerfprobe_core.core.gateway import LLMGateway
from nerfprobe_core.probes.config import ConsistencyProbeConfig
from nerfprobe_core.scorers.consistency_scorer import ConsistencyScorer

class ConsistencyProbe(ProbeProtocol):
    """
    Detects self-contradiction or lack of fact permanence using ConsistencyScorer.
    Formerly ContradictionProbe.
    """
    
    def __init__(self, config: ConsistencyProbeConfig):
        self._config = config
        self._scorer = ConsistencyScorer(
            consistency_type=config.consistency_type,
            expect_match=config.expect_match
        )

    @property
    def config(self) -> ConsistencyProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=100, output_tokens=100) # 2 turns

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        # Enforce Token Budget
        if self.config.max_tokens_per_run > 0 and self.estimated_cost.total_tokens > self.config.max_tokens_per_run:
             return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.HALLUCINATION,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=0.0,
                raw_response="SKIPPED: Exceeds token budget",
                metadata={"error": "Token budget exceeded"}
            )
        start = time.perf_counter()
        
        try:
            # Turn 1
            resp1 = await generator.generate(target, self.config.prompt1)
            
            # Turn 2
            resp2 = await generator.generate(target, self.config.prompt2)
            
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

        responses = [resp1, resp2]
        score = self._scorer.score(responses)
        metrics = self._scorer.metrics(responses)
        passed = score == 1.0
        
        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.HALLUCINATION,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=f"A1: {resp1} | A2: {resp2}",
            metric_scores={
                "similarity": metrics["similarity"]
            },
            metadata={
                "research_ref": "[2504.04823]",
                "config": self.config.model_dump(),
                "answer1": metrics["answer1"],
                "answer2": metrics["answer2"]
            }
        )
