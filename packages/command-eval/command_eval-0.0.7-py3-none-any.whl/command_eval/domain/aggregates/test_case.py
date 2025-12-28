"""TestCase aggregate root.

Manages test case data created from test input and execution result.
SDK-specific fields are stored in evaluation_specs, which Domain layer treats as opaque.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from command_eval.domain.events.test_case_created import TestCaseCreated
from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.ids.test_case_id import TestCaseId
from command_eval.domain.value_objects.ids.test_input_id import TestInputId


@dataclass
class TestCase:
    """Aggregate root for test case management.

    Attributes:
        id: Unique identifier for this test case.
        test_input_id: ID of the related test input.
        input: The actual input text.
        actual: The actual execution result (required).
        execution_time_ms: Execution time in milliseconds.
        evaluation_specs: Evaluation specifications (SDK-independent).
            Domain layer treats this as opaque. Infrastructure layer parses params.
        created_at: When the test case was created.

    Note:
        SDK-specific fields (expected, context, retrieval_context, name, reasoning)
        have been moved to evaluation_specs.params and are parsed by Infrastructure layer.
    """

    id: TestCaseId
    test_input_id: TestInputId
    input: str
    actual: str
    execution_time_ms: int
    evaluation_specs: tuple[EvaluationSpec, ...] = field(default_factory=tuple)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """Validate aggregate invariants."""
        if not self.actual:
            raise ValueError("Actual result is required")
        if self.execution_time_ms < 0:
            raise ValueError("Execution time must be non-negative")

    @classmethod
    def create(
        cls,
        test_input_id: TestInputId,
        input: str,
        actual: str,
        execution_time_ms: int,
        evaluation_specs: tuple[EvaluationSpec, ...] = (),
        is_last_test_case: bool = False,
    ) -> tuple[TestCase, TestCaseCreated]:
        """Create a new TestCase and emit a TestCaseCreated event.

        Args:
            test_input_id: ID of the related test input.
            input: The actual input text.
            actual: The actual execution result.
            execution_time_ms: Execution time in milliseconds.
            evaluation_specs: SDK-independent evaluation specifications.
            is_last_test_case: Whether this is the last test case.

        Returns:
            A tuple of (TestCase, TestCaseCreated event).
        """
        test_case = cls(
            id=TestCaseId.generate(),
            test_input_id=test_input_id,
            input=input,
            actual=actual,
            execution_time_ms=execution_time_ms,
            evaluation_specs=evaluation_specs,
        )

        event = TestCaseCreated(
            test_case_id=test_case.id,
            test_input_id=test_input_id,
            is_last_test_case=is_last_test_case,
        )

        return test_case, event
