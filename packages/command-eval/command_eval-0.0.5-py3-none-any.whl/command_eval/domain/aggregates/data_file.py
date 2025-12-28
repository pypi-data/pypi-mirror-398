"""DataFile aggregate root.

Manages a collection of data items loaded from a YAML/JSON file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from command_eval.domain.entities.data_item import DataItem
from command_eval.domain.events.data_file_loaded import DataFileLoaded
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.ids.data_file_id import DataFileId
from command_eval.domain.value_objects.output_config import OutputConfig


@dataclass
class DataFile:
    """Aggregate root for data file management.

    Attributes:
        id: Unique identifier for this data file.
        file_path: Path to the data file.
        items: Tuple of data items in the file.
        output_config: Optional output configuration for result files.
        created_at: When the data file was loaded.
    """

    id: DataFileId
    file_path: FilePath
    items: tuple[DataItem, ...] = field(default_factory=tuple)
    output_config: OutputConfig | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """Validate aggregate invariants."""
        self._validate_items()
        self._validate_file_path()

    def _validate_items(self) -> None:
        """Validate that there is at least one data item."""
        if not self.items:
            raise ValueError("Data file must contain at least one data item")

    def _validate_file_path(self) -> None:
        """Validate the file path extension."""
        extension = self.file_path.get_extension()
        if extension not in (".yaml", ".yml", ".json"):
            raise ValueError(
                f"Unsupported file format: {extension}. "
                "Supported formats: .yaml, .yml, .json"
            )

    @classmethod
    def create(
        cls,
        file_path: FilePath,
        items: tuple[DataItem, ...],
        output_config: OutputConfig | None = None,
    ) -> tuple[DataFile, DataFileLoaded]:
        """Create a new DataFile and emit a DataFileLoaded event.

        Args:
            file_path: Path to the data file.
            items: Tuple of data items from the file.
            output_config: Optional output configuration for result files.

        Returns:
            A tuple of (DataFile, DataFileLoaded event).
        """
        data_file = cls(
            id=DataFileId.generate(),
            file_path=file_path,
            items=items,
            output_config=output_config,
        )

        event = DataFileLoaded(
            data_file_id=data_file.id,
            file_path=data_file.file_path,
            item_count=len(data_file.items),
        )

        return data_file, event

    @property
    def item_count(self) -> int:
        """Get the number of data items.

        Returns:
            The count of data items.
        """
        return len(self.items)

    def get_item(self, index: int) -> DataItem:
        """Get a data item by index.

        Args:
            index: The index of the item to retrieve.

        Returns:
            The data item at the given index.

        Raises:
            IndexError: If the index is out of bounds.
        """
        if index < 0 or index >= len(self.items):
            raise IndexError(f"Index {index} out of bounds (0-{len(self.items) - 1})")
        return self.items[index]
