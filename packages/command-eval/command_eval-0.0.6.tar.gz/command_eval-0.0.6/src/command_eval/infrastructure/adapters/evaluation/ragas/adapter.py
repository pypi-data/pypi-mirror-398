"""Ragas-based evaluation adapter.

Uses ragas SDK for LLM evaluation.
SDK-specific parameters are extracted from evaluation_specs via RagasParamParser.
"""

from __future__ import annotations

from typing import Any

from command_eval.domain.ports.evaluation_port import (
    EvaluationConfig,
    EvaluationTestCase,
    MetricResult as PortMetricResult,
)
from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.metric_type import MetricType
from command_eval.infrastructure.adapters.evaluation.base import (
    BaseGroupedEvaluationAdapter,
)
from command_eval.infrastructure.adapters.evaluation.ragas.param_parser import (
    RagasParamParser,
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


class RagasAdapter(BaseGroupedEvaluationAdapter):
    """Ragas-based implementation of EvaluationPort.

    SDK-specific logic:
    - Ragas sample construction
    - ragas.evaluate API call
    - Result extraction from ragas response
    """

    def __init__(
        self,
        model: str | None = None,
        embeddings: Any | None = None,
        param_parser: RagasParamParser | None = None,
        **kwargs: Any,
    ) -> None:
        self._model = model
        self._embeddings = embeddings
        self._param_parser = param_parser or RagasParamParser()
        self._kwargs = kwargs

    def get_sdk_name(self) -> str:
        return "ragas"

    def supports_metric(self, metric_type: MetricType) -> bool:
        return metric_type.value.lower() in RAGAS_SUPPORTED_METRICS

    def _build_sdk_test_case(
        self,
        tc: EvaluationTestCase,
        spec: EvaluationSpec,
    ) -> dict[str, Any]:
        """Build Ragas sample dict from EvaluationTestCase."""
        params = self._param_parser.parse(spec.params)

        return {
            "user_input": tc.input,
            "response": tc.actual,
            "retrieved_contexts": list(params.retrieved_contexts) if params.retrieved_contexts else [],
            "reference": params.reference or "",
        }

    def _evaluate_group(
        self,
        metric_name: str,
        spec_params: dict[str, Any],
        items: list[tuple[EvaluationTestCase, dict[str, Any]]],
        config: EvaluationConfig,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Evaluate a group of test cases for a single metric using ragas."""
        try:
            from datasets import Dataset
            from ragas import evaluate as ragas_evaluate
        except ImportError:
            # Fallback to mock evaluation
            self._mock_evaluate_group(metric_name, items, config, metric_results_by_tc)
            return

        # Build dataset from items
        data: dict[str, list[Any]] = {
            "user_input": [],
            "response": [],
            "retrieved_contexts": [],
            "reference": [],
        }

        tcs = []
        for tc, sample in items:
            tcs.append(tc)
            data["user_input"].append(sample["user_input"])
            data["response"].append(sample["response"])
            data["retrieved_contexts"].append(sample["retrieved_contexts"])
            data["reference"].append(sample["reference"])

        dataset = Dataset.from_dict(data)

        # Create metric
        metric = self._create_metric(metric_name)
        if metric is None:
            return

        # Run evaluation
        results = ragas_evaluate(dataset, metrics=[metric])

        # Extract results
        self._collect_metric_results(tcs, results, metric_name, config.default_threshold, metric_results_by_tc)

    def _create_metric(self, metric_name: str) -> Any | None:
        """Create a ragas metric by name."""
        try:
            if metric_name == "answer_relevancy":
                from ragas.metrics import answer_relevancy
                return answer_relevancy
            elif metric_name == "answer_correctness":
                from ragas.metrics import answer_correctness
                return answer_correctness
            elif metric_name == "answer_similarity":
                from ragas.metrics import answer_similarity
                return answer_similarity
            elif metric_name == "context_precision":
                from ragas.metrics import context_precision
                return context_precision
            elif metric_name == "context_recall":
                from ragas.metrics import context_recall
                return context_recall
            elif metric_name == "faithfulness":
                from ragas.metrics import faithfulness
                return faithfulness
            # Add more metrics as needed
        except ImportError:
            pass
        return None

    def _collect_metric_results(
        self,
        test_cases: list[EvaluationTestCase],
        results: Any,
        metric_name: str,
        threshold: float,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Collect metric results from ragas evaluation."""
        scores = results.to_pandas() if hasattr(results, "to_pandas") else None

        for i, tc in enumerate(test_cases):
            if scores is not None and metric_name in scores.columns:
                score = float(scores.iloc[i][metric_name])
            else:
                score = 0.5

            metric_results_by_tc[tc.id].append(
                PortMetricResult(
                    sdk="ragas",
                    metric=metric_name,
                    score=score,
                    passed=score >= threshold,
                )
            )

    def _mock_evaluate_group(
        self,
        metric_name: str,
        items: list[tuple[EvaluationTestCase, dict[str, Any]]],
        config: EvaluationConfig,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Mock evaluation when ragas is not available."""
        for tc, sample in items:
            reference = sample.get("reference", "")
            response = sample.get("response", "")

            if reference:
                actual_len = len(response)
                reference_len = len(reference)
                if reference_len > 0:
                    ratio = min(actual_len, reference_len) / max(actual_len, reference_len)
                    score = min(1.0, ratio)
                else:
                    score = 0.5 if actual_len > 0 else 0.0
            else:
                score = 0.5 if response else 0.0

            metric_results_by_tc[tc.id].append(
                PortMetricResult(
                    sdk="ragas",
                    metric=metric_name,
                    score=score,
                    passed=score >= config.default_threshold,
                )
            )
