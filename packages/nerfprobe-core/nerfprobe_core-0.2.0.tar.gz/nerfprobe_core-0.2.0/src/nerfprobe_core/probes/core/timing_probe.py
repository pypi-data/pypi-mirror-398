"""
TimingProbe - Latency fingerprinting via TTFT and ITL.

Ref: [2502.20589] LLMs Have Rhythm.
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
from nerfprobe_core.probes.config import TimingProbeConfig


@dataclass
class TimingStats:
    """Timing analysis results."""

    ttft_ms: float
    mean_itl_ms: float
    chunk_count: int


class TimingAnalyzer:
    """Pure timing analysis logic."""

    @staticmethod
    def analyze(ttft: float, chunk_times: list[float]) -> TimingStats:
        """Compute timing statistics from raw measurements."""
        mean_itl = sum(chunk_times) / len(chunk_times) if chunk_times else 0.0
        return TimingStats(
            ttft_ms=ttft,
            mean_itl_ms=mean_itl,
            chunk_count=len(chunk_times),
        )


class TimingProbe:
    """
    Measures TTFT and ITL for fingerprinting and speedup detection.
    Uses streaming to capture accurate timing measurements.
    """

    def __init__(self, config: TimingProbeConfig):
        self._config = config

    @property
    def config(self) -> TimingProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        return CostEstimate(input_tokens=10, output_tokens=self.config.token_count)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        start_time = time.perf_counter()
        chunk_times: list[float] = []
        full_response: list[str] = []

        prompt = f"Count from 1 to {self.config.token_count} in words, one per line."

        try:
            ttft_start = start_time
            ttft = 0.0
            last_chunk_time = 0.0

            async for chunk in generator.generate_stream(target, prompt):
                now = time.perf_counter()

                if not full_response:
                    # First token received
                    ttft = (now - ttft_start) * 1000
                    last_chunk_time = now
                else:
                    # Subsequent tokens
                    delta = (now - last_chunk_time) * 1000
                    chunk_times.append(delta)
                    last_chunk_time = now

                full_response.append(chunk)

            response_text = "".join(full_response)
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            # Calculate Timing Stats
            timing_stats = TimingAnalyzer.analyze(ttft, chunk_times)

            passed = bool(response_text.strip()) and latency_ms > 0

            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.TIMING,
                target=target,
                passed=passed,
                score=1.0 if passed else 0.0,
                latency_ms=latency_ms,
                raw_response=response_text,
                ttft_ms=timing_stats.ttft_ms,
                mean_itl_ms=timing_stats.mean_itl_ms,
                metric_scores={},
                metadata={
                    "research_ref": "[2502.20589]",
                    "config": self.config.model_dump(),
                    "chunk_count": timing_stats.chunk_count,
                },
            )

        except Exception as e:
            end_time = time.perf_counter()
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.TIMING,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=(end_time - start_time) * 1000,
                raw_response=f"ERROR: {e!s}",
                metadata={"error": str(e)},
            )
