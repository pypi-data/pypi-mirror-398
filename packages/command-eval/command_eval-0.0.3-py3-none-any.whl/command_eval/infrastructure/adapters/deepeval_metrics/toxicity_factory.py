"""Toxicity metric factory.

Creates ToxicityMetric instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)


class ToxicityMetricFactory(BaseMetricFactory):
    """Factory for creating ToxicityMetric instances.

    ToxicityMetric evaluates whether the LLM's output contains toxic content
    such as personal attacks, mockery, hate speech, dismissive statements,
    or threats.

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
            'toxicity'
        """
        return "toxicity"

    def create(self, config: MetricConfig) -> Any:
        """Create a ToxicityMetric instance.

        Args:
            config: Metric configuration.

        Returns:
            ToxicityMetric instance.
        """
        from deepeval.metrics import ToxicityMetric

        kwargs = config.to_common_kwargs()

        return ToxicityMetric(**kwargs)
