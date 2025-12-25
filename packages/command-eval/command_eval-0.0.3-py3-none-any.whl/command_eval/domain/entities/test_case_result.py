"""TestCaseResult entity.

Represents the evaluation result for a single test case.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from command_eval.domain.entities.metric_result import MetricResult
from command_eval.domain.value_objects.ids.test_case_id import TestCaseId


@dataclass(frozen=True)
class TestCaseResult:
    """The evaluation result for a single test case.

    Attributes:
        test_case_id: The ID of the evaluated test case.
        score: The evaluation score (0.0 to 1.0).
        passed: Whether the test case passed.
        metrics: Dictionary of metric scores (legacy, for backward compat).
        reason: Overall reason for the result (optional).
        metric_results: Detailed per-metric results with SDK info and reasons.
    """

    test_case_id: TestCaseId
    score: float
    passed: bool
    metrics: dict[str, float] = field(default_factory=dict)
    reason: Optional[str] = None
    metric_results: tuple[MetricResult, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate test case result."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        for metric_name, metric_score in self.metrics.items():
            if not 0.0 <= metric_score <= 1.0:
                raise ValueError(
                    f"Metric score for '{metric_name}' must be between 0.0 and 1.0"
                )

    def get_metric_score(self, metric_name: str) -> float | None:
        """Get the score for a specific metric.

        Args:
            metric_name: The name of the metric.

        Returns:
            The metric score, or None if not found.
        """
        return self.metrics.get(metric_name)

    def get_metric_result(self, sdk: str, metric: str) -> MetricResult | None:
        """Get the detailed result for a specific metric.

        Args:
            sdk: SDK name.
            metric: Metric name.

        Returns:
            The MetricResult, or None if not found.
        """
        for mr in self.metric_results:
            if mr.sdk == sdk and mr.metric == metric:
                return mr
        return None
