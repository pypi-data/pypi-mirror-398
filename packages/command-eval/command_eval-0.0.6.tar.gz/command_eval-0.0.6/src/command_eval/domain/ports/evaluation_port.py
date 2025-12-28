"""EvaluationPort interface and related types.

Provides abstraction for LLM evaluation across different SDKs.
SDK-specific fields are stored in evaluation_specs, which Domain layer treats as opaque.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.metric_type import MetricType


@dataclass(frozen=True)
class EvaluationTestCase:
    """SDK-independent test case for evaluation.

    Attributes:
        id: Unique identifier for the test case.
        input: The input query.
        actual: The actual output from command execution.
        execution_time_ms: Execution time in milliseconds.
        evaluation_specs: Evaluation specifications (SDK-independent).
            Domain layer treats this as opaque. Infrastructure layer parses params.

    Note:
        SDK-specific fields (expected, context, retrieval_context, name, reasoning,
        completion_time) have been moved to evaluation_specs.params and are parsed
        by Infrastructure layer adapters.
    """

    id: str
    input: str
    actual: str
    execution_time_ms: int = 0
    evaluation_specs: tuple[EvaluationSpec, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate test case data."""
        if not self.id:
            raise ValueError("Test case ID cannot be empty")
        if not self.input:
            raise ValueError("Test case input cannot be empty")


@dataclass(frozen=True)
class EvaluationConfig:
    """Configuration for evaluation.

    Attributes:
        default_threshold: Default score threshold for pass/fail determination.
            Can be overridden per-metric in YAML evaluation_type.
        verbose_mode: Enable verbose output.
        options: SDK-specific options dictionary.

    Note:
        Metrics are derived from evaluation_specs in test cases, not from config.
    """

    default_threshold: float = 0.5
    verbose_mode: bool = False
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration data."""
        if not 0.0 <= self.default_threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")


@dataclass(frozen=True)
class MetricResult:
    """Result for a single metric evaluation.

    Attributes:
        sdk: SDK name (e.g., "deepeval", "ragas").
        metric: Metric name (e.g., "answer_relevancy").
        score: Metric score (0-1).
        passed: Whether this metric passed.
        reason: Reason for the score (optional).
        metadata: SDK-specific additional data (optional).
            This is a generic container for any SDK-specific data
            that should be passed through to templates without
            Domain layer knowing the specific structure.
    """

    sdk: str
    metric: str
    score: float
    passed: bool
    reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metric result data."""
        if not self.sdk:
            raise ValueError("SDK name cannot be empty")
        if not self.metric:
            raise ValueError("Metric name cannot be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Metric score must be between 0.0 and 1.0")


@dataclass(frozen=True)
class TestCaseResult:
    """Evaluation result for a single test case.

    Attributes:
        test_case_id: ID of the evaluated test case.
        metric_results: Detailed per-metric results with SDK info and reasons.
    """

    test_case_id: str
    metric_results: tuple[MetricResult, ...]

    def __post_init__(self) -> None:
        """Validate result data."""
        if not self.test_case_id:
            raise ValueError("Test case ID cannot be empty")

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


@dataclass(frozen=True)
class EvaluationResponse:
    """Response from evaluation execution.

    Attributes:
        passed_count: Number of passed test cases.
        failed_count: Number of failed test cases.
        total_count: Total number of test cases.
        is_all_passed: Whether all test cases passed.
        details: Detailed results for each test case.
    """

    passed_count: int
    failed_count: int
    total_count: int
    is_all_passed: bool
    details: tuple[TestCaseResult, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate response data."""
        if self.passed_count < 0:
            raise ValueError("Passed count cannot be negative")
        if self.failed_count < 0:
            raise ValueError("Failed count cannot be negative")
        if self.total_count < 0:
            raise ValueError("Total count cannot be negative")
        if self.passed_count + self.failed_count != self.total_count:
            raise ValueError(
                "Passed count + failed count must equal total count"
            )

    @classmethod
    def create(
        cls,
        details: tuple[TestCaseResult, ...],
        threshold: float = 0.5,
    ) -> EvaluationResponse:
        """Create an EvaluationResponse from test case results.

        Args:
            details: Tuple of test case results.
            threshold: Score threshold for pass/fail determination.

        Returns:
            An EvaluationResponse with calculated summary statistics.
        """
        total_count = len(details)
        passed_count = sum(1 for d in details if d.passed)
        failed_count = total_count - passed_count
        is_all_passed = passed_count == total_count and total_count > 0

        return cls(
            passed_count=passed_count,
            failed_count=failed_count,
            total_count=total_count,
            is_all_passed=is_all_passed,
            details=details,
        )


class EvaluationPort(ABC):
    """Abstract interface for LLM evaluation.

    This port provides an abstraction for evaluating LLM outputs,
    allowing different implementations (deepeval, ragas, openeval, etc.).
    """

    @abstractmethod
    def evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Execute evaluation on test cases.

        Args:
            test_cases: List of test cases to evaluate.
            config: Evaluation configuration.

        Returns:
            The evaluation response with results.
        """
        pass

    @abstractmethod
    def get_sdk_name(self) -> str:
        """Get the SDK name for this adapter.

        Returns:
            The name of the evaluation SDK.
        """
        pass

    @abstractmethod
    def supports_metric(self, metric_type: MetricType) -> bool:
        """Check if this adapter supports a specific metric type.

        Args:
            metric_type: The metric type to check.

        Returns:
            True if the metric is supported, False otherwise.
        """
        pass
