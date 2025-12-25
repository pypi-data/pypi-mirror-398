"""MetricType value object.

Represents a metric type identifier for evaluation.
SDK-independent string identifier.
"""

from __future__ import annotations

from dataclasses import dataclass

from command_eval.errors import ValidationError


@dataclass(frozen=True)
class MetricType:
    """Value object representing a metric type.

    A metric type is a string identifier that is SDK-independent.
    Examples: "answer_relevancy", "faithfulness", "context_precision".
    """

    value: str

    def __post_init__(self) -> None:
        """Validate the metric type value."""
        if not self.value:
            raise ValidationError("Metric type value cannot be empty")
        if not isinstance(self.value, str):
            raise ValidationError(
                f"Metric type must be a string, got {type(self.value).__name__}"
            )
        if not self.value.replace("_", "").replace("-", "").isalnum():
            raise ValidationError(
                f"Metric type must contain only alphanumeric characters, "
                f"underscores, and hyphens: {self.value}"
            )

    def __str__(self) -> str:
        """Return the string representation of the metric type."""
        return self.value

    def matches(self, other: str | MetricType) -> bool:
        """Check if this metric type matches another.

        Args:
            other: A string or MetricType to compare.

        Returns:
            True if the values match (case-insensitive), False otherwise.
        """
        other_value = str(other) if isinstance(other, MetricType) else other
        return self.value.lower() == other_value.lower()
