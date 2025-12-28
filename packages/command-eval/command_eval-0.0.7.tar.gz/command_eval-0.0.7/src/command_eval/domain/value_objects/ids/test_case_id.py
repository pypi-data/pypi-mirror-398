"""TestCaseId value object.

Unique identifier for test cases.
"""

from dataclasses import dataclass

from command_eval.domain.value_objects.ids.base_id import BaseId


@dataclass(frozen=True)
class TestCaseId(BaseId):
    """Unique identifier for a test case (UUIDv4)."""

    pass
