"""Subprocess-based command execution adapter.

Uses subprocess module for simple command execution.
"""

from __future__ import annotations

import subprocess
import time

from command_eval.domain.ports.execution_port import (
    ExecutionPort,
    ExecutionRequest,
    ExecutionResponse,
)


class SubprocessExecutionAdapter(ExecutionPort):
    """Subprocess-based implementation of ExecutionPort.

    Uses Python's subprocess module for simple command execution.
    This is a simpler alternative to PTY for non-interactive commands.
    """

    def __init__(
        self,
        shell: str = "/bin/bash",
    ) -> None:
        """Initialize the subprocess execution adapter.

        Args:
            shell: Shell to use for command execution.
        """
        self._shell = shell

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute a command using subprocess.

        Args:
            request: The execution request containing command details.

        Returns:
            The execution response with results.
        """
        start_time = time.time()

        try:
            timeout_seconds = request.timeout_ms / 1000

            # Prepare stdin input (actual_input text)
            stdin_input = request.actual_input.encode("utf-8") if request.actual_input else None

            # Execute command with actual_input passed to stdin
            process = subprocess.run(
                [self._shell, "-c", request.command],
                input=stdin_input,
                capture_output=True,
                timeout=timeout_seconds,
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Read output file
            output = self._read_output_file(request.output_file.value)

            return ExecutionResponse(
                output=output,
                exit_code=process.returncode,
                execution_time_ms=execution_time_ms,
                success=(process.returncode == 0),
            )

        except subprocess.TimeoutExpired:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return ExecutionResponse.failure_response(
                error_message="Command execution timed out",
                exit_code=-1,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return ExecutionResponse.failure_response(
                error_message=str(e),
                exit_code=-1,
                execution_time_ms=execution_time_ms,
            )

    def _read_output_file(self, file_path: str) -> str:
        """Read the output file content.

        Args:
            file_path: Path to the output file.

        Returns:
            The file content, or empty string if file doesn't exist.
        """
        from pathlib import Path

        path = Path(file_path)
        if not path.exists():
            return ""

        return path.read_text(encoding="utf-8")
