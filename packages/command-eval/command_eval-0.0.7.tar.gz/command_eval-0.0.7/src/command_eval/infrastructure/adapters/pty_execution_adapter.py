"""PTY-based command execution adapter.

Uses PTY (pseudo-terminal) for interactive command execution,
equivalent to LLM_Eval's BC2 implementation.
"""

from __future__ import annotations

import os
import pty
import select
import signal
import subprocess
import time
from typing import Callable, Optional

from command_eval.domain.ports.execution_port import (
    ExecutionPort,
    ExecutionRequest,
    ExecutionResponse,
)


class PtyExecutionAdapter(ExecutionPort):
    """PTY-based implementation of ExecutionPort.

    Uses pseudo-terminal for interactive command execution,
    allowing proper stdin/stdout handling for CLI applications
    that expect terminal input.

    This is equivalent to LLM_Eval's combination of:
    - PythonPTYAdapter (PTY management)
    - SubprocessAdapter (process management)
    - SelectStreamAdapter (stream reading)
    """

    def __init__(
        self,
        shell: str = "/bin/bash",
        pty_rows: int = 24,
        pty_cols: int = 80,
        stream_timeout: float = 0.5,
        on_output_callback: Optional[Callable[[bytes], None]] = None,
    ) -> None:
        """Initialize the PTY execution adapter.

        Args:
            shell: Shell to use for command execution.
            pty_rows: Number of rows for PTY size.
            pty_cols: Number of columns for PTY size.
            stream_timeout: Timeout for stream read operations.
            on_output_callback: Optional callback for streaming output.
        """
        self._shell = shell
        self._pty_rows = pty_rows
        self._pty_cols = pty_cols
        self._stream_timeout = stream_timeout
        self._on_output_callback = on_output_callback

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute a command using PTY.

        Args:
            request: The execution request containing command details.

        Returns:
            The execution response with results.
        """
        start_time = time.time()
        master_fd: Optional[int] = None
        process: Optional[subprocess.Popen] = None

        try:
            timeout_seconds = request.timeout_ms / 1000

            # Open PTY
            master_fd, slave_fd = pty.openpty()

            # Build full command with input
            # Equivalent to LLM_Eval: f"{command} '{input}'"
            full_command = f"{request.command} '{request.actual_input}'"

            # Start process with PTY
            process = subprocess.Popen(
                full_command,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                shell=True,
                start_new_session=True,
            )

            # Close slave in parent (child owns it now)
            os.close(slave_fd)

            # Stream output until process completes or timeout
            output_chunks: list[bytes] = []
            deadline = time.time() + timeout_seconds

            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    # Timeout - kill process
                    self._terminate_process(process)
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    console_output = self._decode_output_chunks(output_chunks)
                    return ExecutionResponse.failure_response(
                        error_message="Command execution timed out",
                        exit_code=-1,
                        execution_time_ms=execution_time_ms,
                        console_output=console_output,
                    )

                # Check if data available
                try:
                    readable, _, _ = select.select(
                        [master_fd], [], [], min(self._stream_timeout, remaining)
                    )
                except (OSError, ValueError):
                    break

                if readable:
                    try:
                        data = os.read(master_fd, 4096)
                        if not data:
                            # EOF
                            break
                        output_chunks.append(data)
                        if self._on_output_callback:
                            self._on_output_callback(data)
                    except OSError:
                        break
                else:
                    # No data available, check if process terminated
                    exit_code = process.poll()
                    if exit_code is not None:
                        break

            # Wait for process to fully complete
            try:
                exit_code = process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self._terminate_process(process)
                exit_code = -1

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Read output file
            output = self._read_output_file(request.output_file.value)

            # Decode console output from PTY
            console_output = self._decode_output_chunks(output_chunks)

            success = exit_code == 0
            error_message = (
                None if success else f"Command exited with code {exit_code}"
            )

            return ExecutionResponse(
                output=output,
                exit_code=exit_code,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message,
                console_output=console_output,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return ExecutionResponse.failure_response(
                error_message=str(e),
                exit_code=-1,
                execution_time_ms=execution_time_ms,
            )

        finally:
            # Cleanup
            if master_fd is not None:
                try:
                    os.close(master_fd)
                except OSError:
                    pass
            if process is not None:
                try:
                    process.kill()
                except (OSError, ProcessLookupError):
                    pass

    def _terminate_process(self, process: subprocess.Popen) -> None:
        """Terminate a process and its process group.

        Args:
            process: The process to terminate.
        """
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass

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

    def _decode_output_chunks(self, output_chunks: list[bytes]) -> str:
        """Decode output chunks from PTY to string.

        Args:
            output_chunks: List of byte chunks from PTY output.

        Returns:
            Decoded string output.
        """
        if not output_chunks:
            return ""

        raw_output = b"".join(output_chunks)
        try:
            return raw_output.decode("utf-8", errors="replace")
        except Exception:
            return raw_output.decode("latin-1", errors="replace")
