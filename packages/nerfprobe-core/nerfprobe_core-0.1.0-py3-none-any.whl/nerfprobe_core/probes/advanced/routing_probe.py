"""
RoutingProbe - Dynamic routing detection via difficulty gap analysis.

Ref: [2406.18665] RouteLLM
"""

import time
from dataclasses import dataclass

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import RoutingProbeConfig


@dataclass
class RoutingScore:
    """Score result for routing analysis."""

    value: float
    passed: bool
    reason: str
    easy_accuracy: float
    hard_accuracy: float
    complexity_gap: float


class RoutingScorer:
    """
    Analyzes performance gap between Easy and Hard tasks.
    Ref: [2406.18665] RouteLLM
    """

    def score(
        self, easy_results: list[bool], hard_results: list[bool], threshold: float
    ) -> RoutingScore:
        """
        Evaluate performance gap between easy and hard tasks.
        Large gap suggests routing to weaker models on complex tasks.
        """
        if not easy_results or not hard_results:
            return RoutingScore(
                value=1.0,
                passed=False,
                reason="Insufficient Data",
                easy_accuracy=0.0,
                hard_accuracy=0.0,
                complexity_gap=1.0,
            )

        easy_acc = sum(easy_results) / len(easy_results)
        hard_acc = sum(hard_results) / len(hard_results)

        # Gap: how much harder tasks perform worse
        gap = easy_acc - hard_acc

        # Passed if gap is below threshold
        passed = gap < threshold

        return RoutingScore(
            value=gap,  # Lower is better (smaller gap)
            passed=passed,
            reason=f"Easy Acc: {easy_acc:.2f}, Hard Acc: {hard_acc:.2f}, Gap: {gap:.2f}",
            easy_accuracy=easy_acc,
            hard_accuracy=hard_acc,
            complexity_gap=gap,
        )


class RoutingProbe:
    """
    Detects dynamic routing by comparing performance on Easy vs Hard tasks.
    Large performance gaps suggest cheaper/weaker models for complex queries.
    """

    def __init__(self, config: RoutingProbeConfig):
        self._config = config
        self._scorer = RoutingScorer()

    @property
    def config(self) -> RoutingProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        num_prompts = len(self._config.easy_prompts) + len(self._config.hard_prompts)
        return CostEstimate(input_tokens=num_prompts * 50, output_tokens=num_prompts * 50)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start = time.perf_counter()

        if self.estimated_cost.total_tokens > self._config.max_tokens_per_run:
            return ProbeResult(
                probe_name=self._config.name,
                probe_type=ProbeType.ROUTING,
                target=target,
                score=0.0,
                passed=False,
                latency_ms=0.0,
                raw_response="SKIPPED: Cost Exceeds Budget",
                metadata={"status": "SKIPPED", "cost": self.estimated_cost.total_tokens},
            )

        # Run Easy Tasks
        easy_results: list[bool] = []
        for prompt in self._config.easy_prompts:
            try:
                response = await generator.generate(target, prompt)
                is_correct = self._evaluate_easy(prompt, response)
                easy_results.append(is_correct)
            except Exception:
                easy_results.append(False)

        # Run Hard Tasks
        hard_results: list[bool] = []
        for prompt in self._config.hard_prompts:
            try:
                response = await generator.generate(target, prompt)
                is_correct = self._evaluate_hard(prompt, response)
                hard_results.append(is_correct)
            except Exception:
                hard_results.append(False)

        latency_ms = (time.perf_counter() - start) * 1000
        score = self._scorer.score(easy_results, hard_results, self._config.baseline_gap_threshold)

        return ProbeResult(
            probe_name=self._config.name,
            probe_type=ProbeType.ROUTING,
            target=target,
            score=score.value,
            passed=score.passed,
            latency_ms=latency_ms,
            raw_response=str(easy_results + hard_results),
            metric_scores={
                "easy_accuracy": score.easy_accuracy,
                "hard_accuracy": score.hard_accuracy,
                "complexity_gap": score.complexity_gap,
            },
            metadata={
                "research_ref": "[2406.18665]",
                "reason": score.reason,
                "easy_results": easy_results,
                "hard_results": hard_results,
            },
        )

    def _evaluate_easy(self, prompt: str, response: str) -> bool:
        """Evaluate easy task correctness."""
        if "25 + 32" in prompt or "25+32" in prompt:
            return "57" in response
        if "France" in prompt:
            return "Paris" in response.lower() or "paris" in response.lower()
        return True  # Default if unknown prompt

    def _evaluate_hard(self, prompt: str, response: str) -> bool:
        """Evaluate hard task correctness."""
        if "Solve for x" in prompt:
            # Quadratic 3x^2 - 12x + 9 = 0 has roots x=1, x=3
            normalized = response.replace(" ", "").lower()
            return "x=1" in normalized or "x=3" in normalized
        if "ontological" in prompt:
            # Expect detailed explanation (>50 words)
            return len(response.split()) > 50
        return False
