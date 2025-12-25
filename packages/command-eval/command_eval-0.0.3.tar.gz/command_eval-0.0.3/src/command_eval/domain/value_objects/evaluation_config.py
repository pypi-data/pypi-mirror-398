"""EvaluationConfig value object.

Represents the configuration for an evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvaluationConfig:
    """Value object representing evaluation configuration.

    Attributes:
        threshold: Evaluation threshold (0.0 to 1.0).
        verbose_mode: Whether to output detailed results.
        options: SDK-specific options dictionary.

    Note:
        Metrics are derived from evaluation_specs in test cases (YAML evaluation_list),
        not from this config.
    """

    threshold: float = 0.5
    verbose_mode: bool = False
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
