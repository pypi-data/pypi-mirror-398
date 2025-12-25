"""Test input build policy.

Policy that builds test inputs when a data file is loaded.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from command_eval.domain.aggregates.data_file import DataFile
from command_eval.domain.aggregates.test_input import TestInput
from command_eval.domain.entities.data_item import DataItem
from command_eval.domain.events.data_file_loaded import DataFileLoaded
from command_eval.domain.events.test_input_built import TestInputBuilt
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.ids.data_file_id import DataFileId
from command_eval.domain.value_objects.query_source import QuerySource


class FileContentReader(ABC):
    """Abstract interface for reading file contents."""

    @abstractmethod
    def read(self, file_path: FilePath) -> str:
        """Read the content of a file.

        Args:
            file_path: Path to the file.

        Returns:
            The file content as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...


@dataclass(frozen=True)
class BuildTestInputRequest:
    """Request to build test inputs from a data file.

    Attributes:
        data_file: The loaded data file.
        event: The DataFileLoaded event that triggered this request.
    """

    data_file: DataFile
    event: DataFileLoaded


@dataclass(frozen=True)
class TestInputWithEvent:
    """A test input with its associated event.

    Attributes:
        test_input: The built test input.
        event: The event emitted when building the test input.
    """

    test_input: TestInput
    event: TestInputBuilt


@dataclass(frozen=True)
class BuildTestInputResult:
    """Result of building test inputs.

    Attributes:
        test_inputs: Tuple of test inputs with their events.
        data_file_id: The source data file ID.
    """

    test_inputs: tuple[TestInputWithEvent, ...]
    data_file_id: DataFileId


class TestInputBuildPolicy:
    """Policy for building test inputs when a data file is loaded.

    This policy is responsible for:
    - Receiving a DataFileLoaded event
    - Building TestInput aggregates from each data item
    - Emitting TestInputBuilt events for each test input
    """

    def __init__(self, file_reader: Optional[FileContentReader] = None) -> None:
        """Initialize the policy.

        Args:
            file_reader: Reader for file contents (optional, required for FILE source types).
        """
        self._file_reader = file_reader

    def execute(self, request: BuildTestInputRequest) -> BuildTestInputResult:
        """Execute the test input build policy.

        Args:
            request: The request containing the data file and event.

        Returns:
            The result containing all built test inputs and their events.
        """
        test_inputs: list[TestInputWithEvent] = []

        for item in request.data_file.items:
            test_input, event = self._build_test_input(
                data_file_id=request.data_file.id,
                item=item,
            )
            test_inputs.append(TestInputWithEvent(test_input=test_input, event=event))

        return BuildTestInputResult(
            test_inputs=tuple(test_inputs),
            data_file_id=request.data_file.id,
        )

    def _build_test_input(
        self,
        data_file_id: DataFileId,
        item: DataItem,
    ) -> tuple[TestInput, TestInputBuilt]:
        """Build a single test input from a data item.

        Args:
            data_file_id: The source data file ID.
            item: The data item to build from.

        Returns:
            A tuple of (TestInput, TestInputBuilt event).
        """
        # Get query content
        query = self._get_source_content(item.query_source)

        # Create test input with evaluation_specs propagated from DataItem
        # SDK-specific params are stored in evaluation_specs and parsed by Infrastructure layer
        return TestInput.create(
            data_file_id=data_file_id,
            query=query,
            command=item.command,
            actual_file=item.actual_file,
            pre_commands=item.pre_commands,
            query_append_text=item.query_append_text,
            evaluation_specs=item.evaluation_specs,
        )

    def _get_source_content(self, source: QuerySource) -> str:
        """Get content from a source (file or inline).

        Args:
            source: The source to get content from.

        Returns:
            The content string.

        Raises:
            ValueError: If file source is used without a file reader.
        """
        from command_eval.domain.value_objects.source_type import SourceType

        if source.source_type == SourceType.INLINE:
            return source.value
        elif source.source_type == SourceType.FILE:
            if self._file_reader is None:
                raise ValueError(
                    "File reader is required for FILE source type"
                )
            return self._file_reader.read(FilePath(source.value))
        else:
            raise ValueError(f"Unknown source type: {source.source_type}")
