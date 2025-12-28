"""EvaluationCompleted domain event.

Indicates that an evaluation has completed and results are available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from command_eval.domain.events.base_event import DomainEvent
from command_eval.domain.value_objects.ids.evaluation_id import EvaluationId


@dataclass(frozen=True)
class EvaluationCompleted(DomainEvent):
    """Event indicating an evaluation has completed.

    Attributes:
        evaluation_id: The ID of the completed evaluation.
        passed_count: The number of passed test cases.
        failed_count: The number of failed test cases.
        total_count: The total number of test cases.
        is_all_passed: Whether all test cases passed.
    """

    EVENT_TYPE: ClassVar[str] = "EvaluationCompleted"

    evaluation_id: EvaluationId
    passed_count: int
    failed_count: int
    total_count: int
    is_all_passed: bool

    def __post_init__(self) -> None:
        """Validate event data."""
        if self.passed_count < 0:
            raise ValueError("Passed count cannot be negative")
        if self.failed_count < 0:
            raise ValueError("Failed count cannot be negative")
        if self.total_count < 0:
            raise ValueError("Total count cannot be negative")
        if self.passed_count + self.failed_count != self.total_count:
            raise ValueError(
                "Passed count + failed count must equal total count"
            )
