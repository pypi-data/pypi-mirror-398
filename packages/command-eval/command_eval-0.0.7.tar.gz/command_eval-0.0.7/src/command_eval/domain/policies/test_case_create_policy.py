"""Test case create policy.

Policy that creates test cases when commands are executed successfully.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from command_eval.domain.aggregates.test_case import TestCase
from command_eval.domain.aggregates.test_input import TestInput
from command_eval.domain.events.command_executed import CommandExecuted
from command_eval.domain.events.test_case_created import TestCaseCreated


@dataclass(frozen=True)
class CreateTestCaseRequest:
    """Request to create a test case.

    Attributes:
        test_input: The test input that was executed.
        event: The CommandExecuted event that triggered this request.
        is_last_test_case: Whether this is the last test case to be created.
    """

    test_input: TestInput
    event: CommandExecuted
    is_last_test_case: bool = False


@dataclass(frozen=True)
class CreateTestCaseResult:
    """Result of creating a test case.

    Attributes:
        test_case: The created test case (None if execution failed).
        event: The event emitted when creating the test case (None if skipped).
        skipped: Whether the test case creation was skipped.
        skip_reason: Reason for skipping (if skipped).
    """

    test_case: Optional[TestCase]
    event: Optional[TestCaseCreated]
    skipped: bool = False
    skip_reason: Optional[str] = None

    @classmethod
    def success(
        cls,
        test_case: TestCase,
        event: TestCaseCreated,
    ) -> CreateTestCaseResult:
        """Create a successful result.

        Args:
            test_case: The created test case.
            event: The emitted event.

        Returns:
            A successful result.
        """
        return cls(test_case=test_case, event=event)

    @classmethod
    def skip(cls, reason: str) -> CreateTestCaseResult:
        """Create a skipped result.

        Args:
            reason: Reason for skipping.

        Returns:
            A skipped result.
        """
        return cls(
            test_case=None,
            event=None,
            skipped=True,
            skip_reason=reason,
        )


class TestCaseCreatePolicy:
    """Policy for creating test cases when commands are executed.

    This policy is responsible for:
    - Receiving a CommandExecuted event
    - Creating a TestCase aggregate if execution was successful
    - Emitting a TestCaseCreated event
    - Skipping test case creation if execution failed
    """

    def execute(self, request: CreateTestCaseRequest) -> CreateTestCaseResult:
        """Execute the test case create policy.

        Args:
            request: The request containing the test input and execution event.

        Returns:
            The result containing the test case and event, or skip info.
        """
        # Skip if execution was not successful
        if not request.event.success:
            return CreateTestCaseResult.skip(
                reason="Execution was not successful"
            )

        # Skip if output is empty
        if not request.event.output:
            return CreateTestCaseResult.skip(
                reason="Execution output is empty"
            )

        # Create test case with evaluation_specs propagated from TestInput
        # SDK-specific params are stored in evaluation_specs and parsed by Infrastructure layer
        test_case, event = TestCase.create(
            test_input_id=request.test_input.id,
            input=request.test_input.actual_input,
            actual=request.event.output,
            execution_time_ms=request.event.execution_time_ms,
            evaluation_specs=request.test_input.evaluation_specs,
            is_last_test_case=request.is_last_test_case,
        )

        return CreateTestCaseResult.success(test_case=test_case, event=event)
