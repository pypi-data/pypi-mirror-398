"""Tests for ChainOfThoughtProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget
from nerfprobe_core.probes.advanced import ChainOfThoughtProbe
from nerfprobe_core.probes.config import ChainOfThoughtProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestChainOfThoughtProbe:
    @pytest.mark.asyncio
    async def test_valid_cot(self, mock_gateway, target):
        mock_gateway.generate.return_value = "Step 1: Calculate 15 * 12 = 180.\nStep 2: Calculate 8 * 9 = 72.\nStep 3: Add: 252."
        config = ChainOfThoughtProbeConfig(name="cot_test")
        probe = ChainOfThoughtProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is True
