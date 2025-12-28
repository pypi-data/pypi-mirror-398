"""EvaluationResult entity.

Represents the overall evaluation result.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from command_eval.domain.entities.test_case_result import TestCaseResult


@dataclass(frozen=True)
class EvaluationResult:
    """The overall evaluation result.

    Attributes:
        passed_count: Number of passed test cases.
        failed_count: Number of failed test cases.
        total_count: Total number of test cases.
        is_all_passed: Whether all test cases passed.
        details: List of individual test case results.
    """

    passed_count: int
    failed_count: int
    total_count: int
    is_all_passed: bool
    details: tuple[TestCaseResult, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate evaluation result."""
        if self.passed_count < 0:
            raise ValueError("Passed count cannot be negative")
        if self.failed_count < 0:
            raise ValueError("Failed count cannot be negative")
        if self.total_count < 0:
            raise ValueError("Total count cannot be negative")
        if self.passed_count + self.failed_count != self.total_count:
            raise ValueError("Passed count + failed count must equal total count")

    @classmethod
    def from_test_case_results(
        cls,
        results: tuple[TestCaseResult, ...],
    ) -> EvaluationResult:
        """Create an EvaluationResult from test case results.

        Args:
            results: Tuple of test case results.

        Returns:
            A new EvaluationResult instance.
        """
        if not results:
            raise ValueError("At least one test case result is required")

        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count
        total_count = len(results)
        is_all_passed = failed_count == 0

        return cls(
            passed_count=passed_count,
            failed_count=failed_count,
            total_count=total_count,
            is_all_passed=is_all_passed,
            details=results,
        )

    @property
    def pass_rate(self) -> float:
        """Get the pass rate as a percentage.

        Returns:
            The pass rate (0.0 to 1.0).
        """
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count
