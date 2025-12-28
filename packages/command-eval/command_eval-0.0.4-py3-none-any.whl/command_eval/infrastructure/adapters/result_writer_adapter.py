"""Result writer adapter.

Implements the ResultWriterPort using Jinja2 templates for rendering.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from command_eval.domain.ports.result_writer_port import (
    ResultWriteRequest,
    ResultWriteResponse,
    ResultWriterPort,
)
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.output_type import OutputType


class ResultWriterAdapter(ResultWriterPort):
    """Jinja2-based implementation of ResultWriterPort.

    Uses Jinja2 templates to render evaluation results and writes them to files.
    """

    # Map output types to default template names
    DEFAULT_TEMPLATE_MAP = {
        OutputType.TXT: "default_txt.jinja2",
        OutputType.JSON: "default_json.jinja2",
        OutputType.MARKDOWN: "default_markdown.jinja2",
    }

    def write(self, request: ResultWriteRequest) -> ResultWriteResponse:
        """Write evaluation results to a file using a template.

        Args:
            request: The write request containing result data and configuration.

        Returns:
            The write response with the output path or error.
        """
        try:
            # Create output directory
            output_dir = self._create_output_directory(request)

            # Get the template
            template = self._get_template(request)

            # Render the result
            rendered_content = self._render_template(template, request)

            # Write to file
            output_path = self._write_to_file(request, output_dir, rendered_content)

            return ResultWriteResponse.success_response(output_path)

        except Exception as e:
            return ResultWriteResponse.failure_response(str(e))

    def _create_output_directory(self, request: ResultWriteRequest) -> Path:
        """Create the output directory including timestamp subdirectory.

        Args:
            request: The write request.

        Returns:
            The path to the output directory.
        """
        base_dir = Path(request.output_config.output_dir.value)
        output_dir = base_dir / request.timestamp_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir

    def _get_template(self, request: ResultWriteRequest) -> Template:
        """Get the Jinja2 template for rendering.

        Uses custom template if specified, otherwise uses default template.

        Args:
            request: The write request.

        Returns:
            The Jinja2 Template object.
        """
        if request.output_config.template_file:
            # Use custom template
            return self._load_custom_template(
                request.output_config.template_file.value
            )
        else:
            # Use default template
            return self._load_default_template(request.output_config.output_type)

    def _load_custom_template(self, template_path: str) -> Template:
        """Load a custom template from the file system.

        Args:
            template_path: Path to the custom template file.

        Returns:
            The Jinja2 Template object.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        path = Path(template_path)
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Create environment with the template's directory
        env = Environment(
            loader=FileSystemLoader(str(path.parent)),
            autoescape=False,
        )
        return env.get_template(path.name)

    def _load_default_template(self, output_type: OutputType) -> Template:
        """Load a default template from the package resources.

        Args:
            output_type: The output type to get the template for.

        Returns:
            The Jinja2 Template object.
        """
        template_name = self.DEFAULT_TEMPLATE_MAP[output_type]

        # Use importlib.resources to access package templates
        template_content = resources.files("command_eval.templates").joinpath(
            template_name
        ).read_text(encoding="utf-8")

        env = Environment(autoescape=False)
        return env.from_string(template_content)

    def _render_template(
        self,
        template: Template,
        request: ResultWriteRequest,
    ) -> str:
        """Render the template with the result data.

        Args:
            template: The Jinja2 template.
            request: The write request containing the result data.

        Returns:
            The rendered content.
        """
        # Build context with item_id and all result data
        context = {
            "item_id": request.item_id,
            **request.result_data,
        }

        return template.render(**context)

    def _write_to_file(
        self,
        request: ResultWriteRequest,
        output_dir: Path,
        content: str,
    ) -> FilePath:
        """Write the rendered content to a file.

        Args:
            request: The write request.
            output_dir: The output directory path.
            content: The rendered content to write.

        Returns:
            The path to the written file.
        """
        # Get file extension from output type
        extension = request.output_config.get_file_extension()

        # Build the output file path
        output_file = output_dir / f"{request.item_id}{extension}"

        # Write the content
        output_file.write_text(content, encoding="utf-8")

        return FilePath(str(output_file))
