"""Execution aggregate root.

Manages command execution and its results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from command_eval.domain.entities.execution_result import ExecutionResult
from command_eval.domain.events.command_executed import CommandExecuted
from command_eval.domain.ports.execution_port import (
    ExecutionPort,
    ExecutionRequest,
)
from command_eval.domain.value_objects.execution_status import ExecutionStatus
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.ids.execution_id import ExecutionId
from command_eval.domain.value_objects.ids.test_input_id import TestInputId


@dataclass
class Execution:
    """Aggregate root for command execution management.

    Attributes:
        id: Unique identifier for this execution.
        test_input_id: ID of the related test input.
        command: The command to execute (including pre-commands).
        output_file: Path for command output.
        status: Current execution status.
        result: Execution result (optional, set after completion).
        started_at: When the execution started.
        completed_at: When the execution completed (optional).
    """

    id: ExecutionId
    test_input_id: TestInputId
    command: str
    output_file: FilePath
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[ExecutionResult] = None
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate aggregate invariants."""
        if not self.command:
            raise ValueError("Command is required")

    @classmethod
    def create(
        cls,
        test_input_id: TestInputId,
        command: str,
        output_file: FilePath,
        pre_command: Optional[str] = None,
    ) -> Execution:
        """Create a new Execution in PENDING state.

        Args:
            test_input_id: ID of the related test input.
            command: The command to execute.
            output_file: Path for command output.
            pre_command: Command to run before main command (optional).

        Returns:
            A new Execution instance.
        """
        full_command = command
        if pre_command:
            full_command = f"{pre_command} && {command}"

        return cls(
            id=ExecutionId.generate(),
            test_input_id=test_input_id,
            command=full_command,
            output_file=output_file,
            status=ExecutionStatus.PENDING,
        )

    def execute(
        self,
        port: ExecutionPort,
        actual_input: str,
    ) -> CommandExecuted:
        """Execute the command using the provided port.

        Args:
            port: The execution port to use.
            actual_input: The actual input text to pass to the command.

        Returns:
            A CommandExecuted event.

        Raises:
            ValueError: If execution has already been completed.
        """
        if self.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
            raise ValueError("Execution has already been completed")

        self.status = ExecutionStatus.RUNNING

        request = ExecutionRequest(
            command=self.command,
            actual_input=actual_input,
            output_file=self.output_file,
        )

        response = port.execute(request)

        self.result = ExecutionResult(
            output=response.output,
            exit_code=response.exit_code,
            execution_time_ms=response.execution_time_ms,
            success=response.success,
            console_output=response.console_output,
        )

        if response.success:
            self.status = ExecutionStatus.COMPLETED
        else:
            self.status = ExecutionStatus.FAILED

        self.completed_at = datetime.now(timezone.utc)

        return CommandExecuted(
            execution_id=self.id,
            test_input_id=self.test_input_id,
            success=response.success,
            output=response.output,
            execution_time_ms=response.execution_time_ms,
            console_output=response.console_output,
        )

    @property
    def is_completed(self) -> bool:
        """Check if execution has completed (success or failure)."""
        return self.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED)

    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == ExecutionStatus.COMPLETED
