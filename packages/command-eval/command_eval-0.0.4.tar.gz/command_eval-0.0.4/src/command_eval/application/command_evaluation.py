"""Command evaluation.

Main entry point that orchestrates the complete evaluation flow:
1. Load data file
2. Build test inputs
3. Execute commands
4. Create test cases
5. Execute evaluation
6. Output results (optional)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
    BatchOutputResultRequest,
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
class CommandEvaluationResult:
    """Result of command evaluation.

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


class CommandEvaluation:
    """Main entry point for command evaluation.

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

    def execute(self, request: EvaluationRequest) -> CommandEvaluationResult:
        """Execute command evaluation.

        Args:
            request: The evaluation request.

        Returns:
            The evaluation result.
        """
        _logger.info("=" * 60)
        _logger.info("Starting command evaluation")
        _logger.info("  Data file: %s", request.data_file_path.value)
        _logger.info("  Threshold: %.2f", request.config.default_threshold)

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
            _logger.info("  Evaluating %d test cases...", len(test_cases))
            eval_result = self._evaluation_execution_policy.execute(
                ExecuteEvaluationRequest(
                    test_cases=tuple(test_cases),
                    config=request.config,
                )
            )
            evaluation = eval_result.evaluation

            if evaluation:
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

        # Final summary
        _logger.info("-" * 40)
        _logger.info("Summary:")
        _logger.info("  Commands executed: %d", len(executions))
        _logger.info("  Test cases created: %d", len(test_cases))
        _logger.info("  Skipped: %d", skipped_count)

        if evaluation:
            all_passed = (
                evaluation.result.failed_count == 0
                and evaluation.result.passed_count > 0
            )
            if all_passed:
                _logger.info("  Result: ALL TESTS PASSED")
            else:
                _logger.info("  Result: SOME TESTS FAILED")
        else:
            _logger.info("  Result: NO EVALUATION PERFORMED")

        _logger.info("=" * 60)

        return CommandEvaluationResult(
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
        """Output evaluation results to files."""
        if not data_file.output_config or not self._result_output_policy:
            return

        result = self._result_output_policy.execute_batch(
            BatchOutputResultRequest(
                data_file=data_file,
                test_inputs=test_inputs,
                test_cases=test_cases,
                executions=executions,
                evaluation=evaluation,
            )
        )

        _logger.info(
            "  Output complete: %d success, %d failed",
            result.success_count,
            result.failure_count,
        )
