"""Contextual Precision metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class ContextualPrecisionMetricFactory(BaseMetricFactory):
    """Factory for ContextualPrecisionMetric.

    Evaluates whether relevant retrieval context items are ranked higher.

    Required fields: input, expected_output, retrieval_context
    """

    @property
    def metric_name(self) -> str:
        return "contextual_precision"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([
            RequiredField.INPUT,
            RequiredField.EXPECTED_OUTPUT,
            RequiredField.RETRIEVAL_CONTEXT,
        ])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import ContextualPrecisionMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return ContextualPrecisionMetric(**kwargs)
