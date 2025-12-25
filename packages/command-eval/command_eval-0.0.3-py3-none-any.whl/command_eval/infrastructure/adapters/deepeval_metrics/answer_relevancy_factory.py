"""Answer Relevancy metric factory.

Creates AnswerRelevancyMetric instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)


class AnswerRelevancyMetricFactory(BaseMetricFactory):
    """Factory for creating AnswerRelevancyMetric instances.

    AnswerRelevancyMetric evaluates whether the LLM's output is relevant
    to the input query.

    Required LLMTestCase fields:
        - input: The user query
        - actual_output: The LLM's response

    Constructor parameters:
        - threshold (float): Minimum passing threshold (default: 0.5)
        - model (str): Evaluation model (default: 'gpt-4.1')
        - include_reason (bool): Include reasoning (default: True)
        - strict_mode (bool): Binary scoring (default: False)
        - async_mode (bool): Concurrent execution (default: True)
        - verbose_mode (bool): Print steps (default: False)
        - evaluation_template: Custom prompt template (optional)
    """

    @property
    def metric_name(self) -> str:
        """Get the metric name.

        Returns:
            'answer_relevancy'
        """
        return "answer_relevancy"

    def create(self, config: MetricConfig) -> Any:
        """Create an AnswerRelevancyMetric instance.

        Args:
            config: Metric configuration.

        Returns:
            AnswerRelevancyMetric instance.
        """
        from deepeval.metrics import AnswerRelevancyMetric

        kwargs = config.to_common_kwargs()

        # Handle evaluation_template if provided
        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return AnswerRelevancyMetric(**kwargs)
