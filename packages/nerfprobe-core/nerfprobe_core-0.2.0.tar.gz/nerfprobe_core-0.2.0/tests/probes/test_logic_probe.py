"""Tests for LogicProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget
from nerfprobe_core.probes.advanced import LogicProbe
from nerfprobe_core.probes.config import LogicPuzzleProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestLogicProbe:
    @pytest.mark.asyncio
    async def test_correct_with_reasoning(self, mock_gateway, target):
        mock_gateway.generate.return_value = "First, 48 / 2 = 24 clips. Then 48 + 24 = 72 total."
        config = LogicPuzzleProbeConfig(name="logic_test")
        probe = LogicProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is True
