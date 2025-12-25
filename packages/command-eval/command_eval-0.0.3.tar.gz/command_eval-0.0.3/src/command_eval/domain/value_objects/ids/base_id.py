"""Base ID value object.

Provides common functionality for all ID value objects.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TypeVar

from command_eval.errors import ValidationError

T = TypeVar("T", bound="BaseId")


@dataclass(frozen=True)
class BaseId:
    """Base class for ID value objects.

    All IDs are UUIDv4 format strings.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate the ID value."""
        if not self.value:
            raise ValidationError(f"{self.__class__.__name__} value cannot be empty")
        try:
            uuid.UUID(self.value, version=4)
        except ValueError as e:
            raise ValidationError(
                f"{self.__class__.__name__} must be a valid UUIDv4: {self.value}"
            ) from e

    @classmethod
    def generate(cls: type[T]) -> T:
        """Generate a new ID with a random UUIDv4.

        Returns:
            A new ID instance with a generated UUIDv4.
        """
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls: type[T], value: str) -> T:
        """Create an ID from a string value.

        Args:
            value: The UUID string value.

        Returns:
            A new ID instance.

        Raises:
            ValidationError: If the value is not a valid UUIDv4.
        """
        return cls(value=value)

    def __str__(self) -> str:
        """Return the string representation of the ID."""
        return self.value
