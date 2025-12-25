"""EvaluationStatus enumeration.

Represents the evaluation status of a test case set.
"""

from enum import Enum


class EvaluationStatus(Enum):
    """Enumeration representing the evaluation status.

    PENDING: Waiting to evaluate.
    RUNNING: Currently evaluating.
    COMPLETED: Evaluation completed successfully.
    FAILED: Evaluation failed.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
