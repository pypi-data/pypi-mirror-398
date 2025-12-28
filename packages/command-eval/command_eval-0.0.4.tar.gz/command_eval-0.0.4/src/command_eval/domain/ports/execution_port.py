"""ExecutionPort interface and related types.

Provides abstraction for command execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from command_eval.domain.value_objects.file_path import FilePath


@dataclass(frozen=True)
class ExecutionRequest:
    """Request data for command execution.

    Attributes:
        command: The command to execute.
        query: The query text to pass to the command.
        output_file: The file path where output should be written.
        pre_commands: Commands to run before the main command.
        timeout_ms: Timeout in milliseconds.
        working_directory: Working directory for command execution.
    """

    command: str
    query: str
    output_file: FilePath
    pre_commands: tuple[str, ...] = field(default_factory=tuple)
    timeout_ms: int = 300000  # 5 minutes default
    working_directory: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate request data."""
        if not self.command:
            raise ValueError("Command cannot be empty")
        if self.timeout_ms <= 0:
            raise ValueError("Timeout must be positive")


@dataclass(frozen=True)
class ExecutionResponse:
    """Response data from command execution.

    Attributes:
        output: The captured output from the command (from output file).
        exit_code: The exit code of the command.
        execution_time_ms: Time taken to execute in milliseconds.
        success: Whether the execution was successful.
        error_message: Error message if execution failed.
        console_output: Raw console output from PTY/terminal (optional).
    """

    output: str
    exit_code: int
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None
    console_output: Optional[str] = None

    @classmethod
    def success_response(
        cls,
        output: str,
        exit_code: int,
        execution_time_ms: int,
        console_output: Optional[str] = None,
    ) -> ExecutionResponse:
        """Create a successful execution response.

        Args:
            output: The captured output.
            exit_code: The exit code.
            execution_time_ms: Execution time in milliseconds.
            console_output: Raw console output from PTY/terminal.

        Returns:
            A successful ExecutionResponse.
        """
        return cls(
            output=output,
            exit_code=exit_code,
            execution_time_ms=execution_time_ms,
            success=True,
            error_message=None,
            console_output=console_output,
        )

    @classmethod
    def failure_response(
        cls,
        error_message: str,
        exit_code: int = -1,
        execution_time_ms: int = 0,
        output: str = "",
        console_output: Optional[str] = None,
    ) -> ExecutionResponse:
        """Create a failed execution response.

        Args:
            error_message: The error message.
            exit_code: The exit code (defaults to -1).
            execution_time_ms: Execution time in milliseconds.
            output: Any captured output.
            console_output: Raw console output from PTY/terminal.

        Returns:
            A failed ExecutionResponse.
        """
        return cls(
            output=output,
            exit_code=exit_code,
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=error_message,
            console_output=console_output,
        )


class ExecutionPort(ABC):
    """Abstract interface for command execution.

    This port provides an abstraction for executing CLI commands,
    allowing different implementations (PTY, subprocess, etc.).
    """

    @abstractmethod
    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute a command.

        Args:
            request: The execution request containing command details.

        Returns:
            The execution response with results.
        """
        pass
