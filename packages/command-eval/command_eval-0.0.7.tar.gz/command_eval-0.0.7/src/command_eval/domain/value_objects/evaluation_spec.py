"""EvaluationSpec value object.

Represents an SDK-independent evaluation specification.
Contains SDK name, metric name, and merged parameters.
Domain layer treats this structure as opaque and does not interpret params.
Infrastructure layer (Adapters) parse params to SDK-specific formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from command_eval.errors import ValidationError


@dataclass(frozen=True)
class EvaluationSpec:
    """Value object representing an evaluation specification.

    An evaluation specification contains:
    - sdk: SDK name (e.g., "deepeval", "ragas")
    - metric: Metric name (e.g., "answer_relevancy", "faithfulness")
    - params: Merged parameters from common_param and metric-specific params

    The params dict is opaque to the Domain layer. Infrastructure layer
    Adapters are responsible for parsing params into SDK-specific formats.
    """

    sdk: str
    metric: str
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the evaluation spec."""
        if not self.sdk:
            raise ValidationError("SDK name cannot be empty")
        if not isinstance(self.sdk, str):
            raise ValidationError(
                f"SDK name must be a string, got {type(self.sdk).__name__}"
            )

        if not self.metric:
            raise ValidationError("Metric name cannot be empty")
        if not isinstance(self.metric, str):
            raise ValidationError(
                f"Metric name must be a string, got {type(self.metric).__name__}"
            )

        if not isinstance(self.params, dict):
            raise ValidationError(
                f"Params must be a dict, got {type(self.params).__name__}"
            )

    def __str__(self) -> str:
        """Return the string representation of the evaluation spec."""
        return f"{self.sdk}:{self.metric}"

    def matches_sdk(self, sdk_name: str) -> bool:
        """Check if this spec matches the given SDK name.

        Args:
            sdk_name: SDK name to match against.

        Returns:
            True if the SDK names match (case-insensitive), False otherwise.
        """
        return self.sdk.lower() == sdk_name.lower()

    def matches_metric(self, metric_name: str) -> bool:
        """Check if this spec matches the given metric name.

        Args:
            metric_name: Metric name to match against.

        Returns:
            True if the metric names match (case-insensitive), False otherwise.
        """
        return self.metric.lower() == metric_name.lower()

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter value by key.

        Args:
            key: Parameter key.
            default: Default value if key not found.

        Returns:
            Parameter value or default.
        """
        return self.params.get(key, default)

    def has_param(self, key: str) -> bool:
        """Check if a parameter exists.

        Args:
            key: Parameter key.

        Returns:
            True if the parameter exists, False otherwise.
        """
        return key in self.params
