"""Base adapter for grouped metric evaluation.

Provides common flow for adapters that group test cases by metric.
"""

from __future__ import annotations

import hashlib
import json
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

        for _group_key, (metric_name, spec_params, items) in groups.items():
            self._evaluate_group(metric_name, spec_params, items, config, metric_results_by_tc)

        return self._build_response(test_cases, metric_results_by_tc, config.default_threshold)

    def _group_by_metric(
        self,
        test_cases: list[EvaluationTestCase],
    ) -> dict[str, tuple[str, dict[str, Any], list[tuple[EvaluationTestCase, Any]]]]:
        """Group test cases by metric configuration.

        Each unique metric+params combination gets its own group.
        This ensures metrics like g_eval with different names are evaluated separately.

        Returns:
            A dict mapping group_key to (metric_name, spec_params, items).
        """
        sdk_name = self.get_sdk_name()
        groups: dict[str, tuple[str, dict[str, Any], list[tuple[EvaluationTestCase, Any]]]] = {}

        for tc in test_cases:
            for spec in tc.evaluation_specs:
                if spec.sdk != sdk_name:
                    continue

                metric_name = spec.metric.lower()
                group_key = self._get_metric_group_key(metric_name, spec.params)
                sdk_tc = self._build_sdk_test_case(tc, spec)

                if group_key not in groups:
                    groups[group_key] = (metric_name, dict(spec.params), [])
                groups[group_key][2].append((tc, sdk_tc))

        return groups

    def _get_metric_group_key(self, metric_name: str, params: dict[str, Any]) -> str:
        """Generate a unique key for metric grouping.

        Different param combinations (e.g., different g_eval names) get different keys.
        """
        # Create a stable hash of the params to distinguish different configurations
        params_json = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_json.encode()).hexdigest()[:8]
        return f"{metric_name}:{params_hash}"

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
        spec_params: dict[str, Any],
        items: list[tuple[EvaluationTestCase, Any]],
        config: EvaluationConfig,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Evaluate a group of test cases for a single metric configuration.

        Args:
            metric_name: The metric type name (e.g., "g_eval", "answer_relevancy").
            spec_params: The params from the evaluation spec for this metric.
            items: List of (EvaluationTestCase, SDK test case) tuples.
            config: Evaluation configuration.
            metric_results_by_tc: Dict to append results to, keyed by test case ID.
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
