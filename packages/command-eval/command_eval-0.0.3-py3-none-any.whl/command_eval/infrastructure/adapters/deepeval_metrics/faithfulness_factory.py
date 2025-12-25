"""Faithfulness metric factory.

Creates FaithfulnessMetric instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)


class FaithfulnessMetricFactory(BaseMetricFactory):
    """Factory for creating FaithfulnessMetric instances.

    FaithfulnessMetric evaluates whether the LLM's output is factually
    consistent with the provided retrieval context.

    Required LLMTestCase fields:
        - input: The user query
        - actual_output: The LLM's response
        - retrieval_context: List of context strings

    Constructor parameters:
        - threshold (float): Minimum passing threshold (default: 0.5)
        - model (str): Evaluation model (default: 'gpt-4.1')
        - include_reason (bool): Include reasoning (default: True)
        - strict_mode (bool): Binary scoring (default: False)
        - async_mode (bool): Concurrent execution (default: True)
        - verbose_mode (bool): Print steps (default: False)
        - truths_extraction_limit (int): Max truths to extract (optional)
        - penalize_ambiguous_claims (bool): Exclude ambiguous claims (default: False)
        - evaluation_template: Custom prompt template (optional)
    """

    @property
    def metric_name(self) -> str:
        """Get the metric name.

        Returns:
            'faithfulness'
        """
        return "faithfulness"

    def create(self, config: MetricConfig) -> Any:
        """Create a FaithfulnessMetric instance.

        Args:
            config: Metric configuration.

        Returns:
            FaithfulnessMetric instance.
        """
        from deepeval.metrics import FaithfulnessMetric

        kwargs = config.to_common_kwargs()

        # Handle FaithfulnessMetric-specific parameters
        if "truths_extraction_limit" in config.extra_params:
            kwargs["truths_extraction_limit"] = config.extra_params[
                "truths_extraction_limit"
            ]

        if "penalize_ambiguous_claims" in config.extra_params:
            kwargs["penalize_ambiguous_claims"] = config.extra_params[
                "penalize_ambiguous_claims"
            ]

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return FaithfulnessMetric(**kwargs)
