"""Tests for CodeProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget, ProbeType
from nerfprobe_core.probes.core import CodeProbe
from nerfprobe_core.probes.config import CodeProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestCodeProbe:
    @pytest.mark.asyncio
    async def test_valid_code_passes(self, mock_gateway, target):
        mock_gateway.generate.return_value = "```python\ndef fizzbuzz(n):\n    return n % 15 == 0\n```"
        config = CodeProbeConfig(name="code_test")
        probe = CodeProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is True
        assert result.probe_type == ProbeType.CODE

    @pytest.mark.asyncio
    async def test_invalid_code_fails(self, mock_gateway, target):
        mock_gateway.generate.return_value = "```python\ndef broken(\n    return\n```"
        config = CodeProbeConfig(name="code_test")
        probe = CodeProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is False
