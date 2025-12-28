"""CLI entry point for command-eval.

Provides command line interface for running evaluations.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from command_eval.application.command_evaluation import (
    CommandEvaluation,
    CommandEvaluationResult,
    EvaluationRequest,
)
from command_eval.domain.policies.data_file_load_policy import DataFileParser
from command_eval.domain.policies.test_input_build_policy import FileContentReader
from command_eval.domain.ports.evaluation_port import EvaluationPort
from command_eval.domain.ports.execution_port import ExecutionPort
from command_eval.domain.value_objects.evaluation_config import EvaluationConfig
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.metric_type import MetricType
from command_eval.infrastructure.adapters.subprocess_execution_adapter import (
    SubprocessExecutionAdapter,
)
from command_eval.infrastructure.parsers.json_parser import JsonDataFileParser
from command_eval.infrastructure.parsers.yaml_parser import YamlDataFileParser
from command_eval.presentation.formatter import (
    OutputFormat,
    TextFormatter,
    JsonFormatter,
    get_formatter,
)


class DefaultFileContentReader(FileContentReader):
    """Default file content reader implementation."""

    def read(self, file_path: FilePath) -> str:
        """Read file content.

        Args:
            file_path: Path to the file to read.

        Returns:
            The file content as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        with open(file_path.value, "r", encoding="utf-8") as f:
            return f.read()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="command-eval",
        description="CLI command evaluation tool using LLM-based metrics.",
    )

    parser.add_argument(
        "data_file",
        type=str,
        help="Path to the data file (YAML or JSON format)",
    )

    parser.add_argument(
        "--metrics",
        "-m",
        type=str,
        nargs="+",
        default=["answer_relevancy"],
        help="Metric types to evaluate (default: answer_relevancy)",
    )

    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.5,
        help="Evaluation threshold (0.0-1.0, default: 0.5)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--evaluation-sdk",
        "-e",
        type=str,
        choices=["deepeval", "ragas"],
        default="deepeval",
        help="Evaluation SDK to use (default: deepeval)",
    )

    parser.add_argument(
        "--shell",
        "-s",
        type=str,
        default="/bin/bash",
        help="Shell to use for command execution (default: /bin/bash)",
    )

    parser.add_argument(
        "--output-format",
        "-o",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    return parser


def get_parser_for_file(file_path: str) -> DataFileParser:
    """Get appropriate parser based on file extension.

    Args:
        file_path: Path to the data file.

    Returns:
        Appropriate parser for the file type.

    Raises:
        ValueError: If the file extension is not supported.
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension in (".yaml", ".yml"):
        return YamlDataFileParser()
    elif extension == ".json":
        return JsonDataFileParser()
    else:
        raise ValueError(
            f"Unsupported file extension: {extension}. "
            "Supported: .yaml, .yml, .json"
        )


def get_evaluation_port(sdk: str) -> EvaluationPort:
    """Get the evaluation port for the specified SDK.

    Args:
        sdk: SDK name ("deepeval" or "ragas").

    Returns:
        Configured evaluation port.

    Raises:
        ValueError: If the SDK is not supported.
    """
    if sdk == "deepeval":
        from command_eval.infrastructure.adapters.evaluation.deepeval import (
            DeepEvalAdapter,
        )

        return DeepEvalAdapter()
    elif sdk == "ragas":
        from command_eval.infrastructure.adapters.evaluation.ragas import (
            RagasAdapter,
        )

        return RagasAdapter()
    else:
        raise ValueError(f"Unsupported evaluation SDK: {sdk}")


def run_evaluation(
    data_file: str,
    metrics: list[str],
    threshold: float,
    verbose: bool,
    evaluation_sdk: str,
    shell: str,
) -> CommandEvaluationResult:
    """Run the evaluation.

    Args:
        data_file: Path to the data file.
        metrics: List of metric type strings.
        threshold: Evaluation threshold.
        verbose: Whether to enable verbose output.
        evaluation_sdk: SDK to use for evaluation.
        shell: Shell to use for command execution.

    Returns:
        The evaluation result.
    """
    # Get parser based on file type
    parser = get_parser_for_file(data_file)

    # Create file content reader
    file_reader = DefaultFileContentReader()

    # Create execution port
    execution_port: ExecutionPort = SubprocessExecutionAdapter(shell=shell)

    # Create evaluation port
    evaluation_port = get_evaluation_port(evaluation_sdk)

    # Create command evaluation
    command_eval = CommandEvaluation(
        data_file_parser=parser,
        file_content_reader=file_reader,
        execution_port=execution_port,
        evaluation_port=evaluation_port,
    )

    # Create config
    metric_types = tuple(MetricType(m) for m in metrics)
    config = EvaluationConfig(
        metric_types=metric_types,
        default_threshold=threshold,
        verbose_mode=verbose,
    )

    # Create request
    request = EvaluationRequest(
        data_file_path=FilePath(data_file),
        config=config,
    )

    # Execute
    return command_eval.execute(request)


def format_result(
    result: CommandEvaluationResult, verbose: bool, output_format: str = "text"
) -> str:
    """Format the evaluation result for output.

    Args:
        result: The evaluation result.
        verbose: Whether to show verbose output.
        output_format: Output format ("text" or "json").

    Returns:
        Formatted string output.
    """
    format_enum = OutputFormat(output_format)
    formatter = get_formatter(format_enum)
    return formatter.format(result, verbose=verbose)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        result = run_evaluation(
            data_file=args.data_file,
            metrics=args.metrics,
            threshold=args.threshold,
            verbose=args.verbose,
            evaluation_sdk=args.evaluation_sdk,
            shell=args.shell,
        )

        output = format_result(result, args.verbose, args.output_format)
        print(output)

        return 0 if result.is_successful else 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
