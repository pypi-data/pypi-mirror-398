"""Result output policy.

Policy that outputs evaluation results to files and stdout.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from command_eval.domain.ports.result_writer_port import (
    ResultWriteRequest,
    ResultWriteResponse,
    ResultWriterPort,
)
from command_eval.domain.value_objects.output_config import OutputConfig

if TYPE_CHECKING:
    from command_eval.domain.aggregates.data_file import DataFile
    from command_eval.domain.aggregates.evaluation import Evaluation
    from command_eval.domain.aggregates.execution import Execution
    from command_eval.domain.aggregates.test_case import TestCase
    from command_eval.domain.aggregates.test_input import TestInput


def _to_template_dict(obj: Any) -> Any:
    """Convert any object to a template-friendly dictionary recursively.

    Handles:
    - dataclasses: Converts to dict with all fields
    - Enums: Returns the value
    - datetime: Returns ISO format string
    - Value objects with 'value' attribute: Returns the value
    - tuples/lists: Converts each element
    - dicts: Converts each value
    - Other: Returns as-is
    """
    if obj is None:
        return None

    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            result[f.name] = _to_template_dict(value)
        # Also include properties (non-field attributes that are properties)
        for name in dir(obj):
            if not name.startswith("_") and name not in result:
                try:
                    attr = getattr(type(obj), name, None)
                    if isinstance(attr, property):
                        result[name] = _to_template_dict(getattr(obj, name))
                except Exception:
                    pass
        return result

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, datetime):
        return obj.isoformat()

    if hasattr(obj, "value") and not isinstance(obj, (str, bytes, dict)):
        # Handle value objects like FilePath, IDs, etc.
        return obj.value

    if isinstance(obj, (list, tuple)):
        return [_to_template_dict(item) for item in obj]

    if isinstance(obj, dict):
        return {k: _to_template_dict(v) for k, v in obj.items()}

    return obj


@dataclass(frozen=True)
class OutputResultRequest:
    """Request to output a single evaluation result.

    Attributes:
        output_config: Configuration for output format and location.
        item_id: Unique identifier for the result item.
        result_data: The evaluation result data to write.
        timestamp_dir: Optional timestamp directory name.
    """

    output_config: OutputConfig
    item_id: str
    result_data: dict[str, Any]
    timestamp_dir: Optional[str] = None

    def get_timestamp_dir(self) -> str:
        """Get the timestamp directory name."""
        if self.timestamp_dir:
            return self.timestamp_dir
        return datetime.now().strftime("%Y-%m-%d_%H%M%S")


@dataclass(frozen=True)
class BatchOutputResultRequest:
    """Request to output batch evaluation results.

    Attributes:
        data_file: The data file with output config and items.
        test_inputs: All test inputs.
        test_cases: All test cases.
        executions: All command executions.
        evaluation: The evaluation result.
    """

    data_file: "DataFile"
    test_inputs: tuple["TestInput", ...]
    test_cases: tuple["TestCase", ...]
    executions: tuple["Execution", ...]
    evaluation: "Evaluation"


@dataclass(frozen=True)
class BatchOutputResultResult:
    """Result of batch output operation.

    Attributes:
        success_count: Number of successfully written items.
        failure_count: Number of failed items.
        outputs: List of (item_id, output_path or error) tuples.
    """

    success_count: int
    failure_count: int
    outputs: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OutputResultResult:
    """Result of outputting evaluation results.

    Attributes:
        write_response: Response from the result writer.
        stdout_output: The content that was written to stdout.
    """

    write_response: ResultWriteResponse
    stdout_output: str


class ResultOutputPolicy:
    """Policy for outputting evaluation results.

    This policy is responsible for:
    - Writing evaluation results to files using templates
    - Printing results to stdout
    - Building result data from domain aggregates
    """

    def __init__(self, result_writer: ResultWriterPort) -> None:
        """Initialize the policy."""
        self._result_writer = result_writer

    def execute(self, request: OutputResultRequest) -> OutputResultResult:
        """Execute single result output."""
        timestamp_dir = request.get_timestamp_dir()
        write_request = ResultWriteRequest(
            output_config=request.output_config,
            item_id=request.item_id,
            result_data=request.result_data,
            timestamp_dir=timestamp_dir,
        )
        write_response = self._result_writer.write(write_request)
        stdout_output = self._generate_stdout_output(request, write_response)
        return OutputResultResult(
            write_response=write_response,
            stdout_output=stdout_output,
        )

    def execute_batch(self, request: BatchOutputResultRequest) -> BatchOutputResultResult:
        """Execute batch result output.

        Transforms domain aggregates into result data and outputs each item.
        """
        data_file = request.data_file
        if not data_file.output_config:
            return BatchOutputResultResult(success_count=0, failure_count=0)

        timestamp_dir = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        # Build mappings for efficient lookup
        eval_results_by_input = self._build_eval_results_mapping(
            request.test_cases, request.evaluation
        )
        tc_by_input = {str(tc.test_input_id): tc for tc in request.test_cases}
        exec_by_input = {str(ex.test_input_id): ex for ex in request.executions}

        success_count = 0
        failure_count = 0
        outputs: list[tuple[str, str]] = []

        for i, test_input in enumerate(request.test_inputs):
            input_id = str(test_input.id)
            item_id = (
                data_file.items[i].effective_id
                if i < len(data_file.items)
                else f"item_{i}"
            )

            result_data = self._build_result_data(
                test_input, input_id, tc_by_input, exec_by_input, eval_results_by_input
            )

            output_result = self.execute(
                OutputResultRequest(
                    output_config=data_file.output_config,
                    item_id=item_id,
                    result_data=result_data,
                    timestamp_dir=timestamp_dir,
                )
            )

            if output_result.write_response.success:
                success_count += 1
                path = output_result.write_response.output_path
                outputs.append((item_id, path.value if path else ""))
            else:
                failure_count += 1
                outputs.append((item_id, output_result.write_response.error_message or ""))

            print(output_result.stdout_output)

        return BatchOutputResultResult(
            success_count=success_count,
            failure_count=failure_count,
            outputs=tuple(outputs),
        )

    def _build_eval_results_mapping(
        self,
        test_cases: tuple["TestCase", ...],
        evaluation: "Evaluation",
    ) -> dict[str, list[dict[str, Any]]]:
        """Build mapping from test_input_id to evaluation results."""
        result_by_input: dict[str, list[dict[str, Any]]] = {}

        if not evaluation.result or not evaluation.result.details:
            return result_by_input

        tc_id_to_input_id = {str(tc.id): str(tc.test_input_id) for tc in test_cases}

        for tc_result in evaluation.result.details:
            # tc_result.test_case_id is TestCaseId type, convert to string
            input_id = tc_id_to_input_id.get(str(tc_result.test_case_id))
            if not input_id:
                continue

            if input_id not in result_by_input:
                result_by_input[input_id] = []

            for mr in tc_result.metric_results:
                result_by_input[input_id].append({
                    "sdk": mr.sdk,
                    "metric": mr.metric,
                    "score": mr.score,
                    "success": mr.passed,
                    "reason": mr.reason,
                    "metadata": dict(mr.metadata) if mr.metadata else {},
                })

        return result_by_input

    def _build_result_data(
        self,
        test_input: "TestInput",
        input_id: str,
        tc_by_input: dict[str, "TestCase"],
        exec_by_input: dict[str, "Execution"],
        eval_results_by_input: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Build result data dictionary for a single test input.

        Uses generic conversion to expose all aggregate fields.
        Template access examples:
        - {{ test_input.actual_input }}
        - {{ test_input.command }}
        - {{ test_case.actual }}
        - {{ test_case.execution_time_ms }}
        - {{ execution.status }}
        - {{ execution.result.exit_code }}
        - {{ evaluation_results[0].score }}
        """
        result_data: dict[str, Any] = {
            "test_input": _to_template_dict(test_input),
        }

        if input_id in tc_by_input:
            result_data["test_case"] = _to_template_dict(tc_by_input[input_id])

        if input_id in exec_by_input:
            result_data["execution"] = _to_template_dict(exec_by_input[input_id])

        if input_id in eval_results_by_input:
            result_data["evaluation_results"] = eval_results_by_input[input_id]

        return result_data

    def _generate_stdout_output(
        self,
        request: OutputResultRequest,
        write_response: ResultWriteResponse,
    ) -> str:
        """Generate the stdout output."""
        lines = [f"Item: {request.item_id}"]

        if write_response.success and write_response.output_path:
            lines.append(f"Output: {write_response.output_path.value}")
        elif not write_response.success:
            lines.append(f"Error: {write_response.error_message}")

        if "evaluation_results" in request.result_data:
            for result in request.result_data["evaluation_results"]:
                sdk = result.get("sdk", "unknown")
                metric = result.get("metric", "unknown")
                score = result.get("score", "N/A")
                lines.append(f"  - {sdk}:{metric} = {score}")

        return "\n".join(lines)
