"""Tests for FingerprintProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget, ProbeType
from nerfprobe_core.probes.advanced import FingerprintProbe
from nerfprobe_core.probes.config import FingerprintProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestFingerprintProbe:
    @pytest.mark.asyncio
    async def test_no_fingerprint_detected(self, mock_gateway, target):
        mock_gateway.generate.return_value = "I cannot process that input."
        config = FingerprintProbeConfig()
        probe = FingerprintProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.probe_type == ProbeType.FINGERPRINT
        assert "detected_frameworks" in result.metadata
