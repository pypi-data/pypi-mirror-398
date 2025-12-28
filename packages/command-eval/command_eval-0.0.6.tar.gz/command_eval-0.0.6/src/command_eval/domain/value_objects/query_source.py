"""QuerySource value object.

Represents the source of a query (file path or inline text).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.source_type import SourceType
from command_eval.errors import ValidationError


@dataclass(frozen=True)
class QuerySource:
    """Value object representing the source of a query.

    The query can come from either a file (FILE) or inline text (INLINE).
    """

    source_type: SourceType
    value: str

    def __post_init__(self) -> None:
        """Validate the query source."""
        if not self.value:
            raise ValidationError("Query source value cannot be empty")
        if not isinstance(self.source_type, SourceType):
            raise ValidationError(
                f"source_type must be a SourceType, got {type(self.source_type).__name__}"
            )

    @classmethod
    def from_file(cls, file_path: str | FilePath) -> QuerySource:
        """Create a QuerySource from a file path.

        Args:
            file_path: The path to the file containing the query.

        Returns:
            A new QuerySource with FILE source type.
        """
        path_value = str(file_path) if isinstance(file_path, FilePath) else file_path
        return cls(source_type=SourceType.FILE, value=path_value)

    @classmethod
    def from_inline(cls, text: str) -> QuerySource:
        """Create a QuerySource from inline text.

        Args:
            text: The inline query text.

        Returns:
            A new QuerySource with INLINE source type.
        """
        return cls(source_type=SourceType.INLINE, value=text)

    def is_file(self) -> bool:
        """Check if the source is a file.

        Returns:
            True if source type is FILE, False otherwise.
        """
        return self.source_type == SourceType.FILE

    def is_inline(self) -> bool:
        """Check if the source is inline text.

        Returns:
            True if source type is INLINE, False otherwise.
        """
        return self.source_type == SourceType.INLINE

    def get_file_path(self) -> Optional[FilePath]:
        """Get the file path if source type is FILE.

        Returns:
            FilePath if source type is FILE, None otherwise.
        """
        if self.is_file():
            return FilePath(self.value)
        return None

    def get_content(self) -> str:
        """Get the content value.

        For FILE source type, this returns the file path string.
        For INLINE source type, this returns the inline text.

        Returns:
            The value string.
        """
        return self.value
