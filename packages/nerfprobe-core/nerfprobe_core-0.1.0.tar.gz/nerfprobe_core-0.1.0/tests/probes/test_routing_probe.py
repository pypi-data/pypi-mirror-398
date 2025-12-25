"""Tests for RoutingProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget, ProbeType
from nerfprobe_core.probes.advanced import RoutingProbe
from nerfprobe_core.probes.config import RoutingProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestRoutingProbe:
    @pytest.mark.asyncio
    async def test_routing_probe_runs(self, mock_gateway, target):
        async def mock_generate(t, p):
            if "25 + 32" in p:
                return "The answer is 57"
            if "France" in p:
                return "The capital of France is Paris"
            return "response"
        mock_gateway.generate.side_effect = mock_generate
        config = RoutingProbeConfig()
        probe = RoutingProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.probe_name == "routing_probe"
        assert result.probe_type == ProbeType.ROUTING
