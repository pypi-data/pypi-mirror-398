"""Core domain entities for probe results and model targets."""

import datetime
import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProviderType(str, enum.Enum):
    """Known provider types for categorization."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    AWS = "aws"
    ALIBABA = "alibaba"
    BAIDU = "baidu"
    ZHIPU = "zhipu"


class ProbeType(str, enum.Enum):
    """Categorization of probe types for analysis."""

    MATH = "math"
    INSTRUCTION = "instruction"
    TIMING = "timing"
    STYLE = "style"
    HALLUCINATION = "hallucination"
    COMPARISON = "comparison"
    CODE = "code"
    REPETITION = "repetition"
    ZEROPRINT = "zeroprint"
    CONSTRAINT = "constraint"
    REASONING = "reasoning"
    FINGERPRINT = "fingerprint"
    CONTEXT = "context"
    ROUTING = "routing"
    CALIBRATION = "calibration"
    MULTILINGUAL = "multilingual"


class LogprobToken(BaseModel):
    """Token with probability information for paper-exact metrics."""

    token: str
    logprob: float  # Natural log probability
    top_logprobs: dict[str, float] | None = None  # Top-k alternatives


class LogprobResult(BaseModel):
    """Response with logprob data for KL-divergence, entropy calculations."""

    text: str
    tokens: list[LogprobToken] = Field(default_factory=list)

    @property
    def mean_logprob(self) -> float:
        """Average log probability across tokens."""
        if not self.tokens:
            return 0.0
        return sum(t.logprob for t in self.tokens) / len(self.tokens)


class ModelTarget(BaseModel):
    """Identifies a specific model to test."""

    provider_id: str
    model_name: str  # The API string (e.g., "claude-3-opus-20240229")
    cost_per_m_in: float = 0.0
    cost_per_m_out: float = 0.0

    model_config = ConfigDict(frozen=True)

    def __str__(self) -> str:
        return f"{self.provider_id}/{self.model_name}"


class ProbeResult(BaseModel):
    """The outcome of a single probe execution."""

    probe_name: str
    probe_type: ProbeType
    target: ModelTarget
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

    score: float = Field(ge=0.0, le=1.0)  # Normalized 0.0-1.0
    passed: bool

    # Timing metrics (critical for fingerprinting)
    latency_ms: float
    ttft_ms: float | None = None
    mean_itl_ms: float | None = None

    # Advanced metrics (PPL, TTR, etc)
    metric_scores: dict[str, float] = Field(default_factory=dict)

    # Raw data for deeper analysis
    raw_response: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    def summary(self) -> str:
        """Compact one-line summary for CLI output."""
        status = "PASS" if self.passed else "FAIL"
        return f"{self.probe_name}: {status} ({self.score:.2f}) in {self.latency_ms:.0f}ms"
