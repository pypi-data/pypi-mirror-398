"""Summarization metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class SummarizationMetricFactory(BaseMetricFactory):
    """Factory for SummarizationMetric.

    Evaluates summary quality based on alignment and coverage.

    Required fields: input, actual_output
    """

    @property
    def metric_name(self) -> str:
        return "summarization"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([RequiredField.INPUT, RequiredField.ACTUAL_OUTPUT])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import SummarizationMetric

        kwargs = config.to_common_kwargs()

        for key in ("assessment_questions", "n", "truths_extraction_limit"):
            if key in config.extra_params:
                kwargs[key] = config.extra_params[key]

        return SummarizationMetric(**kwargs)
