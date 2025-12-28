"""Hallucination metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class HallucinationMetricFactory(BaseMetricFactory):
    """Factory for HallucinationMetric.

    Evaluates whether the LLM's output contains hallucinated information.
    Note: threshold is a MAXIMUM (lower is better).

    Required fields: input, actual_output, context
    """

    @property
    def metric_name(self) -> str:
        return "hallucination"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([
            RequiredField.INPUT,
            RequiredField.ACTUAL_OUTPUT,
            RequiredField.CONTEXT,
        ])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import HallucinationMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return HallucinationMetric(**kwargs)
