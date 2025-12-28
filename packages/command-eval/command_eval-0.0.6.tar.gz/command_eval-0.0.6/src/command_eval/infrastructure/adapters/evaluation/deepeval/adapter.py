"""DeepEval-based evaluation adapter.

Uses deepeval SDK for LLM evaluation.
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
    LLM_TEST_CASE_LIST_PARAMS,
    LLM_TEST_CASE_PARAMS,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.metric_registry import (
    DeepEvalMetricRegistry,
)
from command_eval.infrastructure.adapters.evaluation.file_param_resolver import (
    FileParamResolver,
)

if TYPE_CHECKING:
    from deepeval.evaluate import EvaluateResult
    from deepeval.metrics import BaseMetric
    from deepeval.test_case import LLMTestCase
    from deepeval.test_run import MetricData


class DeepEvalAdapter(BaseGroupedEvaluationAdapter):
    """DeepEval-based implementation of EvaluationPort."""

    def __init__(
        self,
        model: str | None = None,
        param_resolver: FileParamResolver | None = None,
        metric_registry: DeepEvalMetricRegistry | None = None,
    ) -> None:
        self._model = model
        self._param_resolver = param_resolver or FileParamResolver(
            list_params=LLM_TEST_CASE_LIST_PARAMS
        )
        self._metric_registry = metric_registry or DeepEvalMetricRegistry()

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

        params = self._param_resolver.resolve(spec.params)

        # Build kwargs: required fields from tc + LLMTestCase params from YAML
        kwargs: dict[str, Any] = {
            "input": tc.input,
            "actual_output": tc.actual,
        }

        for key in LLM_TEST_CASE_PARAMS:
            if key in params:
                kwargs[key] = params[key]

        # Default completion_time from execution time if not specified
        if "completion_time" not in kwargs:
            kwargs["completion_time"] = tc.execution_time_ms / 1000.0

        return LLMTestCase(**kwargs)

    def _evaluate_group(
        self,
        metric_name: str,
        spec_params: dict[str, Any],
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

        metric = self._create_metric(config, metric_name, spec_params)
        results = deepeval_evaluate(test_cases=deepeval_tcs, metrics=[metric])

        self._collect_metric_results(tcs, results, metric_results_by_tc)

    def _create_metric(
        self,
        config: EvaluationConfig,
        metric_name: str,
        spec_params: dict[str, Any],
    ) -> BaseMetric:
        """Create a single deepeval metric."""
        if not self._metric_registry.supports_metric(metric_name):
            raise ValueError(f"Unsupported metric: {metric_name}")

        # Use params directly from spec
        params = dict(spec_params)

        # Add default model if not specified
        if "model" not in params and self._model is not None:
            params["model"] = self._model

        return self._metric_registry.create_metric(
            metric_name, params, config.default_threshold
        )

    def _collect_metric_results(
        self,
        test_cases: list[EvaluationTestCase],
        results: EvaluateResult,
        metric_results_by_tc: dict[str, list[PortMetricResult]],
    ) -> None:
        """Collect metric results from deepeval evaluation."""
        test_results = getattr(results, "test_results", [])

        for i, test_result in enumerate(test_results):
            if i >= len(test_cases):
                break

            tc = test_cases[i]
            metric_data_list = getattr(test_result, "metrics_data", [])

            for metric_data in metric_data_list:
                metric_results_by_tc[tc.id].append(
                    PortMetricResult(
                        sdk="deepeval",
                        metric=getattr(metric_data, "name", "unknown"),
                        score=getattr(metric_data, "score", 0.0),
                        passed=getattr(metric_data, "success", False),
                        reason=getattr(metric_data, "reason", None),
                        metadata=self._extract_metric_metadata(metric_data),
                    )
                )

    def _extract_metric_metadata(self, metric_data: MetricData) -> dict[str, object]:
        """Extract additional metadata from DeepEval metric data.

        Dynamically extracts all public attributes except core fields.
        """
        # Core fields already handled in MetricResult
        core_fields = {"name", "score", "reason", "success"}

        metadata: dict[str, object] = {}
        for attr in dir(metric_data):
            if attr.startswith("_") or attr in core_fields:
                continue
            value = getattr(metric_data, attr, None)
            if value is not None and not callable(value):
                metadata[attr] = value
        return metadata
