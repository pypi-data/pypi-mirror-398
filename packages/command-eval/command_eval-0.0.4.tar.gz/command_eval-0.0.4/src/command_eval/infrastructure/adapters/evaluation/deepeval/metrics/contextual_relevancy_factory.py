"""Contextual Relevancy metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class ContextualRelevancyMetricFactory(BaseMetricFactory):
    """Factory for ContextualRelevancyMetric.

    Evaluates whether the retrieval context is relevant to the input query.

    Required fields: input, retrieval_context
    """

    @property
    def metric_name(self) -> str:
        return "contextual_relevancy"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([
            RequiredField.INPUT,
            RequiredField.RETRIEVAL_CONTEXT,
        ])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import ContextualRelevancyMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return ContextualRelevancyMetric(**kwargs)
