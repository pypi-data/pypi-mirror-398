"""Result output policy.

Policy that outputs evaluation results to files and stdout.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from command_eval.domain.ports.result_writer_port import (
    ResultWriteRequest,
    ResultWriteResponse,
    ResultWriterPort,
)
from command_eval.domain.value_objects.output_config import OutputConfig


@dataclass(frozen=True)
class OutputResultRequest:
    """Request to output evaluation results.

    Attributes:
        output_config: Configuration for output format and location.
        item_id: Unique identifier for the result item.
        result_data: The evaluation result data to write.
        timestamp_dir: Optional timestamp directory name.
            If not provided, will be generated as YYYY-MM-DD_HHMMSS.
    """

    output_config: OutputConfig
    item_id: str
    result_data: dict[str, Any]
    timestamp_dir: Optional[str] = None

    def get_timestamp_dir(self) -> str:
        """Get the timestamp directory name.

        Returns:
            The timestamp directory name.
        """
        if self.timestamp_dir:
            return self.timestamp_dir
        return datetime.now().strftime("%Y-%m-%d_%H%M%S")


@dataclass(frozen=True)
class OutputResultResult:
    """Result of outputting evaluation results.

    Attributes:
        write_response: Response from the result writer.
        stdout_output: The content that was written to stdout.
    """

    write_response: ResultWriteResponse
    stdout_output: str


class ResultOutputPolicy:
    """Policy for outputting evaluation results.

    This policy is responsible for:
    - Writing evaluation results to files using templates
    - Printing results to stdout
    """

    def __init__(
        self,
        result_writer: ResultWriterPort,
    ) -> None:
        """Initialize the policy.

        Args:
            result_writer: Port for writing results to files.
        """
        self._result_writer = result_writer

    def execute(self, request: OutputResultRequest) -> OutputResultResult:
        """Execute the result output policy.

        Args:
            request: The request containing result data and configuration.

        Returns:
            The result containing write response and stdout output.
        """
        # Get timestamp directory
        timestamp_dir = request.get_timestamp_dir()

        # Create write request
        write_request = ResultWriteRequest(
            output_config=request.output_config,
            item_id=request.item_id,
            result_data=request.result_data,
            timestamp_dir=timestamp_dir,
        )

        # Write to file
        write_response = self._result_writer.write(write_request)

        # Generate stdout output
        stdout_output = self._generate_stdout_output(request, write_response)

        return OutputResultResult(
            write_response=write_response,
            stdout_output=stdout_output,
        )

    def _generate_stdout_output(
        self,
        request: OutputResultRequest,
        write_response: ResultWriteResponse,
    ) -> str:
        """Generate the stdout output.

        Args:
            request: The output request.
            write_response: The write response.

        Returns:
            The stdout output string.
        """
        lines = []
        lines.append(f"Item: {request.item_id}")

        if write_response.success and write_response.output_path:
            lines.append(f"Output: {write_response.output_path.value}")
        elif not write_response.success:
            lines.append(f"Error: {write_response.error_message}")

        # Add evaluation results summary if available
        if "evaluation_results" in request.result_data:
            results = request.result_data["evaluation_results"]
            for result in results:
                sdk = result.get("sdk", "unknown")
                metric = result.get("metric", "unknown")
                score = result.get("score", "N/A")
                lines.append(f"  - {sdk}:{metric} = {score}")

        return "\n".join(lines)
