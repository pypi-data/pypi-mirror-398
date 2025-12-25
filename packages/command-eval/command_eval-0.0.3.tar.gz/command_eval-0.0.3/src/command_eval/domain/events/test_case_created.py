"""TestCaseCreated domain event.

Indicates that a test case has been created and is ready for evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from command_eval.domain.events.base_event import DomainEvent
from command_eval.domain.value_objects.ids.test_case_id import TestCaseId
from command_eval.domain.value_objects.ids.test_input_id import TestInputId


@dataclass(frozen=True)
class TestCaseCreated(DomainEvent):
    """Event indicating a test case has been created.

    Attributes:
        test_case_id: The ID of the created test case.
        test_input_id: The ID of the related test input.
        is_last_test_case: Whether this is the last test case in the batch.
    """

    EVENT_TYPE: ClassVar[str] = "TestCaseCreated"

    test_case_id: TestCaseId
    test_input_id: TestInputId
    is_last_test_case: bool
