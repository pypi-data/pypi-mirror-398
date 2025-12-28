"""SourceType enumeration.

Represents the source type for query or expected data.
"""

from enum import Enum


class SourceType(Enum):
    """Enumeration representing the source type.

    FILE: Data is read from a file path.
    INLINE: Data is provided inline as text.
    """

    FILE = "file"
    INLINE = "inline"
