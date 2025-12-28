"""CommandExecuted domain event.

Indicates that a command has been executed and the result is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Optional

from command_eval.domain.events.base_event import DomainEvent
from command_eval.domain.value_objects.ids.execution_id import ExecutionId
from command_eval.domain.value_objects.ids.test_input_id import TestInputId


@dataclass(frozen=True)
class CommandExecuted(DomainEvent):
    """Event indicating a command has been executed.

    Attributes:
        execution_id: The ID of the execution.
        test_input_id: The ID of the related test input.
        success: Whether the execution was successful.
        output: The command output (on success).
        execution_time_ms: The execution time in milliseconds.
        console_output: Raw console output from PTY/terminal (optional).
    """

    EVENT_TYPE: ClassVar[str] = "CommandExecuted"

    execution_id: ExecutionId
    test_input_id: TestInputId
    success: bool
    output: str
    execution_time_ms: int
    console_output: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate event data."""
        if self.execution_time_ms < 0:
            raise ValueError("Execution time cannot be negative")
