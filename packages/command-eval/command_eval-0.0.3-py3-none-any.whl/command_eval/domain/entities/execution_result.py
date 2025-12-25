"""ExecutionResult entity.

Represents the result of a command execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExecutionResult:
    """The result of a command execution.

    Attributes:
        output: The command output content (from output file).
        exit_code: The command exit code.
        execution_time_ms: Execution time in milliseconds.
        success: Whether the execution was successful.
        console_output: Raw console output from PTY/terminal (optional).
    """

    output: str
    exit_code: int
    execution_time_ms: int
    success: bool
    console_output: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate execution result."""
        if self.execution_time_ms < 0:
            raise ValueError("Execution time must be non-negative")

    @classmethod
    def success_result(
        cls,
        output: str,
        exit_code: int,
        execution_time_ms: int,
        console_output: Optional[str] = None,
    ) -> ExecutionResult:
        """Create a successful execution result.

        Args:
            output: The command output.
            exit_code: The exit code.
            execution_time_ms: The execution time in milliseconds.
            console_output: Raw console output from PTY/terminal.

        Returns:
            An ExecutionResult with success=True.
        """
        return cls(
            output=output,
            exit_code=exit_code,
            execution_time_ms=execution_time_ms,
            success=True,
            console_output=console_output,
        )

    @classmethod
    def failure_result(
        cls,
        output: str,
        exit_code: int,
        execution_time_ms: int,
        console_output: Optional[str] = None,
    ) -> ExecutionResult:
        """Create a failed execution result.

        Args:
            output: The command output (may include error messages).
            exit_code: The exit code.
            execution_time_ms: The execution time in milliseconds.
            console_output: Raw console output from PTY/terminal.

        Returns:
            An ExecutionResult with success=False.
        """
        return cls(
            output=output,
            exit_code=exit_code,
            execution_time_ms=execution_time_ms,
            success=False,
            console_output=console_output,
        )
