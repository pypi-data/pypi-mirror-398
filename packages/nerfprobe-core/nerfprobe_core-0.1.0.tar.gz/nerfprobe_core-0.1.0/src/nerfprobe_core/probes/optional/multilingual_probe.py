"""
MultilingualProbe - Asymmetric degradation detection in non-English languages.

Ref: [2024.findings-emnlp.935]
"""

import time

from nerfprobe_core.core import (
    CostEstimate,
    LLMGateway,
    ModelTarget,
    ProbeResult,
    ProbeType,
)
from nerfprobe_core.probes.config import MultilingualProbeConfig
from nerfprobe_core.scorers.multilingual import MultilingualScorer

# Language name mapping
LANG_NAMES: dict[str, str] = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "pt": "Portuguese",
}


class MultilingualProbe:
    """
    Detects asymmetric degradation across languages.
    Tests if model performance differs significantly for non-English.
    """

    def __init__(self, config: MultilingualProbeConfig):
        self._config = config
        self._scorer = MultilingualScorer(expected_keywords={})

    @property
    def config(self) -> MultilingualProbeConfig:
        return self._config

    @property
    def estimated_cost(self) -> CostEstimate:
        num_langs = len(self.config.languages)
        return CostEstimate(input_tokens=50 * num_langs, output_tokens=50 * num_langs)

    async def run(self, target: ModelTarget, generator: LLMGateway) -> ProbeResult:
        if (
            self.config.max_tokens_per_run > 0
            and self.estimated_cost.total_tokens > self.config.max_tokens_per_run
        ):
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.MULTILINGUAL,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=0.0,
                raw_response="SKIPPED: Exceeds token budget",
                metadata={"error": "Token budget exceeded"},
            )

        start = time.perf_counter()
        responses: dict[str, str] = {}

        try:
            for lang in self.config.languages:
                prompt = self.config.prompt_template
                if "{target_language}" in prompt:
                    lang_name = LANG_NAMES.get(lang, lang)
                    prompt = prompt.format(target_language=lang_name)

                resp = await generator.generate(target, prompt)
                responses[lang] = resp

            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            return ProbeResult(
                probe_name=self.config.name,
                probe_type=ProbeType.MULTILINGUAL,
                target=target,
                passed=False,
                score=0.0,
                latency_ms=(time.perf_counter() - start) * 1000,
                raw_response=f"ERROR: {e!s}",
                metadata={"error": str(e)},
            )

        metrics = self._scorer.metrics(responses)
        score = metrics["consistency_score"]
        passed = metrics["passed"]

        return ProbeResult(
            probe_name=self.config.name,
            probe_type=ProbeType.MULTILINGUAL,
            target=target,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            raw_response=str(responses),
            metric_scores={"consistency": score},
            metadata={
                "research_ref": "[2024.findings-emnlp.935]",
                "config": self.config.model_dump(),
                "details": metrics["details"],
            },
        )
