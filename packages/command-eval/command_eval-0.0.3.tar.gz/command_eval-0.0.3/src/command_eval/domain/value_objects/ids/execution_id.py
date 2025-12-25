"""ExecutionId value object.

Unique identifier for command executions.
"""

from dataclasses import dataclass

from command_eval.domain.value_objects.ids.base_id import BaseId


@dataclass(frozen=True)
class ExecutionId(BaseId):
    """Unique identifier for a command execution (UUIDv4)."""

    pass
