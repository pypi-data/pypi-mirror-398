"""Evaluation result output formatter.

Provides formatting for evaluation results to various output formats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Protocol

from command_eval.application.command_evaluation import CommandEvaluationResult


class OutputFormat(Enum):
    """Supported output formats."""

    TEXT = "text"
    JSON = "json"


class ResultFormatter(Protocol):
    """Protocol for result formatters."""

    def format(self, result: CommandEvaluationResult, verbose: bool = False) -> str:
        """Format the evaluation result.

        Args:
            result: The evaluation result to format.
            verbose: Whether to include verbose details.

        Returns:
            Formatted string output.
        """
        ...


class BaseFormatter(ABC):
    """Base class for formatters."""

    @abstractmethod
    def format(self, result: CommandEvaluationResult, verbose: bool = False) -> str:
        """Format the evaluation result.

        Args:
            result: The evaluation result to format.
            verbose: Whether to include verbose details.

        Returns:
            Formatted string output.
        """
        pass


class TextFormatter(BaseFormatter):
    """Text-based formatter for console output."""

    def __init__(self, width: int = 60) -> None:
        """Initialize the formatter.

        Args:
            width: Width of separator lines.
        """
        self._width = width

    def format(self, result: CommandEvaluationResult, verbose: bool = False) -> str:
        """Format the evaluation result as text.

        Args:
            result: The evaluation result to format.
            verbose: Whether to include verbose details.

        Returns:
            Formatted text output.
        """
        lines: list[str] = []

        # Header
        lines.append(self._separator("="))
        lines.append("EVALUATION RESULTS")
        lines.append(self._separator("="))
        lines.append("")

        # Summary section
        lines.extend(self._format_summary(result))
        lines.append("")

        # Evaluation status section
        if result.evaluation:
            lines.extend(self._format_evaluation_status(result))
            lines.append("")

            # Verbose details
            if verbose:
                lines.extend(self._format_detailed_results(result))
                lines.append("")
        else:
            lines.append("Status: NO EVALUATION (no test cases created)")
            lines.append("")

        # Footer
        lines.append(self._separator("="))

        return "\n".join(lines)

    def _separator(self, char: str) -> str:
        """Create a separator line.

        Args:
            char: Character to use for separator.

        Returns:
            Separator string.
        """
        return char * self._width

    def _format_summary(self, result: CommandEvaluationResult) -> list[str]:
        """Format the summary section.

        Args:
            result: The evaluation result.

        Returns:
            List of formatted lines.
        """
        lines: list[str] = []
        lines.append("[Summary]")
        lines.append(f"  Data file: {result.data_file.file_path.value}")
        lines.append(f"  Total items: {len(result.data_file.items)}")
        lines.append(f"  Test inputs built: {len(result.test_inputs)}")
        lines.append(f"  Commands executed: {len(result.executions)}")
        lines.append(f"  Test cases created: {len(result.test_cases)}")
        if result.skipped_count > 0:
            lines.append(f"  Skipped: {result.skipped_count}")
        return lines

    def _format_evaluation_status(self, result: CommandEvaluationResult) -> list[str]:
        """Format the evaluation status section.

        Args:
            result: The evaluation result.

        Returns:
            List of formatted lines.
        """
        lines: list[str] = []
        evaluation = result.evaluation

        if evaluation is None:
            return lines

        status = "PASSED" if evaluation.is_successful else "FAILED"
        lines.append("[Evaluation]")
        lines.append(f"  Status: {status}")
        lines.append(
            f"  Passed/Failed: {evaluation.result.passed_count}/{evaluation.result.failed_count}"
        )
        return lines

    def _format_detailed_results(self, result: CommandEvaluationResult) -> list[str]:
        """Format detailed results for verbose mode.

        Args:
            result: The evaluation result.

        Returns:
            List of formatted lines.
        """
        lines: list[str] = []

        if result.evaluation is None:
            return lines

        lines.append(self._separator("-"))
        lines.append("[Detailed Results]")
        lines.append(self._separator("-"))

        for i, tc_result in enumerate(result.evaluation.result.test_case_results):
            lines.append(f"  Test Case {i + 1}: {tc_result.test_case_id.value}")
            lines.append(f"    Passed: {tc_result.passed}")

            if tc_result.metric_scores:
                lines.append("    Metrics:")
                for metric, score in tc_result.metric_scores.items():
                    lines.append(f"      - {metric}: {score:.4f}")

            if i < len(result.evaluation.result.test_case_results) - 1:
                lines.append("")

        return lines


class JsonFormatter(BaseFormatter):
    """JSON formatter for machine-readable output."""

    def __init__(self, indent: int = 2) -> None:
        """Initialize the formatter.

        Args:
            indent: JSON indentation level.
        """
        self._indent = indent

    def format(self, result: CommandEvaluationResult, verbose: bool = False) -> str:
        """Format the evaluation result as JSON.

        Args:
            result: The evaluation result to format.
            verbose: Whether to include verbose details.

        Returns:
            Formatted JSON output.
        """
        import json

        data = self._build_data(result, verbose)
        return json.dumps(data, indent=self._indent, ensure_ascii=False)

    def _build_data(
        self, result: CommandEvaluationResult, verbose: bool
    ) -> dict:
        """Build the JSON data structure.

        Args:
            result: The evaluation result.
            verbose: Whether to include verbose details.

        Returns:
            Dictionary for JSON serialization.
        """
        data: dict = {
            "summary": {
                "data_file": result.data_file.file_path.value,
                "total_items": len(result.data_file.items),
                "test_inputs_built": len(result.test_inputs),
                "commands_executed": len(result.executions),
                "test_cases_created": len(result.test_cases),
                "skipped": result.skipped_count,
            },
            "has_evaluation": result.evaluation is not None,
            "is_successful": result.is_successful,
        }

        if result.evaluation:
            data["evaluation"] = {
                "status": "PASSED" if result.evaluation.is_successful else "FAILED",
                "passed_count": result.evaluation.result.passed_count,
                "failed_count": result.evaluation.result.failed_count,
            }

            if verbose:
                data["evaluation"]["test_case_results"] = [
                    {
                        "test_case_id": tc_result.test_case_id.value,
                        "passed": tc_result.passed,
                        "metric_scores": tc_result.metric_scores or {},
                    }
                    for tc_result in result.evaluation.result.test_case_results
                ]

        return data


def get_formatter(output_format: OutputFormat) -> BaseFormatter:
    """Get a formatter for the specified output format.

    Args:
        output_format: The desired output format.

    Returns:
        Appropriate formatter instance.

    Raises:
        ValueError: If the format is not supported.
    """
    if output_format == OutputFormat.TEXT:
        return TextFormatter()
    elif output_format == OutputFormat.JSON:
        return JsonFormatter()
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
