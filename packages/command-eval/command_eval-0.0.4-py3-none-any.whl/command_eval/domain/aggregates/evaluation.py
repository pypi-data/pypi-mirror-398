"""Evaluation aggregate root.

Manages evaluation execution and results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from command_eval.domain.aggregates.test_case import TestCase
from command_eval.domain.entities.evaluation_result import EvaluationResult
from command_eval.domain.entities.metric_result import (
    MetricResult as DomainMetricResult,
)
from command_eval.domain.entities.test_case_result import (
    TestCaseResult as DomainTestCaseResult,
)
from command_eval.domain.events.evaluation_completed import EvaluationCompleted
from command_eval.domain.ports.evaluation_port import (
    EvaluationConfig as PortEvaluationConfig,
)
from command_eval.domain.ports.evaluation_port import (
    EvaluationPort,
    EvaluationTestCase,
)
from command_eval.domain.value_objects.evaluation_config import EvaluationConfig
from command_eval.domain.value_objects.evaluation_status import EvaluationStatus
from command_eval.domain.value_objects.ids.evaluation_id import EvaluationId
from command_eval.domain.value_objects.ids.test_case_id import TestCaseId


@dataclass
class Evaluation:
    """Aggregate root for evaluation management.

    Attributes:
        id: Unique identifier for this evaluation.
        test_case_ids: IDs of test cases to evaluate.
        config: Evaluation configuration.
        status: Current evaluation status.
        result: Evaluation result (optional, set after completion).
        started_at: When the evaluation started.
        completed_at: When the evaluation completed (optional).
    """

    id: EvaluationId
    test_case_ids: tuple[TestCaseId, ...]
    config: EvaluationConfig
    status: EvaluationStatus = EvaluationStatus.PENDING
    result: Optional[EvaluationResult] = None
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate aggregate invariants."""
        if not self.test_case_ids:
            raise ValueError("At least one test case is required")

    @classmethod
    def create(
        cls,
        test_case_ids: tuple[TestCaseId, ...],
        config: EvaluationConfig,
    ) -> Evaluation:
        """Create a new Evaluation in PENDING state.

        Args:
            test_case_ids: IDs of test cases to evaluate.
            config: Evaluation configuration.

        Returns:
            A new Evaluation instance.
        """
        return cls(
            id=EvaluationId.generate(),
            test_case_ids=test_case_ids,
            config=config,
            status=EvaluationStatus.PENDING,
        )

    def evaluate(
        self,
        port: EvaluationPort,
        test_cases: tuple[TestCase, ...],
    ) -> EvaluationCompleted:
        """Execute evaluation using the provided port.

        Args:
            port: The evaluation port to use.
            test_cases: The test cases to evaluate.

        Returns:
            An EvaluationCompleted event.

        Raises:
            ValueError: If evaluation has already been completed or
                        if test cases don't match the registered IDs.
        """
        if self.status in (EvaluationStatus.COMPLETED, EvaluationStatus.FAILED):
            raise ValueError("Evaluation has already been completed")

        # Validate test cases match registered IDs
        provided_ids = {tc.id for tc in test_cases}
        expected_ids = set(self.test_case_ids)
        if provided_ids != expected_ids:
            raise ValueError("Provided test cases do not match registered IDs")

        self.status = EvaluationStatus.RUNNING

        # Convert domain test cases to port test cases
        # SDK-specific params are stored in evaluation_specs and parsed by Infrastructure layer
        port_test_cases = [
            EvaluationTestCase(
                id=str(tc.id.value),
                input=tc.input,
                actual=tc.actual,
                execution_time_ms=tc.execution_time_ms,
                evaluation_specs=tc.evaluation_specs,
            )
            for tc in test_cases
        ]

        # Convert domain config to port config
        port_config = PortEvaluationConfig(
            default_threshold=self.config.default_threshold,
            verbose_mode=self.config.verbose_mode,
            options=self.config.options,
        )

        try:
            response = port.evaluate(port_test_cases, port_config)

            # Convert port response to domain result
            domain_results = tuple(
                DomainTestCaseResult(
                    test_case_id=TestCaseId(r.test_case_id),
                    metric_results=tuple(
                        DomainMetricResult(
                            sdk=mr.sdk,
                            metric=mr.metric,
                            score=mr.score,
                            passed=mr.passed,
                            reason=mr.reason,
                            metadata=mr.metadata,
                        )
                        for mr in r.metric_results
                    ),
                )
                for r in response.details
            )

            self.result = EvaluationResult(
                passed_count=response.passed_count,
                failed_count=response.failed_count,
                total_count=response.total_count,
                is_all_passed=response.is_all_passed,
                details=domain_results,
            )

            self.status = EvaluationStatus.COMPLETED
        except Exception:
            self.status = EvaluationStatus.FAILED
            raise

        self.completed_at = datetime.now(timezone.utc)

        return EvaluationCompleted(
            evaluation_id=self.id,
            passed_count=self.result.passed_count,
            failed_count=self.result.failed_count,
            total_count=self.result.total_count,
            is_all_passed=self.result.is_all_passed,
        )

    @property
    def is_completed(self) -> bool:
        """Check if evaluation has completed (success or failure)."""
        return self.status in (EvaluationStatus.COMPLETED, EvaluationStatus.FAILED)

    @property
    def is_successful(self) -> bool:
        """Check if evaluation completed successfully."""
        return self.status == EvaluationStatus.COMPLETED
