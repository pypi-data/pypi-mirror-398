"""Evaluation execution policy.

Policy that executes evaluation when all test cases are generated.
"""

from __future__ import annotations

from dataclasses import dataclass

from command_eval.domain.aggregates.evaluation import Evaluation
from command_eval.domain.aggregates.test_case import TestCase
from command_eval.domain.events.evaluation_completed import EvaluationCompleted
from command_eval.domain.ports.evaluation_port import EvaluationPort
from command_eval.domain.value_objects.evaluation_config import EvaluationConfig
from command_eval.domain.value_objects.ids.test_case_id import TestCaseId


@dataclass(frozen=True)
class ExecuteEvaluationRequest:
    """Request to execute evaluation.

    Attributes:
        test_cases: The test cases to evaluate.
        config: Evaluation configuration.
    """

    test_cases: tuple[TestCase, ...]
    config: EvaluationConfig


@dataclass(frozen=True)
class ExecuteEvaluationResult:
    """Result of executing evaluation.

    Attributes:
        evaluation: The evaluation aggregate.
        event: The EvaluationCompleted event.
    """

    evaluation: Evaluation
    event: EvaluationCompleted


class EvaluationExecutionPolicy:
    """Policy for executing evaluation when all test cases are generated.

    This policy is responsible for:
    - Creating an Evaluation aggregate
    - Executing evaluation using the EvaluationPort
    - Emitting an EvaluationCompleted event
    """

    def __init__(self, evaluation_port: EvaluationPort) -> None:
        """Initialize the policy.

        Args:
            evaluation_port: Port for executing evaluation.
        """
        self._evaluation_port = evaluation_port

    def execute(self, request: ExecuteEvaluationRequest) -> ExecuteEvaluationResult:
        """Execute the evaluation execution policy.

        Args:
            request: The request containing test cases and config.

        Returns:
            The result containing the evaluation and event.

        Raises:
            ValueError: If no test cases are provided.
        """
        # Validate that we have test cases
        if not request.test_cases:
            raise ValueError("At least one test case is required for evaluation")

        # Extract test case IDs
        test_case_ids: tuple[TestCaseId, ...] = tuple(
            tc.id for tc in request.test_cases
        )

        # Create evaluation aggregate
        evaluation = Evaluation.create(
            test_case_ids=test_case_ids,
            config=request.config,
        )

        # Execute evaluation
        event = evaluation.evaluate(
            port=self._evaluation_port,
            test_cases=request.test_cases,
        )

        return ExecuteEvaluationResult(evaluation=evaluation, event=event)
