"""Faithfulness metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class FaithfulnessMetricFactory(BaseMetricFactory):
    """Factory for FaithfulnessMetric.

    Evaluates whether the LLM's output is factually consistent with retrieval context.

    Required fields: input, actual_output, retrieval_context
    """

    @property
    def metric_name(self) -> str:
        return "faithfulness"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([
            RequiredField.INPUT,
            RequiredField.ACTUAL_OUTPUT,
            RequiredField.RETRIEVAL_CONTEXT,
        ])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import FaithfulnessMetric

        kwargs = config.to_common_kwargs()

        for key in ("truths_extraction_limit", "penalize_ambiguous_claims", "evaluation_template"):
            if key in config.extra_params:
                kwargs[key] = config.extra_params[key]

        return FaithfulnessMetric(**kwargs)
