"""DeepEval metric registry.

Manages all metric factories and provides a unified interface for metric creation.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    SimpleMetricFactory,
)


# Metric definitions: (metric_name, metric_class_name, required_params, unsupported_params)
_METRIC_DEFINITIONS: list[tuple[str, str, frozenset[str], frozenset[str]]] = [
    ("answer_relevancy", "AnswerRelevancyMetric", frozenset(), frozenset()),
    ("faithfulness", "FaithfulnessMetric", frozenset(), frozenset()),
    ("contextual_precision", "ContextualPrecisionMetric", frozenset(), frozenset()),
    ("contextual_recall", "ContextualRecallMetric", frozenset(), frozenset()),
    ("contextual_relevancy", "ContextualRelevancyMetric", frozenset(), frozenset()),
    ("hallucination", "HallucinationMetric", frozenset(), frozenset()),
    ("bias", "BiasMetric", frozenset(), frozenset()),
    ("toxicity", "ToxicityMetric", frozenset(), frozenset()),
    ("summarization", "SummarizationMetric", frozenset(), frozenset()),
    ("g_eval", "GEval", frozenset(["name", "evaluation_params"]), frozenset()),
]


class DeepEvalMetricRegistry:
    """Registry for DeepEval metric factories."""

    def __init__(self) -> None:
        self._factories: dict[str, BaseMetricFactory] = {}
        self._register_default_factories()

    def _register_default_factories(self) -> None:
        for name, class_name, required, unsupported in _METRIC_DEFINITIONS:
            self._factories[name] = SimpleMetricFactory(
                metric_name=name,
                metric_class_name=class_name,
                required_params=required,
                unsupported_params=unsupported,
            )

    def register(self, factory: BaseMetricFactory) -> "DeepEvalMetricRegistry":
        """Register a custom metric factory. Returns self for chaining."""
        self._factories[factory.metric_name] = factory
        return self

    def supports_metric(self, metric_name: str) -> bool:
        return metric_name.lower() in self._factories

    def get_factory(self, metric_name: str) -> BaseMetricFactory | None:
        """Get a factory by metric name."""
        return self._factories.get(metric_name.lower())

    def get_supported_metrics(self) -> frozenset[str]:
        return frozenset(self._factories.keys())

    def create_metric(
        self,
        metric_name: str,
        params: dict[str, Any],
        threshold: float,
    ) -> Any:
        """Create a metric instance from params.

        Args:
            metric_name: The metric name.
            params: Parameters from YAML.
            threshold: Default threshold value.

        Returns:
            The metric instance.
        """
        factory = self._factories.get(metric_name.lower())
        if factory is None:
            raise ValueError(f"Unsupported metric: {metric_name}")
        return factory.create(params, threshold)
