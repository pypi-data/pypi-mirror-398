"""Bias metric factory.

Creates BiasMetric instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)


class BiasMetricFactory(BaseMetricFactory):
    """Factory for creating BiasMetric instances.

    BiasMetric evaluates whether the LLM's output contains biased
    opinions or statements.

    Note: For this metric, threshold is a MAXIMUM (lower is better).

    Required LLMTestCase fields:
        - input: The user query
        - actual_output: The LLM's response

    Constructor parameters:
        - threshold (float): Maximum passing threshold (default: 0.5)
        - model (str): Evaluation model (default: 'gpt-4.1')
        - include_reason (bool): Include reasoning (default: True)
        - strict_mode (bool): Binary scoring, 0 for perfection (default: False)
        - async_mode (bool): Concurrent execution (default: True)
        - verbose_mode (bool): Print steps (default: False)
    """

    @property
    def metric_name(self) -> str:
        """Get the metric name.

        Returns:
            'bias'
        """
        return "bias"

    def create(self, config: MetricConfig) -> Any:
        """Create a BiasMetric instance.

        Args:
            config: Metric configuration.

        Returns:
            BiasMetric instance.
        """
        from deepeval.metrics import BiasMetric

        kwargs = config.to_common_kwargs()

        return BiasMetric(**kwargs)
