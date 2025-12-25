"""Unit tests for probe configs."""

import pytest
from nerfprobe_core.probes.config import (
    BaseProbeConfig,
    MathProbeConfig,
    StyleProbeConfig,
    TimingProbeConfig,
    CodeProbeConfig,
    FingerprintProbeConfig,
    ContextProbeConfig,
    RoutingProbeConfig,
    RepetitionProbeConfig,
    ConstraintProbeConfig,
    LogicPuzzleProbeConfig,
    ChainOfThoughtProbeConfig,
    CalibrationProbeConfig,
    ZeroPrintProbeConfig,
    MultilingualProbeConfig,
)


class TestMathProbeConfig:
    def test_required_fields(self):
        config = MathProbeConfig(
            name="test",
            prompt="What is 2+2?",
            expected_answer="4",
        )
        assert config.name == "test"
        assert config.expected_answer == "4"


class TestStyleProbeConfig:
    def test_defaults(self):
        config = StyleProbeConfig(name="style")
        assert config.min_ttr == 0.55
        assert config.sliding_window_size == 50
        assert "{topic}" in config.prompt_template


class TestTimingProbeConfig:
    def test_defaults(self):
        config = TimingProbeConfig(name="timing")
        assert config.token_count == 50
        assert config.max_latency_ms == 5000.0


class TestCodeProbeConfig:
    def test_defaults(self):
        config = CodeProbeConfig(name="code")
        assert config.language == "python"
        assert "FizzBuzz" in config.prompt


class TestFingerprintProbeConfig:
    def test_has_malformed_queries(self):
        config = FingerprintProbeConfig()
        assert len(config.malformed_queries) >= 2
        assert len(config.banner_prompts) >= 2


class TestContextProbeConfig:
    def test_defaults(self):
        config = ContextProbeConfig()
        assert config.context_length == 4000
        assert 0.1 in config.needle_depths
        assert 0.5 in config.needle_depths
        assert 0.9 in config.needle_depths


class TestRoutingProbeConfig:
    def test_easy_hard_prompts(self):
        config = RoutingProbeConfig()
        assert len(config.easy_prompts) >= 2
        assert len(config.hard_prompts) >= 2
        assert config.baseline_gap_threshold == 0.3


class TestRepetitionProbeConfig:
    def test_defaults(self):
        config = RepetitionProbeConfig(name="rep")
        assert config.ngram_size == 4
        assert config.max_repeats == 2


class TestConstraintProbeConfig:
    def test_word_count_type(self):
        config = ConstraintProbeConfig(
            name="constraint",
            type="word_count",
            min_words=10,
            max_words=50,
        )
        assert config.type == "word_count"
        assert config.min_words == 10


class TestLogicPuzzleProbeConfig:
    def test_defaults(self):
        config = LogicPuzzleProbeConfig(name="logic")
        assert config.expected_answer == "72"
        assert len(config.required_reasoning) >= 2


class TestChainOfThoughtProbeConfig:
    def test_defaults(self):
        config = ChainOfThoughtProbeConfig(name="cot")
        assert config.min_steps == 3
        assert config.detect_circular is True


class TestCalibrationProbeConfig:
    def test_defaults(self):
        config = CalibrationProbeConfig(name="calib")
        assert config.min_confidence == 0.9
        assert config.expected_answer == "Paris"


class TestZeroPrintProbeConfig:
    def test_defaults(self):
        config = ZeroPrintProbeConfig(name="zp")
        assert config.iterations == 20
        assert config.min_entropy == 1.0


class TestMultilingualProbeConfig:
    def test_defaults(self):
        config = MultilingualProbeConfig()
        assert "en" in config.languages
        assert len(config.languages) >= 3
