"""Probes module - organized by tier."""

# Advanced tier probes
from nerfprobe_core.probes.advanced import (
    ChainOfThoughtProbe,
    ConstraintProbe,
    ContextProbe,
    FingerprintProbe,
    LogicProbe,
    RepetitionProbe,
    RoutingProbe,
)
from nerfprobe_core.probes.config import (
    # Base
    BaseProbeConfig,
    # Optional tier
    CalibrationProbeConfig,
    ChainOfThoughtProbeConfig,
    CodeProbeConfig,
    # Utility
    ComparisonProbeConfig,
    ConstraintProbeConfig,
    ContextProbeConfig,
    FactProbeConfig,
    # Advanced tier
    FingerprintProbeConfig,
    LogicPuzzleProbeConfig,
    # Core tier
    MathProbeConfig,
    MultilingualProbeConfig,
    RepetitionProbeConfig,
    RoutingProbeConfig,
    StyleProbeConfig,
    TimingProbeConfig,
    ZeroPrintProbeConfig,
)

# Core tier probes
from nerfprobe_core.probes.core import (
    CodeProbe,
    MathProbe,
    StyleProbe,
    TimingProbe,
)

# Optional tier probes
from nerfprobe_core.probes.optional import (
    CalibrationProbe,
    MultilingualProbe,
    ZeroPrintProbe,
)

# Tier definitions for CLI --tier flag
CORE_PROBES = ["math", "style", "timing", "code"]
ADVANCED_PROBES = [
    "fingerprint",
    "context",
    "routing",
    "repetition",
    "constraint",
    "logic",
    "cot",
]
OPTIONAL_PROBES = ["calibration", "zeroprint", "multilingual"]

ALL_PROBES = CORE_PROBES + ADVANCED_PROBES + OPTIONAL_PROBES

# Probe class registry
PROBE_REGISTRY = {
    # Core
    "math": MathProbe,
    "style": StyleProbe,
    "timing": TimingProbe,
    "code": CodeProbe,
    # Advanced
    "fingerprint": FingerprintProbe,
    "context": ContextProbe,
    "routing": RoutingProbe,
    "repetition": RepetitionProbe,
    "constraint": ConstraintProbe,
    "logic": LogicProbe,
    "cot": ChainOfThoughtProbe,
    # Optional
    "calibration": CalibrationProbe,
    "zeroprint": ZeroPrintProbe,
    "multilingual": MultilingualProbe,
}

__all__ = [
    # Configs
    "BaseProbeConfig",
    "MathProbeConfig",
    "StyleProbeConfig",
    "TimingProbeConfig",
    "CodeProbeConfig",
    "FingerprintProbeConfig",
    "ContextProbeConfig",
    "RoutingProbeConfig",
    "RepetitionProbeConfig",
    "ConstraintProbeConfig",
    "LogicPuzzleProbeConfig",
    "ChainOfThoughtProbeConfig",
    "CalibrationProbeConfig",
    "ZeroPrintProbeConfig",
    "MultilingualProbeConfig",
    "ComparisonProbeConfig",
    "FactProbeConfig",
    # Probe classes
    "MathProbe",
    "StyleProbe",
    "TimingProbe",
    "CodeProbe",
    "FingerprintProbe",
    "ContextProbe",
    "RoutingProbe",
    "RepetitionProbe",
    "ConstraintProbe",
    "LogicProbe",
    "ChainOfThoughtProbe",
    "CalibrationProbe",
    "ZeroPrintProbe",
    "MultilingualProbe",
    # Tier lists
    "CORE_PROBES",
    "ADVANCED_PROBES",
    "OPTIONAL_PROBES",
    "ALL_PROBES",
    "PROBE_REGISTRY",
]
