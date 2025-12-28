"""TestInputId value object.

Unique identifier for test inputs.
"""

from dataclasses import dataclass

from command_eval.domain.value_objects.ids.base_id import BaseId


@dataclass(frozen=True)
class TestInputId(BaseId):
    """Unique identifier for a test input (UUIDv4)."""

    pass
