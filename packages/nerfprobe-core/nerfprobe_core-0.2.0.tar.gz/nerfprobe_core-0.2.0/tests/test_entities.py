"""Unit tests for core entities."""

import pytest
from nerfprobe_core.core.entities import (
    ProbeResult,
    ModelTarget,
    ProbeType,
    LogprobToken,
    LogprobResult,
    ProviderType,
)


class TestModelTarget:
    def test_basic_creation(self):
        target = ModelTarget(provider_id="openai", model_name="gpt-4o")
        assert target.provider_id == "openai"
        assert target.model_name == "gpt-4o"

    def test_with_cost_fields(self):
        target = ModelTarget(
            provider_id="anthropic",
            model_name="claude-3-opus",
            cost_per_m_in=15.0,
            cost_per_m_out=75.0,
        )
        assert target.cost_per_m_in == 15.0
        assert target.cost_per_m_out == 75.0

    def test_str_representation(self):
        target = ModelTarget(provider_id="openai", model_name="gpt-4")
        assert str(target) == "openai/gpt-4"


class TestProbeResult:
    def test_basic_creation(self):
        target = ModelTarget(provider_id="openai", model_name="gpt-4")
        result = ProbeResult(
            probe_name="test_probe",
            probe_type=ProbeType.MATH,
            target=target,
            passed=True,
            score=1.0,
            latency_ms=150.0,
            raw_response="The answer is 42.",
        )
        assert result.passed is True
        assert result.score == 1.0

    def test_summary_method(self):
        target = ModelTarget(provider_id="openai", model_name="gpt-4")
        result = ProbeResult(
            probe_name="math_probe",
            probe_type=ProbeType.MATH,
            target=target,
            passed=True,
            score=1.0,
            latency_ms=123.4,
            raw_response="test",
        )
        summary = result.summary()
        assert "PASS" in summary
        assert "math_probe" in summary
        assert "123ms" in summary

    def test_summary_failed(self):
        target = ModelTarget(provider_id="openai", model_name="gpt-4")
        result = ProbeResult(
            probe_name="style_probe",
            probe_type=ProbeType.STYLE,
            target=target,
            passed=False,
            score=0.3,
            latency_ms=200.0,
            raw_response="test",
        )
        summary = result.summary()
        assert "FAIL" in summary

    def test_with_metrics(self):
        target = ModelTarget(provider_id="openai", model_name="gpt-4")
        result = ProbeResult(
            probe_name="test",
            probe_type=ProbeType.TIMING,
            target=target,
            passed=True,
            score=1.0,
            latency_ms=100.0,
            raw_response="",
            ttft_ms=50.0,
            mean_itl_ms=10.0,
            metric_scores={"some_metric": 0.9},
        )
        assert result.ttft_ms == 50.0
        assert "some_metric" in result.metric_scores


class TestProbeType:
    def test_all_types_exist(self):
        types = [
            ProbeType.MATH,
            ProbeType.STYLE,
            ProbeType.TIMING,
            ProbeType.CODE,
            ProbeType.FINGERPRINT,
            ProbeType.CONTEXT,
            ProbeType.ROUTING,
            ProbeType.REPETITION,
            ProbeType.CONSTRAINT,
            ProbeType.REASONING,
            ProbeType.CALIBRATION,
            ProbeType.ZEROPRINT,
            ProbeType.MULTILINGUAL,
        ]
        assert len(types) >= 13


class TestLogprobToken:
    def test_creation(self):
        token = LogprobToken(token="hello", logprob=-0.5)
        assert token.token == "hello"
        assert token.logprob == -0.5

    def test_with_top_logprobs(self):
        token = LogprobToken(
            token="world",
            logprob=-0.3,
            top_logprobs={"world": -0.3, "there": -0.8},
        )
        assert len(token.top_logprobs) == 2


class TestLogprobResult:
    def test_creation(self):
        tokens = [
            LogprobToken(token="The", logprob=-0.1),
            LogprobToken(token="answer", logprob=-0.2),
        ]
        result = LogprobResult(text="The answer", tokens=tokens)
        assert result.text == "The answer"
        assert len(result.tokens) == 2
