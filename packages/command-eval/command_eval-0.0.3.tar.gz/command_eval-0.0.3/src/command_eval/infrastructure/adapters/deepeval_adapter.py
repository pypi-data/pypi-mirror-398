"""DeepEval-based evaluation adapter.

Uses deepeval SDK for LLM evaluation.
SDK-specific parameters are extracted from evaluation_specs via DeepEvalParamParser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from command_eval.domain.ports.evaluation_port import (
    EvaluationConfig,
    EvaluationPort,
    EvaluationResponse,
    EvaluationTestCase,
    MetricResult as PortMetricResult,
)
from command_eval.domain.ports.evaluation_port import (
    TestCaseResult as PortTestCaseResult,
)
from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.metric_type import MetricType
from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    MetricConfig,
)
from command_eval.infrastructure.adapters.deepeval_metrics.metric_registry import (
    DeepEvalMetricRegistry,
    get_default_registry,
)
from command_eval.infrastructure.adapters.deepeval_param_parser import (
    DeepEvalParamParser,
    DeepEvalResolvedParams,
)


class DeepEvalRequiredField(Enum):
    """Required fields for DeepEval metrics."""

    INPUT = "input"
    ACTUAL = "actual"
    EXPECTED = "expected"
    CONTEXT = "context"
    RETRIEVAL_CONTEXT = "retrieval_context"


# Metric-specific required fields mapping
DEEPEVAL_METRIC_REQUIREMENTS: dict[str, frozenset[DeepEvalRequiredField]] = {
    "answer_relevancy": frozenset(
        [DeepEvalRequiredField.INPUT, DeepEvalRequiredField.ACTUAL]
    ),
    "faithfulness": frozenset(
        [
            DeepEvalRequiredField.INPUT,
            DeepEvalRequiredField.ACTUAL,
            DeepEvalRequiredField.RETRIEVAL_CONTEXT,
        ]
    ),
    "contextual_precision": frozenset(
        [
            DeepEvalRequiredField.INPUT,
            DeepEvalRequiredField.ACTUAL,
            DeepEvalRequiredField.EXPECTED,
            DeepEvalRequiredField.RETRIEVAL_CONTEXT,
        ]
    ),
    "contextual_recall": frozenset(
        [
            DeepEvalRequiredField.INPUT,
            DeepEvalRequiredField.ACTUAL,
            DeepEvalRequiredField.EXPECTED,
            DeepEvalRequiredField.RETRIEVAL_CONTEXT,
        ]
    ),
    "contextual_relevancy": frozenset(
        [
            DeepEvalRequiredField.INPUT,
            DeepEvalRequiredField.ACTUAL,
            DeepEvalRequiredField.RETRIEVAL_CONTEXT,
        ]
    ),
    "hallucination": frozenset(
        [
            DeepEvalRequiredField.INPUT,
            DeepEvalRequiredField.ACTUAL,
            DeepEvalRequiredField.CONTEXT,
        ]
    ),
    "bias": frozenset([DeepEvalRequiredField.INPUT, DeepEvalRequiredField.ACTUAL]),
    "toxicity": frozenset([DeepEvalRequiredField.INPUT, DeepEvalRequiredField.ACTUAL]),
    "summarization": frozenset(
        [DeepEvalRequiredField.INPUT, DeepEvalRequiredField.ACTUAL]
    ),
    "g_eval": frozenset([DeepEvalRequiredField.INPUT, DeepEvalRequiredField.ACTUAL]),
}


@dataclass(frozen=True)
class DeepEvalValidationError:
    """Validation error for DeepEval test case.

    Attributes:
        test_case_id: ID of the test case with the error.
        metric: The metric that requires the missing field.
        missing_field: The field that is missing.
    """

    test_case_id: str
    metric: str
    missing_field: DeepEvalRequiredField


class DeepEvalTestCaseValidator:
    """Validator for DeepEval test cases.

    Validates that test cases have all required fields for the specified metrics.
    Uses DeepEvalParamParser to resolve params from evaluation_specs.
    """

    def __init__(
        self,
        param_parser: DeepEvalParamParser | None = None,
    ) -> None:
        """Initialize the validator.

        Args:
            param_parser: Parser for resolving params. Defaults to DeepEvalParamParser.
        """
        self._param_parser = param_parser or DeepEvalParamParser()

    def validate(
        self,
        test_cases: list[EvaluationTestCase],
    ) -> list[DeepEvalValidationError]:
        """Validate test cases against metric requirements.

        Metrics are derived from evaluation_specs in test cases.

        Args:
            test_cases: List of test cases to validate.

        Returns:
            List of validation errors. Empty if all test cases are valid.
        """
        errors: list[DeepEvalValidationError] = []

        for tc in test_cases:
            # Get DeepEval specs for this test case
            deepeval_specs = [
                spec for spec in tc.evaluation_specs if spec.sdk == "deepeval"
            ]

            for spec in deepeval_specs:
                metric_name = spec.metric.lower()
                requirements = DEEPEVAL_METRIC_REQUIREMENTS.get(
                    metric_name, frozenset()
                )

                # Parse params from spec
                resolved_params = self._param_parser.parse(spec.params)

                for required_field in requirements:
                    if not self._has_field(tc, resolved_params, required_field):
                        errors.append(
                            DeepEvalValidationError(
                                test_case_id=tc.id,
                                metric=metric_name,
                                missing_field=required_field,
                            )
                        )

        return errors

    def _has_field(
        self,
        tc: EvaluationTestCase,
        resolved_params: DeepEvalResolvedParams,
        field: DeepEvalRequiredField,
    ) -> bool:
        """Check if a test case has the required field.

        Args:
            tc: The test case to check.
            resolved_params: Resolved params from evaluation_spec.
            field: The field to check for.

        Returns:
            True if the field is present and non-empty.
        """
        if field == DeepEvalRequiredField.INPUT:
            return bool(tc.input)
        elif field == DeepEvalRequiredField.ACTUAL:
            return bool(tc.actual)
        elif field == DeepEvalRequiredField.EXPECTED:
            return resolved_params.expected is not None and bool(
                resolved_params.expected
            )
        elif field == DeepEvalRequiredField.CONTEXT:
            return (
                resolved_params.context is not None
                and len(resolved_params.context) > 0
            )
        elif field == DeepEvalRequiredField.RETRIEVAL_CONTEXT:
            return (
                resolved_params.retrieval_context is not None
                and len(resolved_params.retrieval_context) > 0
            )
        else:
            return False


class DeepEvalAdapter(EvaluationPort):
    """DeepEval-based implementation of EvaluationPort.

    Uses the deepeval library for LLM evaluation.
    SDK-specific parameters are extracted from evaluation_specs via DeepEvalParamParser.
    """

    def __init__(
        self,
        model: str | None = None,
        param_parser: DeepEvalParamParser | None = None,
        metric_registry: DeepEvalMetricRegistry | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the DeepEval adapter.

        Args:
            model: Model to use for evaluation (e.g., "gpt-4").
            param_parser: Parser for resolving params. Defaults to DeepEvalParamParser.
            metric_registry: Registry for metric factories. Defaults to global registry.
            **kwargs: Additional options for deepeval.
        """
        self._model = model
        self._param_parser = param_parser or DeepEvalParamParser()
        self._metric_registry = metric_registry or get_default_registry()
        self._kwargs = kwargs

    def get_sdk_name(self) -> str:
        """Get the SDK name.

        Returns:
            The SDK name "deepeval".
        """
        return "deepeval"

    def supports_metric(self, metric_type: MetricType) -> bool:
        """Check if a metric type is supported.

        Args:
            metric_type: The metric type to check.

        Returns:
            True if the metric is supported, False otherwise.
        """
        return self._metric_registry.supports_metric(metric_type.value)

    def evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Execute evaluation using deepeval.

        Args:
            test_cases: List of test cases to evaluate.
            config: Evaluation configuration.

        Returns:
            The evaluation response with results.
        """
        try:
            # Try to import deepeval
            from deepeval import evaluate as deepeval_evaluate
            from deepeval.test_case import LLMTestCase

            return self._execute_with_deepeval(
                test_cases,
                config,
                deepeval_evaluate,
                LLMTestCase,
            )
        except ImportError:
            # Fallback to mock evaluation if deepeval is not installed
            return self._mock_evaluate(test_cases, config)

    def _execute_with_deepeval(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
        deepeval_evaluate: Any,
        llm_test_case_class: Any,
    ) -> EvaluationResponse:
        """Execute evaluation using deepeval library.

        Args:
            test_cases: List of test cases.
            config: Evaluation configuration.
            deepeval_evaluate: The deepeval evaluate function.
            llm_test_case_class: The LLMTestCase class.

        Returns:
            The evaluation response.
        """
        # Group test cases by their metric set to avoid evaluating
        # test cases with metrics they don't have required fields for
        metric_groups: dict[tuple[str, ...], list[tuple[EvaluationTestCase, Any]]] = {}

        for tc in test_cases:
            # Find the first deepeval spec to get params (or use empty params)
            deepeval_spec = next(
                (s for s in tc.evaluation_specs if s.sdk == "deepeval"), None
            )
            resolved_params = (
                self._param_parser.parse(deepeval_spec.params)
                if deepeval_spec
                else DeepEvalResolvedParams()
            )

            context = (
                list(resolved_params.context) if resolved_params.context else None
            )
            retrieval_context = (
                list(resolved_params.retrieval_context)
                if resolved_params.retrieval_context
                else None
            )

            # Convert execution_time_ms to seconds for completion_time
            completion_time = (
                resolved_params.completion_time
                if resolved_params.completion_time is not None
                else tc.execution_time_ms / 1000.0
            )

            deepeval_tc = llm_test_case_class(
                input=tc.input,
                actual_output=tc.actual,
                expected_output=resolved_params.expected,
                context=context,
                retrieval_context=retrieval_context,
                name=resolved_params.name,
                completion_time=completion_time,
            )

            # Get metric names for this test case
            metric_names = tuple(
                sorted(
                    s.metric.lower()
                    for s in tc.evaluation_specs
                    if s.sdk == "deepeval"
                )
            )

            if metric_names not in metric_groups:
                metric_groups[metric_names] = []
            metric_groups[metric_names].append((tc, deepeval_tc))

        # Evaluate each group with its own metrics
        all_results: list[Any] = []
        all_original_tcs: list[EvaluationTestCase] = []

        for metric_names, group_items in metric_groups.items():
            group_tcs = [item[0] for item in group_items]
            group_deepeval_tcs = [item[1] for item in group_items]

            # Create metrics only for this group
            metrics = self._create_metrics_for_names(config, list(metric_names), group_tcs)

            if not metrics:
                continue

            # Run evaluation for this group
            results = deepeval_evaluate(
                test_cases=group_deepeval_tcs,
                metrics=metrics,
            )

            all_results.append(results)
            all_original_tcs.extend(group_tcs)

        # Merge and convert results
        return self._convert_grouped_results(
            test_cases, all_results, all_original_tcs, config.threshold
        )

    def _create_metrics(
        self,
        config: EvaluationConfig,
        test_cases: list[EvaluationTestCase] | None = None,
    ) -> list[Any]:
        """Create deepeval metrics from test case evaluation_specs.

        Args:
            config: Evaluation configuration.
            test_cases: Test cases containing evaluation_specs with metric definitions.

        Returns:
            List of deepeval metrics.
        """
        metrics = []
        created_metrics: set[str] = set()

        # Extract metric names from evaluation_specs (sdk="deepeval")
        metric_names: list[str] = []
        if test_cases:
            for tc in test_cases:
                for spec in tc.evaluation_specs:
                    if spec.sdk == "deepeval":
                        metric_names.append(spec.metric.lower())

        # Remove duplicates while preserving order
        seen: set[str] = set()
        unique_metrics = [m for m in metric_names if m not in seen and not seen.add(m)]  # type: ignore[func-returns-value]

        for metric_name in unique_metrics:
            if metric_name in created_metrics:
                continue

            if not self._metric_registry.supports_metric(metric_name):
                continue

            # Build metric config from test case specs if available
            metric_params = self._extract_metric_params(metric_name, test_cases)
            metric_config = MetricConfig(
                threshold=config.threshold,
                model=self._model,
                include_reason=metric_params.get("include_reason", True),
                strict_mode=metric_params.get("strict_mode", False),
                async_mode=metric_params.get("async_mode", True),
                verbose_mode=metric_params.get("verbose_mode", False),
                extra_params={
                    k: v
                    for k, v in metric_params.items()
                    if k
                    not in {
                        "threshold",
                        "model",
                        "include_reason",
                        "strict_mode",
                        "async_mode",
                        "verbose_mode",
                    }
                },
            )

            try:
                metric = self._metric_registry.create_metric(metric_name, metric_config)
                metrics.append(metric)
                created_metrics.add(metric_name)
            except Exception:
                # Skip metrics that fail to create
                pass

        if not metrics:
            # Default to answer relevancy if no metrics specified
            default_config = MetricConfig(
                threshold=config.threshold,
                model=self._model,
            )
            metrics.append(
                self._metric_registry.create_metric("answer_relevancy", default_config)
            )

        return metrics

    def _extract_metric_params(
        self,
        metric_name: str,
        test_cases: list[EvaluationTestCase] | None,
    ) -> dict[str, Any]:
        """Extract metric params from test case evaluation specs.

        Args:
            metric_name: The metric name to look for.
            test_cases: Test cases with evaluation specs.

        Returns:
            Merged params for the metric.
        """
        if not test_cases:
            return {}

        # Get params from the first test case that has this metric
        for tc in test_cases:
            for spec in tc.evaluation_specs:
                if spec.sdk == "deepeval" and spec.metric == metric_name:
                    return dict(spec.params)

        return {}

    def _convert_results(
        self,
        test_cases: list[EvaluationTestCase],
        results: Any,
        threshold: float,
    ) -> EvaluationResponse:
        """Convert deepeval results to EvaluationResponse.

        Args:
            test_cases: Original test cases.
            results: Deepeval evaluation results.
            threshold: Score threshold for pass/fail.

        Returns:
            The evaluation response.
        """
        details: list[PortTestCaseResult] = []

        # DeepEval's evaluate() returns test_results with metrics_data
        test_results = getattr(results, "test_results", [])

        for i, tc in enumerate(test_cases):
            metric_results: list[PortMetricResult] = []
            overall_score = 0.5
            overall_reason = None

            if i < len(test_results):
                test_result = test_results[i]
                metrics_data = getattr(test_result, "metrics_data", [])

                if metrics_data:
                    scores = []
                    reasons = []
                    for metric_data in metrics_data:
                        metric_name = getattr(metric_data, "name", "unknown")
                        metric_score = getattr(metric_data, "score", 0.5)
                        metric_reason = getattr(metric_data, "reason", None)
                        metric_passed = metric_score >= threshold

                        scores.append(metric_score)
                        if metric_reason:
                            reasons.append(metric_reason)

                        # Extract additional metadata from DeepEval
                        metadata = self._extract_metric_metadata(metric_data)

                        metric_results.append(
                            PortMetricResult(
                                sdk="deepeval",
                                metric=metric_name,
                                score=metric_score,
                                passed=metric_passed,
                                reason=metric_reason,
                                metadata=metadata,
                            )
                        )

                    if scores:
                        overall_score = sum(scores) / len(scores)
                    if reasons:
                        overall_reason = "; ".join(reasons)

            # Fallback if no metrics_data available
            if not metric_results:
                # Use evaluation_specs to create metric results
                for spec in tc.evaluation_specs:
                    if spec.sdk == "deepeval":
                        metric_results.append(
                            PortMetricResult(
                                sdk="deepeval",
                                metric=spec.metric,
                                score=overall_score,
                                passed=overall_score >= threshold,
                                reason=None,
                            )
                        )

            passed = overall_score >= threshold

            details.append(
                PortTestCaseResult(
                    test_case_id=tc.id,
                    score=overall_score,
                    passed=passed,
                    metrics={"overall": overall_score},
                    reason=overall_reason,
                    metric_results=tuple(metric_results),
                )
            )

        return EvaluationResponse.create(tuple(details), threshold)

    def _extract_metric_metadata(self, metric_data: Any) -> dict[str, Any]:
        """Extract additional metadata from DeepEval metric data.

        Args:
            metric_data: DeepEval MetricData object.

        Returns:
            Dictionary of additional metadata fields.
        """
        metadata: dict[str, Any] = {}

        # Common DeepEval metric attributes to extract
        optional_attrs = [
            "threshold",
            "success",
            "strict_mode",
            "evaluation_model",
            "evaluation_cost",
            "verbose_logs",
            "error",
        ]

        for attr in optional_attrs:
            value = getattr(metric_data, attr, None)
            if value is not None:
                metadata[attr] = value

        return metadata

    def _create_metrics_for_names(
        self,
        config: EvaluationConfig,
        metric_names: list[str],
        test_cases: list[EvaluationTestCase],
    ) -> list[Any]:
        """Create deepeval metrics for specific metric names.

        Args:
            config: Evaluation configuration.
            metric_names: List of metric names to create.
            test_cases: Test cases to extract params from.

        Returns:
            List of deepeval metrics.
        """
        metrics = []
        created_metrics: set[str] = set()

        for metric_name in metric_names:
            if metric_name in created_metrics:
                continue

            if not self._metric_registry.supports_metric(metric_name):
                continue

            # Build metric config from test case specs if available
            metric_params = self._extract_metric_params(metric_name, test_cases)
            metric_config = MetricConfig(
                threshold=config.threshold,
                model=self._model,
                include_reason=metric_params.get("include_reason", True),
                strict_mode=metric_params.get("strict_mode", False),
                async_mode=metric_params.get("async_mode", True),
                verbose_mode=metric_params.get("verbose_mode", False),
                extra_params={
                    k: v
                    for k, v in metric_params.items()
                    if k
                    not in {
                        "threshold",
                        "model",
                        "include_reason",
                        "strict_mode",
                        "async_mode",
                        "verbose_mode",
                    }
                },
            )

            try:
                metric = self._metric_registry.create_metric(metric_name, metric_config)
                metrics.append(metric)
                created_metrics.add(metric_name)
            except Exception:
                # Skip metrics that fail to create
                pass

        if not metrics:
            # Default to answer relevancy if no metrics specified
            default_config = MetricConfig(
                threshold=config.threshold,
                model=self._model,
            )
            metrics.append(
                self._metric_registry.create_metric("answer_relevancy", default_config)
            )

        return metrics

    def _convert_grouped_results(
        self,
        all_test_cases: list[EvaluationTestCase],
        all_results: list[Any],
        original_tcs: list[EvaluationTestCase],
        threshold: float,
    ) -> EvaluationResponse:
        """Convert grouped deepeval results to EvaluationResponse.

        Args:
            all_test_cases: All test cases in original order.
            all_results: List of deepeval results from each group.
            original_tcs: Test cases in the order they were evaluated.
            threshold: Score threshold for pass/fail.

        Returns:
            The evaluation response.
        """
        # Build a map of test case id -> result
        result_map: dict[str, PortTestCaseResult] = {}
        tc_index = 0

        for results in all_results:
            test_results = getattr(results, "test_results", [])

            for test_result in test_results:
                if tc_index >= len(original_tcs):
                    break

                tc = original_tcs[tc_index]
                tc_index += 1

                metric_results: list[PortMetricResult] = []
                overall_score = 0.5
                overall_reason = None

                metrics_data = getattr(test_result, "metrics_data", [])

                if metrics_data:
                    scores = []
                    reasons = []
                    for metric_data in metrics_data:
                        metric_name = getattr(metric_data, "name", "unknown")
                        metric_score = getattr(metric_data, "score", 0.5)
                        metric_reason = getattr(metric_data, "reason", None)
                        metric_passed = metric_score >= threshold

                        scores.append(metric_score)
                        if metric_reason:
                            reasons.append(metric_reason)

                        metadata = self._extract_metric_metadata(metric_data)

                        metric_results.append(
                            PortMetricResult(
                                sdk="deepeval",
                                metric=metric_name,
                                score=metric_score,
                                passed=metric_passed,
                                reason=metric_reason,
                                metadata=metadata,
                            )
                        )

                    if scores:
                        overall_score = sum(scores) / len(scores)
                    if reasons:
                        overall_reason = "; ".join(reasons)

                if not metric_results:
                    for spec in tc.evaluation_specs:
                        if spec.sdk == "deepeval":
                            metric_results.append(
                                PortMetricResult(
                                    sdk="deepeval",
                                    metric=spec.metric,
                                    score=overall_score,
                                    passed=overall_score >= threshold,
                                    reason=None,
                                )
                            )

                passed = overall_score >= threshold

                result_map[tc.id] = PortTestCaseResult(
                    test_case_id=tc.id,
                    score=overall_score,
                    passed=passed,
                    metrics={"overall": overall_score},
                    reason=overall_reason,
                    metric_results=tuple(metric_results),
                )

        # Build final results in original order
        details: list[PortTestCaseResult] = []
        for tc in all_test_cases:
            if tc.id in result_map:
                details.append(result_map[tc.id])
            else:
                # Test case was not evaluated (no deepeval specs?)
                details.append(
                    PortTestCaseResult(
                        test_case_id=tc.id,
                        score=0.0,
                        passed=False,
                        metrics={},
                        reason="No evaluation performed",
                    )
                )

        return EvaluationResponse.create(tuple(details), threshold)

    def _mock_evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Mock evaluation when deepeval is not available.

        This is used for testing and when deepeval is not installed.

        Args:
            test_cases: List of test cases.
            config: Evaluation configuration.

        Returns:
            Mock evaluation response.
        """
        details: list[PortTestCaseResult] = []

        for tc in test_cases:
            # Find the first deepeval spec to get params (or use empty params)
            deepeval_spec = next(
                (s for s in tc.evaluation_specs if s.sdk == "deepeval"), None
            )
            resolved_params = (
                self._param_parser.parse(deepeval_spec.params)
                if deepeval_spec
                else DeepEvalResolvedParams()
            )

            # Simple mock scoring based on output length similarity
            expected = resolved_params.expected
            if expected:
                actual_len = len(tc.actual)
                expected_len = len(expected)
                if expected_len > 0:
                    ratio = min(actual_len, expected_len) / max(
                        actual_len, expected_len
                    )
                    score = min(1.0, ratio)
                else:
                    score = 0.5 if actual_len > 0 else 0.0
            else:
                score = 0.5 if tc.actual else 0.0

            passed = score >= config.threshold

            # Create metric results from evaluation_specs
            metric_results: list[PortMetricResult] = []
            for spec in tc.evaluation_specs:
                if spec.sdk == "deepeval":
                    metric_results.append(
                        PortMetricResult(
                            sdk="deepeval",
                            metric=spec.metric,
                            score=score,
                            passed=passed,
                            reason="Mock evaluation result",
                        )
                    )

            details.append(
                PortTestCaseResult(
                    test_case_id=tc.id,
                    score=score,
                    passed=passed,
                    metrics={"mock_score": score},
                    reason="Mock evaluation result",
                    metric_results=tuple(metric_results),
                )
            )

        return EvaluationResponse.create(tuple(details), config.threshold)
