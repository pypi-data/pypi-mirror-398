"""Base adapter for grouped metric evaluation.

Provides common flow for adapters that group test cases by metric.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from command_eval.domain.ports.evaluation_port import (
    EvaluationConfig,
    EvaluationPort,
    EvaluationResponse,
    EvaluationTestCase,
    MetricResult as PortMetricResult,
    TestCaseResult as PortTestCaseResult,
)
from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec


class BaseGroupedEvaluationAdapter(EvaluationPort):
    """Base adapter that groups test cases by metric for evaluation.

    Subclasses must implement SDK-specific logic for:
    - Building SDK test cases
    - Evaluating metric groups
    """

    def evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Execute evaluation by grouping test cases by metric."""
        groups = self._group_by_metric(test_cases)

        if not groups:
            raise ValueError(f"No {self.get_sdk_name()} metrics found in test cases")

        metric_results_by_tc: dict[str, list[PortMetricResult]] = {
            tc.id: [] for tc in test_cases
        }

        for metric_name, items in groups.items():
            self._evaluate_group(metric_name, items, config, metric_results_by_tc)

        return self._build_response(test_cases, metric_results_by_tc, config.default_threshold)

    def _group_by_metric(
        self,
        test_cases: list[EvaluationTestCase],
    ) -> dict[str, list[tuple[EvaluationTestCase, Any]]]:
        """Group test cases by metric name.

        Each metric gets its own SDK test case built with metric-specific params.
        """
        sdk_name = self.get_sdk_name()
        groups: dict[str, list[tuple[EvaluationTestCase, Any]]] = {}

        for tc in test_cases:
            for spec in tc.evaluation_specs:
                if spec.sdk != sdk_name:
                    continue

                metric_name = spec.metric.lower()
                sdk_tc = self._build_sdk_test_case(tc, spec)

                if metric_name not in groups:
                    groups[metric_name] = []
                groups[metric_name].append((tc, sdk_tc))

        return groups

    @abstractmethod
    def _build_sdk_test_case(
        self,
        tc: EvaluationTestCase,
        spec: EvaluationSpec,
    ) -> Any:
        """Build SDK-specific test case from EvaluationTestCase."""
        pass

    @abstractmethod
    def _evaluate_group(
        self,
        metric_name: str,
        items: list[tuple[EvaluationTestCase, Any]],
        config: EvaluationConfig,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Evaluate a group of test cases for a single metric.

        Results should be appended to metric_results_by_tc.
        """
        pass

    def _build_response(
        self,
        all_test_cases: list[EvaluationTestCase],
        metric_results_by_tc: dict[str, list[PortMetricResult]],
        threshold: float,
    ) -> EvaluationResponse:
        """Build EvaluationResponse from collected metric results."""
        details: list[PortTestCaseResult] = []

        for tc in all_test_cases:
            metric_results = metric_results_by_tc.get(tc.id, [])
            details.append(
                PortTestCaseResult(
                    test_case_id=tc.id,
                    metric_results=tuple(metric_results),
                )
            )

        return EvaluationResponse.create(tuple(details), threshold)
