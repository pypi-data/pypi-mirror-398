"""EvaluationId value object.

Unique identifier for evaluations.
"""

from dataclasses import dataclass

from command_eval.domain.value_objects.ids.base_id import BaseId


@dataclass(frozen=True)
class EvaluationId(BaseId):
    """Unique identifier for an evaluation (UUIDv4)."""

    pass
