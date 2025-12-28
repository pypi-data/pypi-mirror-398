"""DeepEval-based evaluation adapter.

Uses deepeval SDK for LLM evaluation.
SDK-specific parameters are extracted from evaluation_specs via DeepEvalParamParser.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    MetricConfig,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.metric_registry import (
    DeepEvalMetricRegistry,
    get_default_registry,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.param_parser import (
    DeepEvalParamParser,
)

if TYPE_CHECKING:
    from deepeval.evaluate import EvaluateResult
    from deepeval.metrics import BaseMetric
    from deepeval.metrics.indicator import MetricData
    from deepeval.test_case import LLMTestCase


class DeepEvalAdapter(BaseGroupedEvaluationAdapter):
    """DeepEval-based implementation of EvaluationPort.

    SDK-specific logic:
    - LLMTestCase construction
    - deepeval.evaluate API call
    - Metric creation via registry
    - Result extraction from deepeval response
    """

    def __init__(
        self,
        model: str | None = None,
        param_parser: DeepEvalParamParser | None = None,
        metric_registry: DeepEvalMetricRegistry | None = None,
    ) -> None:
        self._model = model
        self._param_parser = param_parser or DeepEvalParamParser()
        self._metric_registry = metric_registry or get_default_registry()

    def get_sdk_name(self) -> str:
        return "deepeval"

    def supports_metric(self, metric_type: MetricType) -> bool:
        return self._metric_registry.supports_metric(metric_type.value)

    def _build_sdk_test_case(
        self,
        tc: EvaluationTestCase,
        spec: EvaluationSpec,
    ) -> LLMTestCase:
        """Convert EvaluationTestCase to DeepEval LLMTestCase."""
        from deepeval.test_case import LLMTestCase

        params = self._param_parser.parse(spec.params)

        return LLMTestCase(
            input=tc.input,
            actual_output=tc.actual,
            expected_output=params.expected,
            context=list(params.context) if params.context else None,
            retrieval_context=list(params.retrieval_context) if params.retrieval_context else None,
            name=params.name,
            completion_time=params.completion_time if params.completion_time is not None else tc.execution_time_ms / 1000.0,
        )

    def _evaluate_group(
        self,
        metric_name: str,
        items: list[tuple[EvaluationTestCase, LLMTestCase]],
        config: EvaluationConfig,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Evaluate a group of test cases for a single metric using deepeval."""
        try:
            from deepeval import evaluate as deepeval_evaluate
        except ImportError as e:
            raise ImportError(
                "deepeval is not installed. Please install it with: pip install deepeval"
            ) from e

        tcs = [item[0] for item in items]
        deepeval_tcs = [item[1] for item in items]

        metric = self._create_metric(config, metric_name, tcs)
        results = deepeval_evaluate(test_cases=deepeval_tcs, metrics=[metric])

        self._collect_metric_results(tcs, results, config.default_threshold, metric_results_by_tc)

    def _create_metric(
        self,
        config: EvaluationConfig,
        metric_name: str,
        test_cases: list[EvaluationTestCase],
    ) -> BaseMetric:
        """Create a single deepeval metric."""
        if not self._metric_registry.supports_metric(metric_name):
            raise ValueError(f"Unsupported metric: {metric_name}")

        metric_config = self._build_metric_config(config, metric_name, test_cases)
        return self._metric_registry.create_metric(metric_name, metric_config)

    def _collect_metric_results(
        self,
        test_cases: list[EvaluationTestCase],
        results: EvaluateResult,
        threshold: float,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Collect metric results from deepeval evaluation."""
        test_results = getattr(results, "test_results", [])

        for i, test_result in enumerate(test_results):
            if i >= len(test_cases):
                break

            tc = test_cases[i]
            metric_data_list = getattr(test_result, "metrics_data", [])

            # Since we pass only one metric to deepeval_evaluate,
            # there should be only one metric result per test case
            for metric_data in metric_data_list:
                name = getattr(metric_data, "name", "unknown")
                score = getattr(metric_data, "score", 0.0)
                reason = getattr(metric_data, "reason", None)

                metric_results_by_tc[tc.id].append(
                    PortMetricResult(
                        sdk="deepeval",
                        metric=name,
                        score=score,
                        passed=score >= threshold,
                        reason=reason,
                        metadata=self._extract_metric_metadata(metric_data),
                    )
                )

    def _build_metric_config(
        self,
        config: EvaluationConfig,
        metric_name: str,
        test_cases: list[EvaluationTestCase],
    ) -> MetricConfig:
        """Build MetricConfig from test case specs."""
        params = self._extract_metric_params(metric_name, test_cases)
        return MetricConfig(
            threshold=config.default_threshold,
            model=self._model,
            include_reason=params.get("include_reason", True),
            strict_mode=params.get("strict_mode", False),
            async_mode=params.get("async_mode", True),
            verbose_mode=params.get("verbose_mode", False),
            extra_params={
                k: v for k, v in params.items()
                if k not in {"threshold", "model", "include_reason", "strict_mode", "async_mode", "verbose_mode"}
            },
        )

    def _extract_metric_params(
        self,
        metric_name: str,
        test_cases: list[EvaluationTestCase],
    ) -> dict[str, Any]:
        """Extract metric params from the first matching test case."""
        for tc in test_cases:
            for spec in tc.evaluation_specs:
                if spec.sdk == "deepeval" and spec.metric.lower() == metric_name.lower():
                    return dict(spec.params)
        return {}

    def _extract_metric_metadata(self, metric_data: MetricData) -> dict[str, object]:
        """Extract additional metadata from DeepEval metric data."""
        metadata: dict[str, object] = {}
        for attr in ["threshold", "success", "strict_mode", "evaluation_model", "evaluation_cost", "verbose_logs", "error"]:
            value = getattr(metric_data, attr, None)
            if value is not None:
                metadata[attr] = value
        return metadata
