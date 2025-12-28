"""Answer Relevancy metric factory."""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class AnswerRelevancyMetricFactory(BaseMetricFactory):
    """Factory for AnswerRelevancyMetric.

    Evaluates whether the LLM's output is relevant to the input query.

    Required fields: input, actual_output
    """

    @property
    def metric_name(self) -> str:
        return "answer_relevancy"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset([RequiredField.INPUT, RequiredField.ACTUAL_OUTPUT])

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import AnswerRelevancyMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return AnswerRelevancyMetric(**kwargs)
