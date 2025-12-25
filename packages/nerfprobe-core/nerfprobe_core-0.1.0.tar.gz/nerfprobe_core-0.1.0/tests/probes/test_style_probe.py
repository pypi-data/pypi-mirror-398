"""Tests for StyleProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget, ProbeType
from nerfprobe_core.probes.core import StyleProbe
from nerfprobe_core.probes.config import StyleProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestStyleProbe:
    @pytest.mark.asyncio
    async def test_high_ttr_passes(self, mock_gateway, target):
        mock_gateway.generate.return_value = (
            "The ancient robot discovered mysterious ruins hidden beneath the desert sands."
        )
        config = StyleProbeConfig(name="style_test", min_ttr=0.5, sliding_window_size=10)
        probe = StyleProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is True
        assert result.probe_type == ProbeType.STYLE

    @pytest.mark.asyncio
    async def test_low_ttr_fails(self, mock_gateway, target):
        mock_gateway.generate.return_value = "the the the the the the the the"
        config = StyleProbeConfig(name="style_test", min_ttr=0.5)
        probe = StyleProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is False
