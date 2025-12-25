"""Infrastructure adapters.

Provides implementations for domain ports.
"""

from command_eval.infrastructure.adapters.custom_eval_adapter import (
    CustomEvalAdapter,
    CustomMetricInput,
    CustomMetricResult,
)
from command_eval.infrastructure.adapters.deepeval_adapter import DeepEvalAdapter
from command_eval.infrastructure.adapters.multi_eval_adapter import MultiEvalAdapter
from command_eval.infrastructure.adapters.pty_execution_adapter import (
    PtyExecutionAdapter,
)
from command_eval.infrastructure.adapters.ragas_adapter import RagasAdapter
from command_eval.infrastructure.adapters.result_writer_adapter import (
    ResultWriterAdapter,
)
from command_eval.infrastructure.adapters.subprocess_execution_adapter import (
    SubprocessExecutionAdapter,
)

__all__ = [
    # Execution adapters
    "PtyExecutionAdapter",
    "SubprocessExecutionAdapter",
    # Evaluation adapters
    "DeepEvalAdapter",
    "RagasAdapter",
    "MultiEvalAdapter",
    # Custom evaluation base classes
    "CustomEvalAdapter",
    "CustomMetricInput",
    "CustomMetricResult",
    # Result writer
    "ResultWriterAdapter",
]
