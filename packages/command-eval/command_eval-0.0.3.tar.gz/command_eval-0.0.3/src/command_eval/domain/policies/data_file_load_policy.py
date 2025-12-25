"""Data file load policy.

Policy that loads a data file when evaluation is requested.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from command_eval.domain.aggregates.data_file import DataFile
from command_eval.domain.entities.data_item import DataItem
from command_eval.domain.events.data_file_loaded import DataFileLoaded
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.output_config import OutputConfig


@dataclass(frozen=True)
class ParseResult:
    """Result of parsing a data file.

    Attributes:
        items: Tuple of data items from the file.
        output_config: Optional output configuration for result files.
    """

    items: tuple[DataItem, ...]
    output_config: OutputConfig | None = None


class DataFileParser(ABC):
    """Abstract interface for parsing data files."""

    @abstractmethod
    def parse(self, file_path: FilePath) -> ParseResult:
        """Parse a data file and return parse result.

        Args:
            file_path: Path to the data file.

        Returns:
            ParseResult containing data items and optional output config.

        Raises:
            ValueError: If the file cannot be parsed.
            FileNotFoundError: If the file does not exist.
        """
        ...


@dataclass(frozen=True)
class LoadDataFileRequest:
    """Request to load a data file.

    Attributes:
        file_path: Path to the data file to load.
    """

    file_path: FilePath


@dataclass(frozen=True)
class LoadDataFileResult:
    """Result of loading a data file.

    Attributes:
        data_file: The loaded data file aggregate.
        event: The domain event emitted.
    """

    data_file: DataFile
    event: DataFileLoaded


class DataFileLoadPolicy:
    """Policy for loading data files when evaluation is requested.

    This policy is responsible for:
    - Receiving an evaluation request with a file path
    - Parsing the data file
    - Creating a DataFile aggregate
    - Emitting a DataFileLoaded event
    """

    def __init__(self, parser: DataFileParser) -> None:
        """Initialize the policy.

        Args:
            parser: Parser to use for reading data files.
        """
        self._parser = parser

    def execute(self, request: LoadDataFileRequest) -> LoadDataFileResult:
        """Execute the data file load policy.

        Args:
            request: The request containing the file path.

        Returns:
            The result containing the data file and event.

        Raises:
            ValueError: If the file cannot be parsed or is invalid.
            FileNotFoundError: If the file does not exist.
        """
        # Validate file path
        self._validate_file_path(request.file_path)

        # Parse the data file
        parse_result = self._parser.parse(request.file_path)

        # Create the DataFile aggregate
        data_file, event = DataFile.create(
            file_path=request.file_path,
            items=parse_result.items,
            output_config=parse_result.output_config,
        )

        return LoadDataFileResult(data_file=data_file, event=event)

    def _validate_file_path(self, file_path: FilePath) -> None:
        """Validate the file path.

        Args:
            file_path: The file path to validate.

        Raises:
            ValueError: If the file path is invalid.
        """
        extension = file_path.get_extension()
        if extension not in (".yaml", ".yml", ".json"):
            raise ValueError(
                f"Unsupported file format: {extension}. "
                "Supported formats: .yaml, .yml, .json"
            )
