"""File parameter resolver.

Resolves *_file parameters to their file contents.
Generic implementation usable by any evaluation adapter.
"""

from __future__ import annotations

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


def _read_and_format_files(
    file_paths: list[str],
    file_reader: FileContentReader,
) -> str:
    """Read multiple files and concatenate with filepath headers.

    Format:
        ---filepath1---
        (content1)
        ---filepath2---
        (content2)

    Args:
        file_paths: List of file paths to read.
        file_reader: File content reader.

    Returns:
        Concatenated file contents with headers.
    """
    parts: list[str] = []
    for file_path in file_paths:
        content = file_reader.read(file_path)
        parts.append(f"---{file_path}---\n{content.strip()}")
    return "\n".join(parts)


def resolve_file_params(
    params: dict[str, Any],
    file_reader: FileContentReader,
    *,
    list_params: frozenset[str] = frozenset(),
    skip_params: frozenset[str] = frozenset({"param_file"}),
) -> dict[str, Any]:
    """Resolve *_file parameters to their file contents.

    Automatically converts:
    - <key>_file -> <key> (if <key> not already set)
    - For keys in list_params, content is parsed as list (one item per line)
    - If <key>_file is a list of paths, contents are concatenated with headers:
        ---filepath1---
        (content1)
        ---filepath2---
        (content2)

    Args:
        params: The params dict from YAML.
        file_reader: File content reader.
        list_params: Keys that should be parsed as list (one item per line).
        skip_params: File params to skip during resolution.

    Returns:
        Dict with file contents resolved.
    """
    resolved: dict[str, Any] = {}

    for key, value in params.items():
        if key.endswith("_file") and key not in skip_params:
            base_key = key[:-5]  # Remove "_file" suffix
            if base_key not in params:  # Only if base key not already set
                # Handle list of file paths
                if isinstance(value, list):
                    file_paths = [str(v) for v in value]
                    content = _read_and_format_files(file_paths, file_reader)
                    if base_key in list_params:
                        # Parse concatenated content as list
                        resolved[base_key] = [
                            line.strip() for line in content.split("\n") if line.strip()
                        ]
                    else:
                        resolved[base_key] = content
                else:
                    # Single file path
                    content = file_reader.read(str(value))
                    if base_key in list_params:
                        # Parse as list (one item per non-empty line)
                        resolved[base_key] = [
                            line.strip() for line in content.split("\n") if line.strip()
                        ]
                    else:
                        resolved[base_key] = content.strip()
        elif isinstance(value, dict):
            resolved[key] = resolve_file_params(
                value, file_reader, list_params=list_params, skip_params=skip_params
            )
        elif isinstance(value, list):
            resolved[key] = [
                resolve_file_params(
                    item, file_reader, list_params=list_params, skip_params=skip_params
                )
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            resolved[key] = value

    return resolved


class FileParamResolver:
    """Resolves *_file parameters to their file contents.

    Generic implementation that can be configured for any SDK.
    """

    def __init__(
        self,
        file_reader: FileContentReader | None = None,
        list_params: frozenset[str] | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            file_reader: File content reader. Defaults to DefaultFileContentReader.
            list_params: Keys that should be parsed as list.
        """
        self._file_reader = file_reader or DefaultFileContentReader()
        self._list_params = list_params or frozenset()

    def resolve(self, params: dict[str, Any]) -> dict[str, Any]:
        """Resolve *_file parameters in the given dict.

        Args:
            params: The params dict.

        Returns:
            Dict with resolved values.
        """
        return resolve_file_params(
            params, self._file_reader, list_params=self._list_params
        )
