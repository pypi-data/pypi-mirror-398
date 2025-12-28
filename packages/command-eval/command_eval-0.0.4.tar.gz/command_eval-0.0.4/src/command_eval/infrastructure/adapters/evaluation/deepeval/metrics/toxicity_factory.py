"""Toxicity metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class ToxicityMetricFactory(BaseMetricFactory):
    """Factory for ToxicityMetric.

    Evaluates whether the LLM's output contains toxic content.
    Note: threshold is a MAXIMUM (lower is better).

    Required fields: input, actual_output
    """

    @property
    def metric_name(self) -> str:
        return "toxicity"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([RequiredField.INPUT, RequiredField.ACTUAL_OUTPUT])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import ToxicityMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return ToxicityMetric(**kwargs)
