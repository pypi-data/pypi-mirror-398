"""Tests for ConstraintProbe."""

import pytest
from unittest.mock import AsyncMock
from nerfprobe_core import ModelTarget
from nerfprobe_core.probes.advanced import ConstraintProbe
from nerfprobe_core.probes.config import ConstraintProbeConfig


@pytest.fixture
def mock_gateway():
    return AsyncMock()


@pytest.fixture
def target():
    return ModelTarget(provider_id="test", model_name="test-model")


class TestConstraintProbe:
    @pytest.mark.asyncio
    async def test_word_count_satisfied(self, mock_gateway, target):
        mock_gateway.generate.return_value = " ".join(["word"] * 100)
        config = ConstraintProbeConfig(name="constraint_test", min_words=80, max_words=120)
        probe = ConstraintProbe(config)
        result = await probe.run(target, mock_gateway)
        assert result.passed is True
