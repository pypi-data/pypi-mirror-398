"""TestCaseResult entity.

Represents the evaluation result for a single test case.
"""

from __future__ import annotations

from dataclasses import dataclass

from command_eval.domain.entities.metric_result import MetricResult
from command_eval.domain.value_objects.ids.test_case_id import TestCaseId


@dataclass(frozen=True)
class TestCaseResult:
    """The evaluation result for a single test case.

    Attributes:
        test_case_id: The ID of the evaluated test case.
        metric_results: Detailed per-metric results with SDK info and reasons.
    """

    test_case_id: TestCaseId
    metric_results: tuple[MetricResult, ...]

    @property
    def passed(self) -> bool:
        """All metrics passed."""
        if not self.metric_results:
            return False
        return all(mr.passed for mr in self.metric_results)

    @property
    def metrics(self) -> dict[str, float]:
        """Scores for each metric."""
        return {mr.metric: mr.score for mr in self.metric_results}

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
