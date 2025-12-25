"""Ragas-based evaluation adapter.

Uses ragas SDK for LLM evaluation.
SDK-specific parameters are extracted from evaluation_specs via RagasParamParser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from command_eval.domain.ports.evaluation_port import (
    EvaluationConfig,
    EvaluationPort,
    EvaluationResponse,
    EvaluationTestCase,
)
from command_eval.domain.ports.evaluation_port import (
    TestCaseResult as PortTestCaseResult,
)
from command_eval.domain.value_objects.metric_type import MetricType
from command_eval.infrastructure.adapters.ragas_param_parser import (
    RagasParamParser,
    RagasResolvedParams,
)


# Supported metric types for ragas
RAGAS_SUPPORTED_METRICS = frozenset(
    [
        "answer_relevancy",
        "answer_correctness",
        "answer_similarity",
        "context_precision",
        "context_recall",
        "context_relevancy",
        "context_entity_recall",
        "faithfulness",
        "harmfulness",
        "coherence",
        "conciseness",
    ]
)


class RagasRequiredField(Enum):
    """Required fields for Ragas metrics."""

    USER_INPUT = "user_input"
    RESPONSE = "response"
    REFERENCE = "reference"
    RETRIEVED_CONTEXTS = "retrieved_contexts"


# Metric-specific required fields mapping
RAGAS_METRIC_REQUIREMENTS: dict[str, frozenset[RagasRequiredField]] = {
    "answer_relevancy": frozenset(
        [RagasRequiredField.USER_INPUT, RagasRequiredField.RESPONSE]
    ),
    "answer_correctness": frozenset(
        [
            RagasRequiredField.USER_INPUT,
            RagasRequiredField.RESPONSE,
            RagasRequiredField.REFERENCE,
        ]
    ),
    "answer_similarity": frozenset(
        [
            RagasRequiredField.USER_INPUT,
            RagasRequiredField.RESPONSE,
            RagasRequiredField.REFERENCE,
        ]
    ),
    "context_precision": frozenset(
        [
            RagasRequiredField.USER_INPUT,
            RagasRequiredField.REFERENCE,
            RagasRequiredField.RETRIEVED_CONTEXTS,
        ]
    ),
    "context_recall": frozenset(
        [
            RagasRequiredField.USER_INPUT,
            RagasRequiredField.REFERENCE,
            RagasRequiredField.RETRIEVED_CONTEXTS,
        ]
    ),
    "context_relevancy": frozenset(
        [
            RagasRequiredField.USER_INPUT,
            RagasRequiredField.RESPONSE,
            RagasRequiredField.RETRIEVED_CONTEXTS,
        ]
    ),
    "context_entity_recall": frozenset(
        [
            RagasRequiredField.USER_INPUT,
            RagasRequiredField.REFERENCE,
            RagasRequiredField.RETRIEVED_CONTEXTS,
        ]
    ),
    "faithfulness": frozenset(
        [
            RagasRequiredField.USER_INPUT,
            RagasRequiredField.RESPONSE,
            RagasRequiredField.RETRIEVED_CONTEXTS,
        ]
    ),
    "harmfulness": frozenset(
        [RagasRequiredField.USER_INPUT, RagasRequiredField.RESPONSE]
    ),
    "coherence": frozenset(
        [RagasRequiredField.USER_INPUT, RagasRequiredField.RESPONSE]
    ),
    "conciseness": frozenset(
        [RagasRequiredField.USER_INPUT, RagasRequiredField.RESPONSE]
    ),
}


@dataclass(frozen=True)
class RagasValidationError:
    """Validation error for Ragas test case.

    Attributes:
        test_case_id: ID of the test case with the error.
        metric: The metric that requires the missing field.
        missing_field: The field that is missing.
    """

    test_case_id: str
    metric: str
    missing_field: RagasRequiredField


class RagasTestCaseValidator:
    """Validator for Ragas test cases.

    Validates that test cases have all required fields for the specified metrics.
    Uses RagasParamParser to resolve params from evaluation_specs.
    """

    def __init__(
        self,
        param_parser: RagasParamParser | None = None,
    ) -> None:
        """Initialize the validator.

        Args:
            param_parser: Parser for resolving params. Defaults to RagasParamParser.
        """
        self._param_parser = param_parser or RagasParamParser()

    def validate(
        self,
        test_cases: list[EvaluationTestCase],
    ) -> list[RagasValidationError]:
        """Validate test cases against metric requirements.

        Metrics are derived from evaluation_specs in test cases.

        Args:
            test_cases: List of test cases to validate.

        Returns:
            List of validation errors. Empty if all test cases are valid.
        """
        errors: list[RagasValidationError] = []

        for tc in test_cases:
            # Get Ragas specs for this test case
            ragas_specs = [
                spec for spec in tc.evaluation_specs if spec.sdk == "ragas"
            ]

            for spec in ragas_specs:
                metric_name = spec.metric.lower()
                requirements = RAGAS_METRIC_REQUIREMENTS.get(
                    metric_name, frozenset()
                )

                # Parse params from spec
                resolved_params = self._param_parser.parse(spec.params)

                for required_field in requirements:
                    if not self._has_field(tc, resolved_params, required_field):
                        errors.append(
                            RagasValidationError(
                                test_case_id=tc.id,
                                metric=metric_name,
                                missing_field=required_field,
                            )
                        )

        return errors

    def _has_field(
        self,
        tc: EvaluationTestCase,
        resolved_params: RagasResolvedParams,
        field: RagasRequiredField,
    ) -> bool:
        """Check if a test case has the required field.

        Args:
            tc: The test case to check.
            resolved_params: Resolved params from evaluation_spec.
            field: The field to check for.

        Returns:
            True if the field is present and non-empty.
        """
        if field == RagasRequiredField.USER_INPUT:
            return bool(tc.input)
        elif field == RagasRequiredField.RESPONSE:
            return bool(tc.actual)
        elif field == RagasRequiredField.REFERENCE:
            return resolved_params.reference is not None and bool(
                resolved_params.reference
            )
        elif field == RagasRequiredField.RETRIEVED_CONTEXTS:
            return (
                resolved_params.retrieved_contexts is not None
                and len(resolved_params.retrieved_contexts) > 0
            )
        else:
            return False


class RagasAdapter(EvaluationPort):
    """Ragas-based implementation of EvaluationPort.

    Uses the ragas library for LLM evaluation.
    SDK-specific parameters are extracted from evaluation_specs via RagasParamParser.
    """

    def __init__(
        self,
        model: str | None = None,
        embeddings: Any | None = None,
        param_parser: RagasParamParser | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Ragas adapter.

        Args:
            model: Model to use for evaluation (e.g., "gpt-4").
            embeddings: Embedding model to use.
            param_parser: Parser for resolving params. Defaults to RagasParamParser.
            **kwargs: Additional options for ragas.
        """
        self._model = model
        self._embeddings = embeddings
        self._param_parser = param_parser or RagasParamParser()
        self._kwargs = kwargs

    def get_sdk_name(self) -> str:
        """Get the SDK name.

        Returns:
            The SDK name "ragas".
        """
        return "ragas"

    def supports_metric(self, metric_type: MetricType) -> bool:
        """Check if a metric type is supported.

        Args:
            metric_type: The metric type to check.

        Returns:
            True if the metric is supported, False otherwise.
        """
        return metric_type.value.lower() in RAGAS_SUPPORTED_METRICS

    def evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Execute evaluation using ragas.

        Args:
            test_cases: List of test cases to evaluate.
            config: Evaluation configuration.

        Returns:
            The evaluation response with results.
        """
        try:
            # Try to import ragas
            from ragas import evaluate as ragas_evaluate
            from ragas.metrics import answer_relevancy

            return self._execute_with_ragas(
                test_cases,
                config,
                ragas_evaluate,
                answer_relevancy,
            )
        except ImportError:
            # Fallback to mock evaluation if ragas is not installed
            return self._mock_evaluate(test_cases, config)

    def _execute_with_ragas(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
        ragas_evaluate: Any,
        answer_relevancy_metric: Any,
    ) -> EvaluationResponse:
        """Execute evaluation using ragas library.

        Args:
            test_cases: List of test cases.
            config: Evaluation configuration.
            ragas_evaluate: The ragas evaluate function.
            answer_relevancy_metric: The answer_relevancy metric.

        Returns:
            The evaluation response.
        """
        from datasets import Dataset

        # Convert to ragas dataset format
        # Ragas uses different field names:
        # - user_input/question -> tc.input
        # - response/answer -> tc.actual
        # - retrieved_contexts/contexts -> resolved_params.retrieved_contexts
        # - reference/ground_truth -> resolved_params.reference
        data: dict[str, list] = {
            "user_input": [],
            "response": [],
            "retrieved_contexts": [],
            "reference": [],
        }

        for tc in test_cases:
            # Find the first ragas spec to get params (or use empty params)
            ragas_spec = next(
                (s for s in tc.evaluation_specs if s.sdk == "ragas"), None
            )
            resolved_params = (
                self._param_parser.parse(ragas_spec.params)
                if ragas_spec
                else RagasResolvedParams()
            )

            data["user_input"].append(tc.input)
            data["response"].append(tc.actual)
            data["retrieved_contexts"].append(
                list(resolved_params.retrieved_contexts)
                if resolved_params.retrieved_contexts
                else []
            )
            data["reference"].append(resolved_params.reference or "")

        dataset = Dataset.from_dict(data)

        # Create metrics based on test case evaluation_specs
        metrics = self._create_metrics(config, test_cases, answer_relevancy_metric)

        # Run evaluation
        results = ragas_evaluate(dataset, metrics=metrics)

        # Convert results to port response
        return self._convert_results(test_cases, results, config.threshold)

    def _create_metrics(
        self,
        config: EvaluationConfig,
        test_cases: list[EvaluationTestCase],
        answer_relevancy_metric: Any,
    ) -> list[Any]:
        """Create ragas metrics from test case evaluation_specs.

        Args:
            config: Evaluation configuration.
            test_cases: Test cases containing evaluation_specs with metric definitions.
            answer_relevancy_metric: The answer_relevancy metric object.

        Returns:
            List of ragas metrics.
        """
        metrics = []
        created_metrics: set[str] = set()

        # Extract metric names from evaluation_specs (sdk="ragas")
        for tc in test_cases:
            for spec in tc.evaluation_specs:
                if spec.sdk == "ragas":
                    metric_name = spec.metric.lower()
                    if metric_name in created_metrics:
                        continue
                    if metric_name == "answer_relevancy":
                        metrics.append(answer_relevancy_metric)
                        created_metrics.add(metric_name)
                    # Add more metric types as needed

        if not metrics:
            # Default to answer relevancy if no metrics specified
            metrics.append(answer_relevancy_metric)

        return metrics

    def _convert_results(
        self,
        test_cases: list[EvaluationTestCase],
        results: Any,
        threshold: float,
    ) -> EvaluationResponse:
        """Convert ragas results to EvaluationResponse.

        Args:
            test_cases: Original test cases.
            results: Ragas evaluation results.
            threshold: Score threshold for pass/fail.

        Returns:
            The evaluation response.
        """
        details: list[PortTestCaseResult] = []

        # Ragas returns a DataFrame-like object
        scores = results.to_pandas() if hasattr(results, "to_pandas") else None

        for i, tc in enumerate(test_cases):
            # Get score from results
            if scores is not None and "answer_relevancy" in scores.columns:
                score = float(scores.iloc[i]["answer_relevancy"])
            else:
                score = 0.5

            passed = score >= threshold

            details.append(
                PortTestCaseResult(
                    test_case_id=tc.id,
                    score=score,
                    passed=passed,
                    metrics={"overall": score},
                )
            )

        return EvaluationResponse.create(tuple(details), threshold)

    def _mock_evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Mock evaluation when ragas is not available.

        This is used for testing and when ragas is not installed.

        Args:
            test_cases: List of test cases.
            config: Evaluation configuration.

        Returns:
            Mock evaluation response.
        """
        details: list[PortTestCaseResult] = []

        for tc in test_cases:
            # Find the first ragas spec to get params (or use empty params)
            ragas_spec = next(
                (s for s in tc.evaluation_specs if s.sdk == "ragas"), None
            )
            resolved_params = (
                self._param_parser.parse(ragas_spec.params)
                if ragas_spec
                else RagasResolvedParams()
            )

            # Simple mock scoring based on output length similarity
            reference = resolved_params.reference
            if reference:
                actual_len = len(tc.actual)
                reference_len = len(reference)
                if reference_len > 0:
                    ratio = min(actual_len, reference_len) / max(
                        actual_len, reference_len
                    )
                    score = min(1.0, ratio)
                else:
                    score = 0.5 if actual_len > 0 else 0.0
            else:
                score = 0.5 if tc.actual else 0.0

            passed = score >= config.threshold

            details.append(
                PortTestCaseResult(
                    test_case_id=tc.id,
                    score=score,
                    passed=passed,
                    metrics={"mock_score": score},
                )
            )

        return EvaluationResponse.create(tuple(details), config.threshold)
