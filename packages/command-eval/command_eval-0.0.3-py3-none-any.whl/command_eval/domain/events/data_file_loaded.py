"""DataFileLoaded domain event.

Indicates that a data file has been loaded and is ready for test input construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from command_eval.domain.events.base_event import DomainEvent
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.ids.data_file_id import DataFileId


@dataclass(frozen=True)
class DataFileLoaded(DomainEvent):
    """Event indicating a data file has been loaded.

    Attributes:
        data_file_id: The ID of the loaded data file.
        file_path: The path of the loaded file.
        item_count: The number of data items in the file.
    """

    EVENT_TYPE: ClassVar[str] = "DataFileLoaded"

    data_file_id: DataFileId
    file_path: FilePath
    item_count: int

    def __post_init__(self) -> None:
        """Validate event data."""
        if self.item_count < 1:
            raise ValueError("Item count must be at least 1")
