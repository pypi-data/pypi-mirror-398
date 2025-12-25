"""Custom evaluation adapter base class.

Provides a base class for library users to create custom evaluation adapters.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from command_eval.infrastructure.logging import get_logger

_logger = get_logger(__name__)

from command_eval.domain.ports.evaluation_port import (
    EvaluationConfig,
    EvaluationPort,
    EvaluationResponse,
    EvaluationTestCase,
)
from command_eval.domain.ports.evaluation_port import (
    TestCaseResult as PortTestCaseResult,
)
from command_eval.domain.value_objects.metric_type import MetricType


@dataclass(frozen=True)
class CustomMetricResult:
    """Result of a custom metric evaluation.

    Attributes:
        score: The evaluation score (0.0 to 1.0).
        passed: Whether the test case passed.
        reason: Optional reason for the result.
        metadata: Optional additional metadata.
    """

    score: float
    passed: bool
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the result."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")


@dataclass(frozen=True)
class CustomMetricInput:
    """Input for custom metric evaluation.

    Attributes:
        test_case_id: ID of the test case.
        input: The input query.
        actual: The actual output from command execution.
        params: Merged parameters from evaluation_spec (common_param + metric-specific).
        execution_time_ms: Execution time in milliseconds.
    """

    test_case_id: str
    input: str
    actual: str
    params: dict[str, Any]
    execution_time_ms: int = 0


class CustomEvalAdapter(EvaluationPort):
    """Base class for custom evaluation adapters.

    Library users can extend this class to create custom evaluation adapters
    that integrate with the command-eval framework.

    Example:
        ```python
        class MyCustomAdapter(CustomEvalAdapter):
            def get_sdk_name(self) -> str:
                return "custom"

            def get_supported_metrics(self) -> frozenset[str]:
                return frozenset({"my_metric", "another_metric"})

            def evaluate_metric(
                self,
                metric_name: str,
                inputs: list[CustomMetricInput],
                config: EvaluationConfig,
            ) -> dict[str, CustomMetricResult]:
                results = {}
                for inp in inputs:
                    # Your custom evaluation logic here
                    score = 1.0 if "expected" in inp.actual else 0.5
                    results[inp.test_case_id] = CustomMetricResult(
                        score=score,
                        passed=score >= config.threshold,
                        reason="Custom evaluation reason",
                    )
                return results
        ```
    """

    @abstractmethod
    def get_supported_metrics(self) -> frozenset[str]:
        """Get the set of supported metric names.

        Returns:
            Frozenset of supported metric names (lowercase).
        """
        pass

    @abstractmethod
    def evaluate_metric(
        self,
        metric_name: str,
        inputs: list[CustomMetricInput],
        config: EvaluationConfig,
    ) -> dict[str, CustomMetricResult]:
        """Evaluate a specific metric on the inputs.

        Args:
            metric_name: The name of the metric to evaluate.
            inputs: List of inputs to evaluate.
            config: Evaluation configuration.

        Returns:
            Dictionary mapping test_case_id to CustomMetricResult.
        """
        pass

    def supports_metric(self, metric_type: MetricType) -> bool:
        """Check if this adapter supports a specific metric type.

        Args:
            metric_type: The metric type to check.

        Returns:
            True if the metric is supported.
        """
        return metric_type.value.lower() in self.get_supported_metrics()

    def evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Execute evaluation on test cases.

        This method handles the orchestration of custom metric evaluation.
        Subclasses should override `evaluate_metric` instead of this method.

        Args:
            test_cases: List of test cases to evaluate.
            config: Evaluation configuration.

        Returns:
            The evaluation response with results.
        """
        sdk_name = self.get_sdk_name()
        supported_metrics = self.get_supported_metrics()

        _logger.info("CustomEvalAdapter [%s]: Starting evaluation", sdk_name)
        _logger.info("  Supported metrics: %s", list(supported_metrics))
        _logger.info("  Test cases: %d", len(test_cases))

        if not test_cases:
            return EvaluationResponse.create(tuple(), config.threshold)

        # Group inputs by metric
        metric_inputs: dict[str, list[CustomMetricInput]] = {}

        for tc in test_cases:
            for spec in tc.evaluation_specs:
                if spec.sdk.lower() != sdk_name:
                    continue

                metric_name = spec.metric.lower()
                if metric_name not in supported_metrics:
                    _logger.warning("  Unsupported metric: %s", metric_name)
                    continue

                if metric_name not in metric_inputs:
                    metric_inputs[metric_name] = []

                metric_inputs[metric_name].append(
                    CustomMetricInput(
                        test_case_id=tc.id,
                        input=tc.input,
                        actual=tc.actual,
                        params=dict(spec.params),
                        execution_time_ms=tc.execution_time_ms,
                    )
                )

        _logger.info("  Metrics to evaluate: %s",
                    {k: len(v) for k, v in metric_inputs.items()})

        # Evaluate each metric
        all_results: dict[str, dict[str, CustomMetricResult]] = {}

        for metric_name, inputs in metric_inputs.items():
            _logger.info("  Evaluating metric: %s (%d inputs)", metric_name, len(inputs))
            try:
                results = self.evaluate_metric(metric_name, inputs, config)
                all_results[metric_name] = results
                for tc_id, result in results.items():
                    _logger.debug("    %s: score=%.2f passed=%s reason=%s",
                                 tc_id, result.score, result.passed,
                                 result.reason[:50] if result.reason else None)
            except Exception as e:
                _logger.error("  Error evaluating %s: %s", metric_name, e)
                # Create error results for this metric
                all_results[metric_name] = {
                    inp.test_case_id: CustomMetricResult(
                        score=0.0,
                        passed=False,
                        reason=f"Error evaluating {metric_name}: {e}",
                    )
                    for inp in inputs
                }

        # Aggregate results per test case
        test_case_results: dict[str, PortTestCaseResult] = {}

        for tc in test_cases:
            metrics: dict[str, float] = {}
            scores: list[float] = []
            reasons: list[str] = []

            for metric_name, results in all_results.items():
                if tc.id in results:
                    result = results[tc.id]
                    metrics[metric_name] = result.score
                    scores.append(result.score)
                    if result.reason:
                        reasons.append(f"{metric_name}: {result.reason}")

            if scores:
                avg_score = sum(scores) / len(scores)
                passed = avg_score >= config.threshold
                reason = "; ".join(reasons) if reasons else None

                test_case_results[tc.id] = PortTestCaseResult(
                    test_case_id=tc.id,
                    score=avg_score,
                    passed=passed,
                    metrics=metrics,
                    reason=reason,
                )
            else:
                # No metrics evaluated for this test case
                test_case_results[tc.id] = PortTestCaseResult(
                    test_case_id=tc.id,
                    score=0.0,
                    passed=False,
                    metrics={},
                    reason=f"No matching metrics for SDK: {sdk_name}",
                )

        # Create ordered results
        ordered_results = tuple(
            test_case_results[tc.id]
            for tc in test_cases
            if tc.id in test_case_results
        )

        response = EvaluationResponse.create(ordered_results, config.threshold)
        _logger.info("  Results: passed=%d failed=%d overall=%.2f",
                    response.passed_count, response.failed_count,
                    response.overall_score)

        return response
