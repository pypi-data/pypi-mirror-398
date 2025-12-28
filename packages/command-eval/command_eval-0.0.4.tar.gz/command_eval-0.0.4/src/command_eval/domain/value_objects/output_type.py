"""OutputType enumeration.

Represents the output format type for evaluation results.
"""

from enum import Enum


class OutputType(Enum):
    """Enumeration representing the output format type.

    TXT: Plain text format.
    JSON: JSON format.
    MARKDOWN: Markdown format.
    """

    TXT = "txt"
    JSON = "json"
    MARKDOWN = "markdown"
