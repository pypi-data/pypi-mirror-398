"""ResultWriterPort interface and related types.

Provides abstraction for writing evaluation results to files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.output_config import OutputConfig


@dataclass(frozen=True)
class ResultWriteRequest:
    """Request data for writing evaluation results.

    Attributes:
        output_config: Configuration for output format and location.
        item_id: Unique identifier for the result item.
        result_data: The evaluation result data to write.
        timestamp_dir: The timestamp directory name (YYYY-MM-DD_HHMMSS).
    """

    output_config: OutputConfig
    item_id: str
    result_data: dict[str, Any]
    timestamp_dir: str

    def __post_init__(self) -> None:
        """Validate request data."""
        if not self.item_id:
            raise ValueError("item_id cannot be empty")
        if not self.timestamp_dir:
            raise ValueError("timestamp_dir cannot be empty")


@dataclass(frozen=True)
class ResultWriteResponse:
    """Response data from writing evaluation results.

    Attributes:
        success: Whether the write was successful.
        output_path: The path where the result was written.
        error_message: Error message if write failed.
    """

    success: bool
    output_path: Optional[FilePath] = None
    error_message: Optional[str] = None

    @classmethod
    def success_response(cls, output_path: FilePath) -> ResultWriteResponse:
        """Create a successful write response.

        Args:
            output_path: The path where the result was written.

        Returns:
            A successful ResultWriteResponse.
        """
        return cls(
            success=True,
            output_path=output_path,
            error_message=None,
        )

    @classmethod
    def failure_response(cls, error_message: str) -> ResultWriteResponse:
        """Create a failed write response.

        Args:
            error_message: The error message.

        Returns:
            A failed ResultWriteResponse.
        """
        return cls(
            success=False,
            output_path=None,
            error_message=error_message,
        )


class ResultWriterPort(ABC):
    """Abstract interface for writing evaluation results.

    This port provides an abstraction for writing evaluation results
    to files using templates (Jinja2).
    """

    @abstractmethod
    def write(self, request: ResultWriteRequest) -> ResultWriteResponse:
        """Write evaluation results to a file.

        Args:
            request: The write request containing result data and configuration.

        Returns:
            The write response with the output path or error.
        """
        pass
