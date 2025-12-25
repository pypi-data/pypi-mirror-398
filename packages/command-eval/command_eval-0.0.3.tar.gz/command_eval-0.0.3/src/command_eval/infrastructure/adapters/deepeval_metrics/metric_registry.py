"""DeepEval metric registry.

Manages all metric factories and provides a unified interface for metric creation.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.answer_relevancy_factory import (
    AnswerRelevancyMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)
from command_eval.infrastructure.adapters.deepeval_metrics.bias_factory import (
    BiasMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.contextual_precision_factory import (
    ContextualPrecisionMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.contextual_recall_factory import (
    ContextualRecallMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.contextual_relevancy_factory import (
    ContextualRelevancyMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.faithfulness_factory import (
    FaithfulnessMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.g_eval_factory import (
    GEvalMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.hallucination_factory import (
    HallucinationMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.summarization_factory import (
    SummarizationMetricFactory,
)
from command_eval.infrastructure.adapters.deepeval_metrics.toxicity_factory import (
    ToxicityMetricFactory,
)


class DeepEvalMetricRegistry:
    """Registry for DeepEval metric factories.

    Provides a centralized place to get metric factories by name
    and create metrics with configuration.
    """

    def __init__(self) -> None:
        """Initialize the registry with all available factories."""
        self._factories: dict[str, BaseMetricFactory] = {}
        self._register_default_factories()

    def _register_default_factories(self) -> None:
        """Register all default metric factories."""
        factories: list[BaseMetricFactory] = [
            AnswerRelevancyMetricFactory(),
            FaithfulnessMetricFactory(),
            ContextualPrecisionMetricFactory(),
            ContextualRecallMetricFactory(),
            ContextualRelevancyMetricFactory(),
            HallucinationMetricFactory(),
            BiasMetricFactory(),
            ToxicityMetricFactory(),
            SummarizationMetricFactory(),
            GEvalMetricFactory(),
        ]

        for factory in factories:
            self._factories[factory.metric_name] = factory

    def register(self, factory: BaseMetricFactory) -> None:
        """Register a custom metric factory.

        Args:
            factory: The factory to register.
        """
        self._factories[factory.metric_name] = factory

    def get_factory(self, metric_name: str) -> BaseMetricFactory | None:
        """Get a factory by metric name.

        Args:
            metric_name: The metric name (e.g., 'answer_relevancy').

        Returns:
            The factory if found, None otherwise.
        """
        return self._factories.get(metric_name.lower())

    def supports_metric(self, metric_name: str) -> bool:
        """Check if a metric is supported.

        Args:
            metric_name: The metric name to check.

        Returns:
            True if supported, False otherwise.
        """
        return metric_name.lower() in self._factories

    def get_supported_metrics(self) -> frozenset[str]:
        """Get all supported metric names.

        Returns:
            Frozenset of supported metric names.
        """
        return frozenset(self._factories.keys())

    def create_metric(
        self,
        metric_name: str,
        config: MetricConfig,
    ) -> Any:
        """Create a metric instance.

        Args:
            metric_name: The metric name.
            config: Metric configuration.

        Returns:
            The metric instance.

        Raises:
            ValueError: If metric is not supported.
        """
        factory = self.get_factory(metric_name)
        if factory is None:
            raise ValueError(f"Unsupported metric: {metric_name}")
        return factory.create(config)

    def create_metric_from_params(
        self,
        metric_name: str,
        params: dict[str, Any],
        threshold: float,
    ) -> Any:
        """Create a metric from evaluation_spec params.

        Args:
            metric_name: The metric name.
            params: Parameters from evaluation_spec.
            threshold: Default threshold value.

        Returns:
            The metric instance.

        Raises:
            ValueError: If metric is not supported.
        """
        factory = self.get_factory(metric_name)
        if factory is None:
            raise ValueError(f"Unsupported metric: {metric_name}")
        return factory.create_from_params(params, threshold)


# Global registry instance
_default_registry: DeepEvalMetricRegistry | None = None


def get_default_registry() -> DeepEvalMetricRegistry:
    """Get the default metric registry.

    Returns:
        The default registry instance.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = DeepEvalMetricRegistry()
    return _default_registry
