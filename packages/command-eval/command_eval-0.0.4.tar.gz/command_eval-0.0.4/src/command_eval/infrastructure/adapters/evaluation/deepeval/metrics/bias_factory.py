"""Bias metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class BiasMetricFactory(BaseMetricFactory):
    """Factory for BiasMetric.

    Evaluates whether the LLM's output contains biased opinions.
    Note: threshold is a MAXIMUM (lower is better).

    Required fields: input, actual_output
    """

    @property
    def metric_name(self) -> str:
        return "bias"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([RequiredField.INPUT, RequiredField.ACTUAL_OUTPUT])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import BiasMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return BiasMetric(**kwargs)
