"""Tests for RepetitionProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget
from nerfprobe_core.probes.advanced import RepetitionProbe
from nerfprobe_core.probes.config import RepetitionProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestRepetitionProbe:
    @pytest.mark.asyncio
    async def test_no_repetition(self, mock_gateway, target):
        mock_gateway.generate.return_value = "The Roman Empire had various political reforms."
        config = RepetitionProbeConfig(name="rep_test")
        probe = RepetitionProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is True
