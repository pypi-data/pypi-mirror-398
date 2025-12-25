"""Scorer and Probe protocols."""

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from nerfprobe_core.core.entities import ModelTarget, ProbeResult
from nerfprobe_core.core.gateway import LLMGateway


class CostEstimate(BaseModel):
    """Estimated cost for a probe execution."""

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@runtime_checkable
class ScorerProtocol(Protocol):
    """
    Pure logic component that evaluates a parsed response.
    Has no side effects and no LLM usage.
    """

    def score(self, response: Any) -> float:
        """Return a normalized score (0.0 - 1.0)."""
        ...

    def metrics(self, response: Any) -> dict[str, Any]:
        """Return detailed metrics (e.g., {'ttr': 0.65})."""
        ...


@runtime_checkable
class ProbeProtocol(Protocol):
    """
    The interface all probes must satisfy.
    Composes Generator -> Parser -> Scorer.
    """

    @property
    def config(self) -> BaseModel:
        """Probe configuration."""
        ...

    @property
    def estimated_cost(self) -> CostEstimate:
        """Estimated token cost for budgeting."""
        ...

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        """Execute the probe and return results."""
        ...
