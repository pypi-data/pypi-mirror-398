"""Command execution policy.

Policy that executes commands when test inputs are built.
"""

from __future__ import annotations

from dataclasses import dataclass

from command_eval.domain.aggregates.execution import Execution
from command_eval.domain.aggregates.test_input import TestInput
from command_eval.domain.events.command_executed import CommandExecuted
from command_eval.domain.events.test_input_built import TestInputBuilt
from command_eval.domain.ports.execution_port import ExecutionPort


@dataclass(frozen=True)
class ExecuteCommandRequest:
    """Request to execute a command for a test input.

    Attributes:
        test_input: The test input to execute.
        event: The TestInputBuilt event that triggered this request.
    """

    test_input: TestInput
    event: TestInputBuilt


@dataclass(frozen=True)
class ExecuteCommandResult:
    """Result of executing a command.

    Attributes:
        execution: The execution aggregate.
        event: The CommandExecuted event.
    """

    execution: Execution
    event: CommandExecuted


class CommandExecutionPolicy:
    """Policy for executing commands when test inputs are built.

    This policy is responsible for:
    - Receiving a TestInputBuilt event
    - Creating an Execution aggregate
    - Executing the command using the ExecutionPort
    - Emitting a CommandExecuted event
    """

    def __init__(self, execution_port: ExecutionPort) -> None:
        """Initialize the policy.

        Args:
            execution_port: Port for executing commands.
        """
        self._execution_port = execution_port

    def execute(self, request: ExecuteCommandRequest) -> ExecuteCommandResult:
        """Execute the command execution policy.

        Args:
            request: The request containing the test input and event.

        Returns:
            The result containing the execution and event.
        """
        # Create execution aggregate
        execution = Execution.create(
            test_input_id=request.test_input.id,
            command=request.test_input.command,
            output_file=request.test_input.actual_file,
            pre_command=request.test_input.pre_command,
        )

        # Execute the command
        event = execution.execute(
            port=self._execution_port,
            query=request.test_input.query,
        )

        return ExecuteCommandResult(execution=execution, event=event)
