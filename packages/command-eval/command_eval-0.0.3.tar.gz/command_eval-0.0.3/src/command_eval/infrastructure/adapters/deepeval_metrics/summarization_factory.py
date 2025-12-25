"""Summarization metric factory.

Creates SummarizationMetric instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)


class SummarizationMetricFactory(BaseMetricFactory):
    """Factory for creating SummarizationMetric instances.

    SummarizationMetric evaluates the quality of a summary based on
    alignment (no hallucinations) and coverage (includes key information).

    Required LLMTestCase fields:
        - input: The original text to be summarized
        - actual_output: The LLM's summary

    Constructor parameters:
        - threshold (float): Minimum passing threshold (default: 0.5)
        - model (str): Evaluation model (default: 'gpt-4.1')
        - include_reason (bool): Include reasoning (default: True)
        - strict_mode (bool): Binary scoring (default: False)
        - async_mode (bool): Concurrent execution (default: True)
        - verbose_mode (bool): Print steps (default: False)
        - assessment_questions (list[str]): Custom yes/no questions (optional)
        - n (int): Number of auto-generated questions (default: 5)
        - truths_extraction_limit (int): Max truths to extract (optional)
    """

    @property
    def metric_name(self) -> str:
        """Get the metric name.

        Returns:
            'summarization'
        """
        return "summarization"

    def create(self, config: MetricConfig) -> Any:
        """Create a SummarizationMetric instance.

        Args:
            config: Metric configuration.

        Returns:
            SummarizationMetric instance.
        """
        from deepeval.metrics import SummarizationMetric

        kwargs = config.to_common_kwargs()

        # Handle SummarizationMetric-specific parameters
        if "assessment_questions" in config.extra_params:
            kwargs["assessment_questions"] = config.extra_params["assessment_questions"]

        if "n" in config.extra_params:
            kwargs["n"] = config.extra_params["n"]

        if "truths_extraction_limit" in config.extra_params:
            kwargs["truths_extraction_limit"] = config.extra_params[
                "truths_extraction_limit"
            ]

        return SummarizationMetric(**kwargs)
