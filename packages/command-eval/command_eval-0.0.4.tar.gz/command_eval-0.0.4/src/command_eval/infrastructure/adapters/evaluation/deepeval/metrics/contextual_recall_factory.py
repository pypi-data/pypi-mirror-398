"""Contextual Recall metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class ContextualRecallMetricFactory(BaseMetricFactory):
    """Factory for ContextualRecallMetric.

    Evaluates whether retrieval context contains necessary info for expected output.

    Required fields: input, expected_output, retrieval_context
    """

    @property
    def metric_name(self) -> str:
        return "contextual_recall"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([
            RequiredField.INPUT,
            RequiredField.EXPECTED_OUTPUT,
            RequiredField.RETRIEVAL_CONTEXT,
        ])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import ContextualRecallMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return ContextualRecallMetric(**kwargs)
