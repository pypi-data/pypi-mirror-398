"""Gateway protocols for LLM communication."""

from collections.abc import AsyncIterator
from typing import Protocol

from nerfprobe_core.core.entities import LogprobResult, ModelTarget


class LLMGateway(Protocol):
    """
    Port for communicating with LLM providers.
    Implementations will adapt OpenAI, Anthropic, etc.
    """

    async def generate(self, model: ModelTarget, prompt: str) -> str:
        """Simple completion."""
        ...

    def generate_stream(self, model: ModelTarget, prompt: str) -> AsyncIterator[str]:
        """Streaming completion for timing analysis."""
        ...

    async def generate_with_logprobs(
        self,
        model: ModelTarget,
        prompt: str,
        top_logprobs: int = 5,
    ) -> LogprobResult:
        """
        Completion with token-level log probabilities.
        Required for paper-exact metrics: KL-divergence, entropy.

        Ref: [2407.01235] ZeroPrint, [2511.07585] Calibration

        Raises NotImplementedError if provider doesn't support logprobs.
        """
        ...
