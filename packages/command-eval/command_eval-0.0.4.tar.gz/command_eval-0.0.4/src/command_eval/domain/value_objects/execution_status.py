"""ExecutionStatus enumeration.

Represents the execution status of a command.
"""

from enum import Enum


class ExecutionStatus(Enum):
    """Enumeration representing the execution status.

    PENDING: Waiting to execute.
    RUNNING: Currently executing.
    COMPLETED: Execution completed successfully.
    FAILED: Execution failed.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
