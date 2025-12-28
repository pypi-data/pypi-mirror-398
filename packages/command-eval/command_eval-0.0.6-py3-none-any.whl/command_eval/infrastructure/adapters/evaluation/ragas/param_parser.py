"""Ragas parameter parser.

Parses EvaluationSpec.params into Ragas-specific resolved parameters.
Handles file reading for *_file parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from command_eval.infrastructure.adapters.evaluation.file_param_resolver import (
    DefaultFileContentReader,
    FileContentReader,
)


@dataclass(frozen=True)
class RagasResolvedParams:
    """Resolved parameters for Ragas evaluation.

    Attributes:
        reference: Expected/reference output text (optional).
        retrieved_contexts: RAG retrieval context for evaluation (optional).
    """

    reference: str | None = None
    retrieved_contexts: tuple[str, ...] | None = None


class RagasParamParser:
    """Parser for Ragas evaluation parameters.

    Parses EvaluationSpec.params dict into RagasResolvedParams.
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

    def parse(self, params: dict[str, Any]) -> RagasResolvedParams:
        """Parse params dict into RagasResolvedParams.

        Args:
            params: The params dict from EvaluationSpec.

        Returns:
            RagasResolvedParams with resolved values.
        """
        reference = self._parse_reference(params)
        retrieved_contexts = self._parse_retrieved_contexts(params)

        return RagasResolvedParams(
            reference=reference,
            retrieved_contexts=retrieved_contexts,
        )

    def _parse_reference(self, params: dict[str, Any]) -> str | None:
        """Parse reference value from params.

        Supports both inline 'reference' and file-based 'reference_file'.

        Args:
            params: The params dict.

        Returns:
            Reference text or None.
        """
        reference = params.get("reference")
        reference_file = params.get("reference_file")

        if reference is not None:
            return str(reference)
        elif reference_file is not None:
            return self._file_reader.read(str(reference_file)).strip()
        else:
            return None

    def _parse_retrieved_contexts(
        self, params: dict[str, Any]
    ) -> tuple[str, ...] | None:
        """Parse retrieved_contexts from params.

        Supports both inline 'retrieved_contexts' and
        file-based 'retrieved_contexts_file'.

        Args:
            params: The params dict.

        Returns:
            Retrieved contexts tuple or None.
        """
        retrieved_contexts = params.get("retrieved_contexts")
        retrieved_contexts_file = params.get("retrieved_contexts_file")

        if retrieved_contexts is not None:
            return self._to_string_tuple(retrieved_contexts)
        elif retrieved_contexts_file is not None:
            return self._read_contexts_file(str(retrieved_contexts_file))
        else:
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

    def _read_contexts_file(self, file_path: str) -> tuple[str, ...]:
        """Read contexts from file.

        Each non-empty line becomes a context item.

        Args:
            file_path: Path to the contexts file.

        Returns:
            Tuple of context strings.
        """
        content = self._file_reader.read(file_path)
        lines = content.split("\n")
        return tuple(line.strip() for line in lines if line.strip())
