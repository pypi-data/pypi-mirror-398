"""Tests for MathProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget, ProbeType
from nerfprobe_core.probes.core import MathProbe
from nerfprobe_core.probes.config import MathProbeConfig


@pytest.fixture
def mock_gateway():
    gateway = AsyncMock()
    gateway.generate = AsyncMock(return_value="Mock response")
    return gateway


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestMathProbe:
    @pytest.mark.asyncio
    async def test_correct_answer(self, mock_gateway, target):
        mock_gateway.generate.return_value = "The answer is 252."
        config = MathProbeConfig(name="math_test", prompt="What is 15*12 + 8*9?", expected_answer="252")
        probe = MathProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is True
        assert result.score == 1.0
        assert result.probe_type == ProbeType.MATH

    @pytest.mark.asyncio
    async def test_wrong_answer(self, mock_gateway, target):
        mock_gateway.generate.return_value = "The answer is 100."
        config = MathProbeConfig(name="math_test", prompt="test", expected_answer="252")
        probe = MathProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_gateway_error(self, mock_gateway, target):
        mock_gateway.generate.side_effect = Exception("API Error")
        config = MathProbeConfig(name="math_test", prompt="test", expected_answer="42")
        probe = MathProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is False
        assert "ERROR" in result.raw_response
