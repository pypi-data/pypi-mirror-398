"""OutputConfig value object.

Represents the configuration for output result files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.output_type import OutputType


@dataclass(frozen=True)
class OutputConfig:
    """Value object representing output configuration.

    Attributes:
        output_type: The output format type (txt, json, markdown).
        output_dir: The directory where output files will be written.
        template_file: Optional custom template file path.
    """

    output_type: OutputType
    output_dir: FilePath
    template_file: Optional[FilePath] = None

    def get_file_extension(self) -> str:
        """Get the file extension for the output type.

        Returns:
            The file extension including the dot (e.g., '.md').
        """
        extension_map = {
            OutputType.TXT: ".txt",
            OutputType.JSON: ".json",
            OutputType.MARKDOWN: ".md",
        }
        return extension_map[self.output_type]
