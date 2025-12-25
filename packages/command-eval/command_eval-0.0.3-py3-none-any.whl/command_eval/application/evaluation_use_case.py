"""Evaluation use case.

Main use case that orchestrates the complete evaluation flow:
1. Load data file
2. Build test inputs
3. Execute commands
4. Create test cases
5. Execute evaluation
6. Output results (optional)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from command_eval.domain.aggregates.data_file import DataFile
from command_eval.infrastructure.logging import get_logger

_logger = get_logger(__name__)
from command_eval.domain.aggregates.evaluation import Evaluation
from command_eval.domain.aggregates.execution import Execution
from command_eval.domain.aggregates.test_case import TestCase
from command_eval.domain.aggregates.test_input import TestInput
from command_eval.domain.policies.command_execution_policy import (
    CommandExecutionPolicy,
    ExecuteCommandRequest,
)
from command_eval.domain.policies.data_file_load_policy import (
    DataFileLoadPolicy,
    DataFileParser,
    LoadDataFileRequest,
)
from command_eval.domain.policies.evaluation_execution_policy import (
    EvaluationExecutionPolicy,
    ExecuteEvaluationRequest,
)
from command_eval.domain.policies.result_output_policy import (
    OutputResultRequest,
    ResultOutputPolicy,
)
from command_eval.domain.policies.test_case_create_policy import (
    CreateTestCaseRequest,
    TestCaseCreatePolicy,
)
from command_eval.domain.policies.test_input_build_policy import (
    BuildTestInputRequest,
    FileContentReader,
    TestInputBuildPolicy,
)
from command_eval.domain.ports.evaluation_port import EvaluationPort
from command_eval.domain.ports.execution_port import ExecutionPort
from command_eval.domain.ports.result_writer_port import ResultWriterPort
from command_eval.domain.value_objects.evaluation_config import EvaluationConfig
from command_eval.domain.value_objects.file_path import FilePath


@dataclass(frozen=True)
class EvaluationRequest:
    """Request to execute evaluation.

    Attributes:
        data_file_path: Path to the data file.
        config: Evaluation configuration.
    """

    data_file_path: FilePath
    config: EvaluationConfig


@dataclass(frozen=True)
class EvaluationUseCaseResult:
    """Result of the evaluation use case.

    Attributes:
        data_file: The loaded data file.
        test_inputs: All test inputs that were built.
        executions: All command executions.
        test_cases: All test cases that were created.
        evaluation: The evaluation result (None if no test cases passed).
        skipped_count: Number of test inputs that were skipped.
    """

    data_file: DataFile
    test_inputs: tuple[TestInput, ...]
    executions: tuple[Execution, ...]
    test_cases: tuple[TestCase, ...]
    evaluation: Optional[Evaluation]
    skipped_count: int

    @property
    def is_successful(self) -> bool:
        """Check if evaluation was successful."""
        return self.evaluation is not None and self.evaluation.is_successful

    @property
    def has_test_cases(self) -> bool:
        """Check if any test cases were created."""
        return len(self.test_cases) > 0


class EvaluationUseCase:
    """Main use case for executing evaluation.

    This orchestrates the complete evaluation flow by coordinating
    all domain policies and aggregates.
    """

    def __init__(
        self,
        data_file_parser: DataFileParser,
        file_content_reader: Optional[FileContentReader],
        execution_port: ExecutionPort,
        evaluation_port: EvaluationPort,
        result_writer_port: Optional[ResultWriterPort] = None,
    ) -> None:
        """Initialize the use case.

        Args:
            data_file_parser: Parser for reading data files.
            file_content_reader: Reader for file contents (for FILE sources).
            execution_port: Port for executing commands.
            evaluation_port: Port for executing evaluation.
            result_writer_port: Optional port for writing results to files.
        """
        self._data_file_load_policy = DataFileLoadPolicy(parser=data_file_parser)
        self._test_input_build_policy = TestInputBuildPolicy(
            file_reader=file_content_reader
        )
        self._command_execution_policy = CommandExecutionPolicy(
            execution_port=execution_port
        )
        self._test_case_create_policy = TestCaseCreatePolicy()
        self._evaluation_execution_policy = EvaluationExecutionPolicy(
            evaluation_port=evaluation_port
        )
        self._result_output_policy: Optional[ResultOutputPolicy] = None
        if result_writer_port:
            self._result_output_policy = ResultOutputPolicy(
                result_writer=result_writer_port
            )

    def execute(self, request: EvaluationRequest) -> EvaluationUseCaseResult:
        """Execute the evaluation use case.

        Args:
            request: The evaluation request.

        Returns:
            The evaluation result.
        """
        _logger.info("=" * 60)
        _logger.info("Starting evaluation use case")
        _logger.info("  Data file: %s", request.data_file_path.value)
        _logger.info("  Threshold: %.2f", request.config.threshold)

        # Step 1: Load data file
        _logger.info("-" * 40)
        _logger.info("Step 1: Loading data file...")
        load_result = self._data_file_load_policy.execute(
            LoadDataFileRequest(file_path=request.data_file_path)
        )
        data_file = load_result.data_file
        _logger.info("  Loaded %d items from data file", len(data_file.items))

        # Step 2: Build test inputs
        _logger.info("-" * 40)
        _logger.info("Step 2: Building test inputs...")
        build_result = self._test_input_build_policy.execute(
            BuildTestInputRequest(
                data_file=data_file,
                event=load_result.event,
            )
        )
        test_inputs = tuple(ti.test_input for ti in build_result.test_inputs)
        _logger.info("  Built %d test inputs", len(test_inputs))

        # Step 3 & 4: Execute commands and create test cases
        _logger.info("-" * 40)
        _logger.info("Step 3 & 4: Executing commands and creating test cases...")
        executions: list[Execution] = []
        test_cases: list[TestCase] = []
        skipped_count = 0

        for i, test_input_with_event in enumerate(build_result.test_inputs):
            test_input = test_input_with_event.test_input
            input_event = test_input_with_event.event

            _logger.info("  [%d/%d] Executing: %s",
                        i + 1, len(build_result.test_inputs),
                        test_input.command[:60] + "..."
                        if len(test_input.command) > 60 else test_input.command)
            _logger.debug("    Test input ID: %s", test_input.id)

            # Execute command
            exec_result = self._command_execution_policy.execute(
                ExecuteCommandRequest(
                    test_input=test_input,
                    event=input_event,
                )
            )
            executions.append(exec_result.execution)
            _logger.debug("    Execution status: %s", exec_result.execution.status)

            # Determine if this is the last test case
            is_last = i == len(build_result.test_inputs) - 1

            # Create test case
            tc_result = self._test_case_create_policy.execute(
                CreateTestCaseRequest(
                    test_input=test_input,
                    event=exec_result.event,
                    is_last_test_case=is_last,
                )
            )

            if tc_result.skipped:
                skipped_count += 1
                _logger.info("    -> SKIPPED")
            else:
                test_cases.append(tc_result.test_case)
                _logger.info("    -> OK (test case created)")

        _logger.info("  Executed %d commands, created %d test cases, skipped %d",
                    len(executions), len(test_cases), skipped_count)

        # Step 5: Execute evaluation (if we have test cases)
        _logger.info("-" * 40)
        _logger.info("Step 5: Executing evaluation...")
        evaluation: Optional[Evaluation] = None
        if test_cases:
            # Get the last test case's event for triggering
            last_tc = test_cases[-1]
            # Create a trigger event with is_last_test_case=True
            from command_eval.domain.events.test_case_created import TestCaseCreated

            trigger_event = TestCaseCreated(
                test_case_id=last_tc.id,
                test_input_id=last_tc.test_input_id,
                is_last_test_case=True,
            )

            _logger.info("  Evaluating %d test cases...", len(test_cases))
            eval_result = self._evaluation_execution_policy.execute(
                ExecuteEvaluationRequest(
                    test_cases=tuple(test_cases),
                    config=request.config,
                    trigger_event=trigger_event,
                )
            )
            evaluation = eval_result.evaluation

            if evaluation:
                _logger.info("  Overall score: %.2f", evaluation.result.overall_score)
                _logger.info("  Passed: %d, Failed: %d",
                            evaluation.result.passed_count,
                            evaluation.result.failed_count)
        else:
            _logger.info("  No test cases to evaluate")

        # Step 6: Output results (if output_config is set)
        if data_file.output_config and self._result_output_policy and evaluation:
            _logger.info("-" * 40)
            _logger.info("Step 6: Outputting results...")
            self._output_results(
                data_file=data_file,
                test_inputs=test_inputs,
                test_cases=tuple(test_cases),
                executions=tuple(executions),
                evaluation=evaluation,
            )

        _logger.info("=" * 60)

        return EvaluationUseCaseResult(
            data_file=data_file,
            test_inputs=test_inputs,
            executions=tuple(executions),
            test_cases=tuple(test_cases),
            evaluation=evaluation,
            skipped_count=skipped_count,
        )

    def _output_results(
        self,
        data_file: DataFile,
        test_inputs: tuple[TestInput, ...],
        test_cases: tuple[TestCase, ...],
        executions: tuple[Execution, ...],
        evaluation: Evaluation,
    ) -> None:
        """Output evaluation results to files.

        Args:
            data_file: The data file with output config.
            test_inputs: The test inputs.
            test_cases: The test cases.
            executions: The command executions.
            evaluation: The evaluation result.
        """
        if not data_file.output_config or not self._result_output_policy:
            return

        # Generate timestamp directory once for all items
        timestamp_dir = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        # Get test case results by test input ID
        result_by_input_id: dict[str, dict[str, Any]] = {}
        if evaluation.result.details:
            for tc_result in evaluation.result.details:
                # Find the test input ID for this test case
                for tc in test_cases:
                    if tc.id == tc_result.test_case_id:
                        input_id = str(tc.test_input_id)
                        if input_id not in result_by_input_id:
                            result_by_input_id[input_id] = {
                                "evaluation_results": []
                            }
                        # Add evaluation result for each metric result
                        for mr in tc_result.metric_results:
                            result_by_input_id[input_id]["evaluation_results"].append({
                                "sdk": mr.sdk,
                                "metric": mr.metric,
                                "score": mr.score,
                                "success": mr.passed,
                                "reason": mr.reason,
                                "metadata": mr.metadata,
                            })
                        break

        # Build a mapping from test_input_id to test_case for actual output
        tc_by_input_id: dict[str, TestCase] = {}
        for tc in test_cases:
            tc_by_input_id[str(tc.test_input_id)] = tc

        # Build a mapping from test_input_id to execution for console_output
        exec_by_input_id: dict[str, Execution] = {}
        for ex in executions:
            exec_by_input_id[str(ex.test_input_id)] = ex

        # Output result for each test input
        # Note: test_inputs are in the same order as data_file.items
        for i, test_input in enumerate(test_inputs):
            input_id = str(test_input.id)
            # Get effective_id from the corresponding data item
            effective_id = data_file.items[i].effective_id if i < len(data_file.items) else f"item_{i}"

            # Get actual output from test case
            actual_output = ""
            if input_id in tc_by_input_id:
                actual_output = tc_by_input_id[input_id].actual

            # Get console output from execution
            console_output = None
            if input_id in exec_by_input_id:
                exec_result = exec_by_input_id[input_id].result
                if exec_result:
                    console_output = exec_result.console_output

            # Build result data
            result_data: dict[str, Any] = {
                "query": test_input.query,
                "actual_output": actual_output,
            }

            # Add console output if available
            if console_output:
                result_data["console_output"] = console_output

            # Add evaluation results if available
            if input_id in result_by_input_id:
                result_data.update(result_by_input_id[input_id])

            # Output the result
            output_request = OutputResultRequest(
                output_config=data_file.output_config,
                item_id=effective_id,
                result_data=result_data,
                timestamp_dir=timestamp_dir,
            )

            output_result = self._result_output_policy.execute(output_request)

            if output_result.write_response.success:
                _logger.info("  Output: %s", output_result.write_response.output_path)
            else:
                _logger.warning(
                    "  Failed to output %s: %s",
                    effective_id,
                    output_result.write_response.error_message,
                )

            # Print to stdout
            print(output_result.stdout_output)
