"""
ContextProbe - KV Cache compression detection via depth-placed reasoning.

Ref: [2512.12008] KV Cache Compression
"""

import random
import string
import time
from dataclasses import dataclass

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import ContextProbeConfig


@dataclass
class ReasoningNeedle:
    """A reasoning task embedded in context."""

    premise_1: str
    premise_2: str
    question: str
    expected_answer: str


@dataclass
class ContextScore:
    """Score result for context analysis."""

    value: float
    passed: bool
    reason: str
    depth_results: dict[float, bool]
    middle_failure: bool


class ContextScorer:
    """
    Evaluates reasoning retrieval accuracy at different depths.
    Ref: [2512.12008]
    """

    def score(self, results: dict[float, bool]) -> ContextScore:
        """
        Evaluate depth results for KV cache compression artifacts.

        Args:
            results: Dictionary mapping depth (0.1, 0.5, 0.9) to success
        """
        if not results:
            return ContextScore(
                value=0.0,
                passed=False,
                reason="No results generated",
                depth_results={},
                middle_failure=False,
            )

        passed_count = sum(1 for v in results.values() if v)
        total = len(results)
        acc = passed_count / total

        # Check for compression artifacts: Middle degradation
        start_ok = results.get(0.1, False)
        mid_ok = results.get(0.5, False)
        end_ok = results.get(0.9, False)

        middle_failure = start_ok and end_ok and not mid_ok

        reason_parts = []
        if middle_failure:
            reason_parts.append("KV Cache Compression detected (Middle failure).")
        if acc < 0.6:
            reason_parts.append("General Context Failure.")

        reason = " ".join(reason_parts) if reason_parts else "Context Integrity OK."

        return ContextScore(
            value=acc,
            passed=acc >= 0.9 and not middle_failure,
            reason=reason,
            depth_results=results,
            middle_failure=middle_failure,
        )


class ContextProbe:
    """
    Tests for KV cache compression artifacts by placing reasoning premises
    at specific depths within a long context.
    """

    def __init__(self, config: ContextProbeConfig):
        self._config = config
        self._scorer = ContextScorer()

    @property
    def config(self) -> ContextProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        input_tokens = len(self._config.needle_depths) * self._config.context_length
        output_tokens = len(self._config.needle_depths) * 10
        return CostEstimate(input_tokens=input_tokens, output_tokens=output_tokens)

    def _generate_haystack(self, length: int) -> list[str]:
        """Generate filler text tokens."""
        filler = (
            "The quick brown fox jumps over the lazy dog. "
            "Pack my box with five dozen liquor jugs. "
            "How vexingly quick daft zebras jump. "
        ) * 100
        words = filler.split()
        while len(words) < length:
            words += words
        return words[:length]

    def _create_needle(self) -> ReasoningNeedle:
        """Create a unique reasoning task to prevent training data contamination."""
        obj = "".join(random.choices(string.ascii_uppercase, k=3))
        prop = "".join(random.choices(string.ascii_lowercase, k=4))

        return ReasoningNeedle(
            premise_1=f"Ref-X{obj} is composed of {prop}.",
            premise_2=f"Materials composed of {prop} are magnetic.",
            question=f"Is Ref-X{obj} magnetic? Answer Yes or No.",
            expected_answer="Yes",
        )

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start = time.perf_counter()

        if self.estimated_cost.total_tokens > self._config.max_tokens_per_run:
            return ProbeResult(
                probe_name=self._config.name,
                probe_type=ProbeType.CONTEXT,
                target=target,
                score=0.0,
                passed=False,
                latency_ms=0.0,
                raw_response="SKIPPED: Cost Exceeds Budget",
                metadata={"status": "SKIPPED", "cost": self.estimated_cost.total_tokens},
            )

        filler_tokens = self._generate_haystack(self._config.context_length)
        total_tokens = len(filler_tokens)

        results: dict[float, bool] = {}

        for depth in self._config.needle_depths:
            needle = self._create_needle()

            # Insert needle at depth
            insert_idx = int(total_tokens * depth)

            context_tokens = (
                filler_tokens[:insert_idx]
                + [needle.premise_1, needle.premise_2]
                + filler_tokens[insert_idx:]
            )

            prompt = f"""Context:
{" ".join(context_tokens)}

Question: {needle.question}
Answer:"""

            try:
                response = await generator.generate(target, prompt)
                passed = needle.expected_answer.lower() in response.lower()
                results[depth] = passed
            except Exception:
                results[depth] = False

        latency_ms = (time.perf_counter() - start) * 1000
        score = self._scorer.score(results)

        return ProbeResult(
            probe_name=self._config.name,
            probe_type=ProbeType.CONTEXT,
            target=target,
            score=score.value,
            passed=score.passed,
            latency_ms=latency_ms,
            raw_response="ContextProbe Execution",
            metric_scores={f"depth_{k}": 1.0 if v else 0.0 for k, v in results.items()},
            metadata={
                "research_ref": "[2512.12008]",
                "depth_results": score.depth_results,
                "middle_failure": score.middle_failure,
                "reason": score.reason,
            },
        )
