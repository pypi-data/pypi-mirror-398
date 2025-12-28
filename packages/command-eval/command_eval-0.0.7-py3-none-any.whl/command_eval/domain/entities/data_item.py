"""DataItem entity.

Represents a single data item within a data file.
SDK-specific fields are stored in evaluation_specs, which Domain layer treats as opaque.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.actual_input_source import ActualInputSource


@dataclass(frozen=True)
class DataItem:
    """A data item within a data file.

    Attributes:
        index: The index of this item within the data file (0-based).
        id: Optional item ID for output file naming. If not specified,
            effective_id returns 'item_{index}'.
        actual_input_source: Source of the actual input (file path or inline text).
        command: The command to execute.
        actual_output_file: The actual output file path for command execution.
        pre_commands: Commands to run before the main command.
        actual_input_append_text: Text to append to the input (optional).
        evaluation_specs: Evaluation specifications (SDK-independent).
            Domain layer treats this as opaque. Infrastructure layer parses params.

    Note:
        SDK-specific fields (expected_source, context, retrieval_context, name, reasoning)
        have been moved to evaluation_specs.params and are parsed by Infrastructure layer.
    """

    index: int
    actual_input_source: ActualInputSource
    command: str
    actual_output_file: FilePath
    id: str | None = None
    pre_commands: tuple[str, ...] = field(default_factory=tuple)
    actual_input_append_text: str | None = None
    evaluation_specs: tuple[EvaluationSpec, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate data item."""
        if self.index < 0:
            raise ValueError("Index must be non-negative")
        if not self.command:
            raise ValueError("Command cannot be empty")

    @property
    def effective_id(self) -> str:
        """Get the effective ID for this item.

        Returns:
            The item's id if specified, otherwise 'item_{index}'.
        """
        return self.id if self.id else f"item_{self.index}"
