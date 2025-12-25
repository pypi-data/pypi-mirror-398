"""MetricResult entity.

Represents the evaluation result for a single metric.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class MetricResult:
    """The evaluation result for a single metric.

    Attributes:
        sdk: SDK name (e.g., "deepeval", "ragas").
        metric: Metric name (e.g., "answer_relevancy").
        score: The metric score (0.0 to 1.0).
        passed: Whether this metric passed.
        reason: Reason for the score (optional).
        metadata: SDK-specific additional data (optional).
            This is a generic container for any SDK-specific data
            that should be passed through to templates without
            Domain layer knowing the specific structure.
    """

    sdk: str
    metric: str
    score: float
    passed: bool
    reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metric result."""
        if not self.sdk:
            raise ValueError("SDK name cannot be empty")
        if not self.metric:
            raise ValueError("Metric name cannot be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
