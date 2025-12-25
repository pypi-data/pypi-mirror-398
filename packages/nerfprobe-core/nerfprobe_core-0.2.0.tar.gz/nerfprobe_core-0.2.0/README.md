# NerfProbe Core

Shared probe and scorer implementations for scientifically-grounded LLM degradation detection.

## Installation

```bash
pip install nerfprobe-core
```

## Overview

**nerfprobe-core** provides the detection logic used by:
- **[nerfprobe](https://pypi.org/project/nerfprobe/)** - CLI tool for developers
- **[NerfStatus](https://nerfstatus.com)** - Monitoring service

## Probes

14 probes across 3 tiers, each grounded in peer-reviewed research:

### Core Tier
| Probe | Detection | Research |
|-------|-----------|----------|
| MathProbe | Arithmetic reasoning degradation | [2504.04823](https://arxiv.org/abs/2504.04823) |
| StyleProbe | Vocabulary collapse (TTR) | [2403.06408](https://arxiv.org/abs/2403.06408) |
| TimingProbe | Latency fingerprinting | [2502.20589](https://arxiv.org/abs/2502.20589) |
| CodeProbe | Syntax collapse | [2512.08213](https://arxiv.org/abs/2512.08213) |

### Advanced Tier
| Probe | Detection | Research |
|-------|-----------|----------|
| FingerprintProbe | Framework detection | [2407.15847](https://arxiv.org/abs/2407.15847) |
| ContextProbe | KV cache compression | [2512.12008](https://arxiv.org/abs/2512.12008) |
| RoutingProbe | Model routing detection | [2406.18665](https://arxiv.org/abs/2406.18665) |
| RepetitionProbe | Phrase looping | [2403.06408](https://arxiv.org/abs/2403.06408) |
| ConstraintProbe | Instruction adherence | [2409.11055](https://arxiv.org/abs/2409.11055) |
| LogicProbe | Reasoning drift | [2504.04823](https://arxiv.org/abs/2504.04823) |
| ChainOfThoughtProbe | CoT integrity | [2504.04823](https://arxiv.org/abs/2504.04823) |

### Optional Tier
| Probe | Detection | Research |
|-------|-----------|----------|
| CalibrationProbe | Confidence calibration | [2511.07585](https://arxiv.org/abs/2511.07585) |
| ZeroPrintProbe | Mode collapse | [2407.01235](https://arxiv.org/abs/2407.01235) |
| MultilingualProbe | Cross-language asymmetry | [EMNLP.935](https://aclanthology.org/2023.findings-emnlp.935/) |

## Scorers

10 scoring implementations:
- **MathScorer** - Expected answer matching
- **TTRScorer** - Type-Token Ratio calculation
- **CodeScorer** - Python syntax validation
- **RepetitionScorer** - N-gram repetition detection
- **ConstraintScorer** - Word count and forbidden word checks
- **LogicScorer** - Answer + reasoning validation
- **ChainOfThoughtScorer** - Step counting & circular detection
- **CalibrationScorer** - Confidence extraction
- **EntropyScorer** - Shannon entropy calculation
- **MultilingualScorer** - Cross-language consistency

## Model Registry

Ships with 10 SOTA models (Dec 2025) with probe-relevant fields:
- `context_window` - For ContextProbe
- `knowledge_cutoff` - For TemporalProbe

```python
from nerfprobe_core import get_model_info, RESEARCH_PROMPT

# Known model
info = get_model_info("gpt-5.2")
print(f"Context: {info.context_window:,}")

# Unknown model - get research prompt
prompt = RESEARCH_PROMPT.format(model_name="new-model", provider="provider")
```

## Usage

```python
from nerfprobe_core import ModelTarget
from nerfprobe_core.probes import MathProbe
from nerfprobe_core.probes.config import MathProbeConfig

# Configure probe
config = MathProbeConfig(
    prompt="What is 15 * 12 + 8 * 9?",
    expected_answer="252",
)

# Run probe
target = ModelTarget(provider_id="openai", model_name="gpt-5.2")
probe = MathProbe(config)
result = await probe.run(target, gateway)

print(result.summary())  # math_probe: PASS (1.00) in 234ms
```

## Dependencies

- `pydantic>=2.0.0`
- `pyyaml>=6.0.0`

## License

Apache-2.0
