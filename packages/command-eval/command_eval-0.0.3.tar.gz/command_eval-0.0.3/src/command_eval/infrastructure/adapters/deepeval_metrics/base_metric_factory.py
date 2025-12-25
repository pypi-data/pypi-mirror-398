"""Base metric factory for DeepEval metrics.

Provides common interface and configuration for all metric factories.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MetricConfig:
    """Configuration for DeepEval metrics.

    Attributes:
        threshold: Minimum/maximum passing threshold (0.0-1.0).
        model: Model name for evaluation (e.g., "gpt-4", "gpt-4-turbo").
        include_reason: Whether to include reasoning with score.
        strict_mode: Enforce binary scoring (0 or 1).
        async_mode: Enable concurrent execution.
        verbose_mode: Print intermediate calculation steps.
        extra_params: Additional metric-specific parameters.
    """

    threshold: float = 0.5
    model: str | None = None
    include_reason: bool = True
    strict_mode: bool = False
    async_mode: bool = True
    verbose_mode: bool = False
    extra_params: dict[str, Any] = field(default_factory=dict)

    def to_common_kwargs(self) -> dict[str, Any]:
        """Convert common config to kwargs for metric constructor.

        Returns:
            Dictionary of common constructor arguments.
        """
        kwargs: dict[str, Any] = {
            "threshold": self.threshold,
            "include_reason": self.include_reason,
            "strict_mode": self.strict_mode,
            "async_mode": self.async_mode,
            "verbose_mode": self.verbose_mode,
        }
        if self.model is not None:
            kwargs["model"] = self.model
        return kwargs


class BaseMetricFactory(ABC):
    """Abstract base factory for creating DeepEval metrics.

    Each metric type should have its own factory implementation.
    """

    @property
    @abstractmethod
    def metric_name(self) -> str:
        """Get the metric name (e.g., 'answer_relevancy').

        Returns:
            The metric name string.
        """
        pass

    @abstractmethod
    def create(self, config: MetricConfig) -> Any:
        """Create a metric instance with the given configuration.

        Args:
            config: Metric configuration.

        Returns:
            A DeepEval metric instance.
        """
        pass

    def create_from_params(self, params: dict[str, Any], threshold: float) -> Any:
        """Create a metric from evaluation_spec params.

        Args:
            params: Parameters from evaluation_spec.
            threshold: Default threshold value.

        Returns:
            A DeepEval metric instance.
        """
        config = self._build_config(params, threshold)
        return self.create(config)

    def _build_config(self, params: dict[str, Any], threshold: float) -> MetricConfig:
        """Build MetricConfig from params.

        Args:
            params: Parameters from evaluation_spec.
            threshold: Default threshold value.

        Returns:
            MetricConfig instance.
        """
        extra_params = {}
        known_keys = {
            "threshold",
            "model",
            "include_reason",
            "strict_mode",
            "async_mode",
            "verbose_mode",
        }

        for key, value in params.items():
            if key not in known_keys:
                extra_params[key] = value

        return MetricConfig(
            threshold=params.get("threshold", threshold),
            model=params.get("model"),
            include_reason=params.get("include_reason", True),
            strict_mode=params.get("strict_mode", False),
            async_mode=params.get("async_mode", True),
            verbose_mode=params.get("verbose_mode", False),
            extra_params=extra_params,
        )
