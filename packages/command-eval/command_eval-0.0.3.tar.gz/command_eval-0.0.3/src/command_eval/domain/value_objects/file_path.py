"""FilePath value object.

Represents a file path with validation and utility methods.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from command_eval.errors import ValidationError


@dataclass(frozen=True)
class FilePath:
    """Value object representing a file path.

    Provides methods for path validation, existence checking,
    and extension extraction.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate the file path value."""
        if not self.value:
            raise ValidationError("File path cannot be empty")
        if not isinstance(self.value, str):
            raise ValidationError(
                f"File path must be a string, got {type(self.value).__name__}"
            )

    def exists(self) -> bool:
        """Check if the file exists.

        Returns:
            True if the file exists, False otherwise.
        """
        return os.path.exists(self.value)

    def is_file(self) -> bool:
        """Check if the path points to a file.

        Returns:
            True if the path is a file, False otherwise.
        """
        return os.path.isfile(self.value)

    def is_directory(self) -> bool:
        """Check if the path points to a directory.

        Returns:
            True if the path is a directory, False otherwise.
        """
        return os.path.isdir(self.value)

    def get_extension(self) -> str:
        """Get the file extension.

        Returns:
            The file extension including the dot (e.g., '.yaml').
            Returns empty string if no extension.
        """
        return Path(self.value).suffix

    def get_extensions(self) -> str:
        """Get all file extensions (for files like .tar.gz).

        Returns:
            All file extensions (e.g., '.tar.gz').
        """
        return "".join(Path(self.value).suffixes)

    def get_filename(self) -> str:
        """Get the filename without directory path.

        Returns:
            The filename including extension.
        """
        return os.path.basename(self.value)

    def get_stem(self) -> str:
        """Get the filename without extension.

        Returns:
            The filename without the last extension.
        """
        return Path(self.value).stem

    def get_parent(self) -> FilePath:
        """Get the parent directory path.

        Returns:
            A new FilePath representing the parent directory.
        """
        parent = os.path.dirname(self.value)
        return FilePath(parent if parent else ".")

    def join(self, *parts: str) -> FilePath:
        """Join path parts to this path.

        Args:
            *parts: Path parts to join.

        Returns:
            A new FilePath with the joined path.
        """
        return FilePath(os.path.join(self.value, *parts))

    def is_absolute(self) -> bool:
        """Check if the path is absolute.

        Returns:
            True if the path is absolute, False otherwise.
        """
        return os.path.isabs(self.value)

    def to_absolute(self) -> FilePath:
        """Convert to absolute path.

        Returns:
            A new FilePath with the absolute path.
        """
        return FilePath(os.path.abspath(self.value))

    def __str__(self) -> str:
        """Return the string representation of the path."""
        return self.value
