"""DataFileId value object.

Unique identifier for data files.
"""

from dataclasses import dataclass

from command_eval.domain.value_objects.ids.base_id import BaseId


@dataclass(frozen=True)
class DataFileId(BaseId):
    """Unique identifier for a data file (UUIDv4)."""

    pass
