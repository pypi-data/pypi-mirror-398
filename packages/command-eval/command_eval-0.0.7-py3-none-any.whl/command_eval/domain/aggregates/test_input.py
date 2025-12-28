"""TestInput aggregate root.

Manages test input data constructed from a data item.
SDK-specific fields are stored in evaluation_specs, which Domain layer treats as opaque.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from command_eval.domain.events.test_input_built import TestInputBuilt
from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.ids.data_file_id import DataFileId
from command_eval.domain.value_objects.ids.test_input_id import TestInputId


@dataclass
class TestInput:
    """Aggregate root for test input management.

    Attributes:
        id: Unique identifier for this test input.
        data_file_id: ID of the source data file.
        actual_input: The final actual input text.
        command: The command to execute.
        actual_output_file: Path for command output.
        pre_command: Joined pre-commands (optional).
        evaluation_specs: Evaluation specifications (SDK-independent).
            Domain layer treats this as opaque. Infrastructure layer parses params.
        created_at: When the test input was created.

    Note:
        SDK-specific fields (expected, context, retrieval_context, name, reasoning)
        have been moved to evaluation_specs.params and are parsed by Infrastructure layer.
    """

    id: TestInputId
    data_file_id: DataFileId
    actual_input: str
    command: str
    actual_output_file: FilePath
    pre_command: str | None = None
    evaluation_specs: tuple[EvaluationSpec, ...] = field(default_factory=tuple)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """Validate aggregate invariants."""
        if not self.command:
            raise ValueError("Command is required")

    @classmethod
    def create(
        cls,
        data_file_id: DataFileId,
        actual_input: str,
        command: str,
        actual_output_file: FilePath,
        pre_commands: tuple[str, ...] | None = None,
        actual_input_append_text: str | None = None,
        evaluation_specs: tuple[EvaluationSpec, ...] = (),
    ) -> tuple[TestInput, TestInputBuilt]:
        """Create a new TestInput and emit a TestInputBuilt event.

        Args:
            data_file_id: ID of the source data file.
            actual_input: The base actual input text.
            command: The command to execute.
            actual_output_file: Path for command output.
            pre_commands: Commands to run before main command (optional).
            actual_input_append_text: Text to append to input (optional).
            evaluation_specs: SDK-independent evaluation specifications.

        Returns:
            A tuple of (TestInput, TestInputBuilt event).
        """
        # Join input with append text if provided
        final_input = actual_input
        if actual_input_append_text:
            final_input = f"{actual_input}{actual_input_append_text}"

        # Join pre-commands with && if provided
        pre_command = None
        if pre_commands:
            pre_command = " && ".join(pre_commands)

        test_input = cls(
            id=TestInputId.generate(),
            data_file_id=data_file_id,
            actual_input=final_input,
            command=command,
            actual_output_file=actual_output_file,
            pre_command=pre_command,
            evaluation_specs=evaluation_specs,
        )

        event = TestInputBuilt(
            test_input_id=test_input.id,
            data_file_id=data_file_id,
            command=command,
            actual_output_file=actual_output_file,
        )

        return test_input, event

    @property
    def full_command(self) -> str:
        """Get the full command including pre-commands.

        Returns:
            The full command string.
        """
        if self.pre_command:
            return f"{self.pre_command} && {self.command}"
        return self.command
