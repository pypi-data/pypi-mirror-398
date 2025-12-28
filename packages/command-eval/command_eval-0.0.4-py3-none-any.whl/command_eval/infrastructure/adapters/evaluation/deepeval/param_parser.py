"""DeepEval parameter parser.

Parses EvaluationSpec.params into DeepEval-specific resolved parameters.
Handles file reading for *_file parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class FileContentReader(Protocol):
    """Protocol for reading file contents."""

    def read(self, file_path: str) -> str:
        """Read file contents.

        Args:
            file_path: Path to the file.

        Returns:
            File contents as string.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        ...


class DefaultFileContentReader:
    """Default implementation of FileContentReader."""

    def read(self, file_path: str) -> str:
        """Read file contents.

        Args:
            file_path: Path to the file.

        Returns:
            File contents as string.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


@dataclass(frozen=True)
class DeepEvalResolvedParams:
    """Resolved parameters for DeepEval evaluation.

    Attributes:
        expected: Expected output text (optional).
        context: Ground truth context for evaluation (optional).
        retrieval_context: RAG retrieval context for evaluation (optional).
        name: Test case name for identification (optional).
        reasoning: Reasoning process for evaluation (optional).
        completion_time: Execution completion time in seconds (optional).
    """

    expected: str | None = None
    context: tuple[str, ...] | None = None
    retrieval_context: tuple[str, ...] | None = None
    name: str | None = None
    reasoning: str | None = None
    completion_time: float | None = None


class DeepEvalParamParser:
    """Parser for DeepEval evaluation parameters.

    Parses EvaluationSpec.params dict into DeepEvalResolvedParams.
    Handles both inline values and file references (*_file parameters).
    """

    def __init__(
        self,
        file_reader: FileContentReader | None = None,
    ) -> None:
        """Initialize the parser.

        Args:
            file_reader: File content reader. Defaults to DefaultFileContentReader.
        """
        self._file_reader = file_reader or DefaultFileContentReader()

    def parse(self, params: dict[str, Any]) -> DeepEvalResolvedParams:
        """Parse params dict into DeepEvalResolvedParams.

        Args:
            params: The params dict from EvaluationSpec.

        Returns:
            DeepEvalResolvedParams with resolved values.
        """
        expected = self._parse_expected(params)
        context = self._parse_context(params)
        retrieval_context = self._parse_retrieval_context(params)
        name = params.get("name")
        reasoning = params.get("reasoning")
        completion_time = self._parse_completion_time(params)

        return DeepEvalResolvedParams(
            expected=expected,
            context=context,
            retrieval_context=retrieval_context,
            name=name,
            reasoning=reasoning,
            completion_time=completion_time,
        )

    def _parse_expected(self, params: dict[str, Any]) -> str | None:
        """Parse expected value from params.

        Supports both inline 'expected' and file-based 'expected_file'.

        Args:
            params: The params dict.

        Returns:
            Expected output text or None.
        """
        expected = params.get("expected")
        expected_file = params.get("expected_file")

        if expected is not None:
            return str(expected)
        elif expected_file is not None:
            return self._file_reader.read(str(expected_file)).strip()
        else:
            return None

    def _parse_context(self, params: dict[str, Any]) -> tuple[str, ...] | None:
        """Parse context from params.

        Supports both inline 'context' and file-based 'context_file'.

        Args:
            params: The params dict.

        Returns:
            Context tuple or None.
        """
        context = params.get("context")
        context_file = params.get("context_file")

        if context is not None:
            return self._to_string_tuple(context)
        elif context_file is not None:
            return self._read_context_file(str(context_file))
        else:
            return None

    def _parse_retrieval_context(
        self, params: dict[str, Any]
    ) -> tuple[str, ...] | None:
        """Parse retrieval_context from params.

        Supports both inline 'retrieval_context' and file-based 'retrieval_context_file'.

        Args:
            params: The params dict.

        Returns:
            Retrieval context tuple or None.
        """
        retrieval_context = params.get("retrieval_context")
        retrieval_context_file = params.get("retrieval_context_file")

        if retrieval_context is not None:
            return self._to_string_tuple(retrieval_context)
        elif retrieval_context_file is not None:
            return self._read_context_file(str(retrieval_context_file))
        else:
            return None

    def _parse_completion_time(self, params: dict[str, Any]) -> float | None:
        """Parse completion_time from params.

        Args:
            params: The params dict.

        Returns:
            Completion time in seconds or None.
        """
        completion_time = params.get("completion_time")
        if completion_time is not None:
            return float(completion_time)
        return None

    def _to_string_tuple(self, value: Any) -> tuple[str, ...]:
        """Convert value to tuple of strings.

        Args:
            value: A list or single value.

        Returns:
            Tuple of strings.
        """
        if isinstance(value, list):
            return tuple(str(v) for v in value if v)
        else:
            return (str(value),)

    def _read_context_file(self, file_path: str) -> tuple[str, ...]:
        """Read context from file.

        Each non-empty line becomes a context item.

        Args:
            file_path: Path to the context file.

        Returns:
            Tuple of context strings.
        """
        content = self._file_reader.read(file_path)
        lines = content.split("\n")
        return tuple(line.strip() for line in lines if line.strip())
