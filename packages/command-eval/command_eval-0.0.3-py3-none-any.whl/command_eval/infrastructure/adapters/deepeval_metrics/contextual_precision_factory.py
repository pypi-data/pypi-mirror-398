"""Contextual Precision metric factory.

Creates ContextualPrecisionMetric instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)


class ContextualPrecisionMetricFactory(BaseMetricFactory):
    """Factory for creating ContextualPrecisionMetric instances.

    ContextualPrecisionMetric evaluates whether all items in the retrieval
    context that are relevant to the expected output are ranked higher.

    Required LLMTestCase fields:
        - input: The user query
        - actual_output: The LLM's response
        - expected_output: The expected/ground truth response
        - retrieval_context: List of context strings

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
            'contextual_precision'
        """
        return "contextual_precision"

    def create(self, config: MetricConfig) -> Any:
        """Create a ContextualPrecisionMetric instance.

        Args:
            config: Metric configuration.

        Returns:
            ContextualPrecisionMetric instance.
        """
        from deepeval.metrics import ContextualPrecisionMetric

        kwargs = config.to_common_kwargs()

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return ContextualPrecisionMetric(**kwargs)
